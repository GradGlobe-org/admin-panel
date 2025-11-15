from django.core.cache import cache
from django.http import JsonResponse

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_limit = 300  # 300 requests
        self.request_window = 5 * 60  # 5 minutes in seconds
        self.block_duration = 10 * 60  # 10 minutes in seconds

    def __call__(self, request):
        # Skip rate limiting for certain paths if needed
        if request.path.startswith('/admin/'):
            return self.get_response(request)
            
        ip = self.get_ip(request)
        request_key = f"rl:requests:{ip}"
        block_key = f"rl:blocked:{ip}"

        # Check if IP is blocked
        if cache.get(block_key):
            return JsonResponse(
                {'error': 'Too many requests. Please try again later.'},
                status=429
            )

        # Get current request count
        current_requests = cache.get(request_key, 0)

        if current_requests >= self.request_limit:
            # Set block and clear request counter
            cache.set(block_key, True, timeout=self.block_duration)
            cache.delete(request_key)
            return JsonResponse(
                {'error': 'Too many requests. Please try again in 10 minutes.'},
                status=429
            )

        # Increment request count (or initialize if doesn't exist)
        if current_requests:
            cache.incr(request_key)
        else:
            cache.set(request_key, 1, timeout=self.request_window)

        response = self.get_response(request)
        return response

    def get_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

import requests
import traceback
import json
from django.http import JsonResponse
from django.urls import resolve
from django.utils.deprecation import MiddlewareMixin

TELEGRAM_BOT_TOKEN = "8543435604:AAE2uDmfT8KvF3geL9MHErS4Ew26ofX1mKg"
TELEGRAM_CHAT_ID = "-1003457718565"

MAX_TELEGRAM_LENGTH = 3900  # Telegram max 4096 chars


def safe_json(value):
    """Safely convert any Python value to JSON."""
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except Exception:
        return str(value)


def escape_md(text: str) -> str:
    """Escape Markdown characters that might break Telegram formatting."""
    if not isinstance(text, str):
        return str(text)
    return text.replace("`", "'").replace("*", "×")


def send_telegram_message(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        requests.post(url, data=payload, timeout=3)
    except Exception:
        # NEVER raise inside error logger
        pass


class TelegramErrorLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """
        Safely catch all Django exceptions and log them to Telegram
        without breaking other middleware or Django internals.
        """

        # -------- 1. URL + method --------
        try:
            url = request.build_absolute_uri()
        except Exception:
            url = "Unknown"

        method = getattr(request, "method", "Unknown")

        # -------- 2. User --------
        try:
            if hasattr(request, "user") and request.user.is_authenticated:
                user = f"{request.user} (ID: {request.user.id})"
            else:
                user = "Anonymous"
        except Exception:
            user = "Unknown"

        # -------- 3. Headers (safe) --------
        try:
            headers = {
                k: v for k, v in request.headers.items()
                if k.lower() not in ["authorization", "cookie"]
            }
        except Exception:
            headers = "Could not read headers"

        # -------- 4. GET params --------
        try:
            get_params = dict(request.GET)
        except Exception:
            get_params = "Invalid GET"

        # -------- 5. POST body --------
        body_preview = None
        try:
            raw = request.body
            if raw:
                try:
                    body_preview = raw.decode("utf-8")
                except UnicodeDecodeError:
                    body_preview = "<Binary data>"
            else:
                body_preview = None
        except Exception:
            body_preview = "Could not read body"

        # Try JSON parsing
        try:
            parsed_body = json.loads(body_preview) if body_preview else None
        except Exception:
            parsed_body = body_preview  # fallback

        # -------- 6. View name --------
        try:
            resolved = resolve(request.path)
            view_name = f"{resolved.func.__module__}.{resolved.func.__name__}"
        except Exception:
            view_name = "Unknown"

        # -------- 7. Traceback --------
        try:
            tb = traceback.format_exc()
        except Exception:
            tb = "Traceback unavailable"

        # -------- 8. Build Telegram message --------
        message = (
            "*🚨 Django Server Error Detected!*\n\n"
            f"*View:* `{escape_md(view_name)}`\n"
            f"*User:* `{escape_md(str(user))}`\n"
            f"*Method:* `{method}`\n"
            f"*URL:* `{escape_md(url)}`\n\n"
            "*Headers:*\n"
            f"```{escape_md(safe_json(headers))}```\n"
            "*GET Params:*\n"
            f"```{escape_md(safe_json(get_params))}```\n"
            "*Body:*\n"
            f"```{escape_md(str(parsed_body))}```\n\n"
            "*Traceback:*\n"
            f"```{escape_md(tb)}```"
        )

        # -------- 9. Enforce Telegram limit --------
        message = message[:MAX_TELEGRAM_LENGTH] + (
            "...\n`[TRUNCATED]`" if len(message) > MAX_TELEGRAM_LENGTH else ""
        )

        # -------- 10. Send to Telegram safely --------
        send_telegram_message(message)

        # -------- 11. Standard error response --------
        return JsonResponse({"error": "Internal server error occurred."}, status=500)

