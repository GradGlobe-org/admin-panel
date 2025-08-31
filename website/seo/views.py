from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import yake
from website.utils import api_key_required, token_required

def get_yake_keywords(text, ratio=0.04, max_keywords=20):
    """
    Extract keywords using YAKE based on word count ratio.
    """
    word_count = len(text.split())
    top_keywords = max(1, min(max_keywords, int(word_count * ratio)))

    kw_extractor = yake.KeywordExtractor(
        lan="en",
        n=3,
        dedupLim=0.9,
        dedupFunc='seqm',
        windowsSize=1,
        top=top_keywords,
        features=None
    )

    keywords = kw_extractor.extract_keywords(text)
    keyword_list = [kw for kw, _ in keywords]
    keyword_string = ", ".join(keyword_list)
    return keyword_string

@token_required
@api_key_required
@csrf_exempt
def meta_keywords(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        content = data.get("content")

        if not content:
            return JsonResponse({"error": "No content provided."}, status=400)

        keywords = get_yake_keywords(content)
        return JsonResponse({"keywords": keywords})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@token_required
@api_key_required
@csrf_exempt
def extract_keywords(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        text = data.get('text')

        if not text:
            return JsonResponse({'error': 'No text provided.'}, status=400)

        keywords = get_yake_keywords(text)
        return JsonResponse({'keywords': keywords})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
