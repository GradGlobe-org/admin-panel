from rake_nltk import Rake
import nltk
from nltk import word_tokenize, pos_tag
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from website.utils import api_key_required

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('averaged_perceptron_tagger_eng')


GOOD_POS = {"NN", "NNS", "NNP", "NNPS", "JJ"}

def is_meaningful(phrase):
    """
    Collects only the meaning full keywords good for seo
    """
    words = word_tokenize(phrase)
    tagged = pos_tag(words)
    return any(tag in GOOD_POS for word, tag in tagged)

def extract_keywords_rake(text, top_n=10):
    """
    Extracts Keywrods from the text
    """
    r = Rake()
    r.extract_keywords_from_text(text)
    ranked = r.get_ranked_phrases()

    filtered = [
        phrase for phrase in ranked[:top_n]
        if is_meaningful(phrase) and len(phrase.strip()) > 3
    ]
    return filtered




@api_key_required
@csrf_exempt
def meta_keywords(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON request"
        }, status=400)

    content = data.get("content")

    # try:
    keywords = extract_keywords_rake(content)
    # except:
        # return JsonResponse({
        #     "error": "Internal Server Error"
        # }, status=500)
    
    return JsonResponse({"keywords" : keywords})