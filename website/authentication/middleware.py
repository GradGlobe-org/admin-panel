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
