from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import json
from decimal import Decimal, ROUND_DOWN


@csrf_exempt
def draft_university_name(request):
    if request.method == 'GET':
        try:
            # Get the first university with DRAFT status, ordered by highest review_rating
            draft_university = university.objects.filter(status='DRAFT').first()
            
            if not draft_university:
                return JsonResponse(
                    {"error": "No universities with DRAFT status found"},
                    status=404
                )
            
            # Return only the name
            return JsonResponse({"name": draft_university.name}, status=200)
        
        except Exception as e:
            return JsonResponse(
                {"error": f"An error occurred: {str(e)}"},
                status=500
            )
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def update_university(request):
    if request.method == 'PUT':
        try:
            # Parse JSON payload
            try:
                data = json.loads(request.body)
                # data = data.get('data')
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON payload"}, status=400)

            # Extract university name from payload
            university_name = data.get('name')
            if not university_name:
                return JsonResponse({"error": "University name is required"}, status=400)

            # Find the university
            try:
                uni = university.objects.get(name=university_name, status='DRAFT')
            except ObjectDoesNotExist:
                return JsonResponse({"error": f"No DRAFT university found with name '{university_name}'"}, status=404)

            # Update university fields
            uni_fields = ['cover_url', 'cover_origin', 'type', 'establish_year', 'about', 
                          'admission_requirements', 'location_map_link', 'review_rating', 
                          'avg_acceptance_rate', 'avg_tution_fee']
            for field in uni_fields:
                if field in data:
                    setattr(uni, field, data[field])

            # Update location (only if matching location exists)
            if 'location' in data:
                loc_data = data['location']
                if not all(key in loc_data for key in ['city', 'state', 'country']):
                    return JsonResponse({"error": "Location must include city, state, and country"}, status=400)
                try:
                    loc = location.objects.get(
                        city=loc_data['city'], state=loc_data['state'], country=loc_data['country']
                    )
                    uni.location = loc
                except location.DoesNotExist:
                    return JsonResponse({"error": f"Location '{loc_data['city']}, {loc_data['state']}, {loc_data['country']}' does not exist"}, status=400)

            # Delete existing related model entries
            AdmissionStats.objects.filter(university=uni).delete()
            Visa.objects.filter(university=uni).delete()
            WorkOpportunity.objects.filter(university=uni).delete()
            Uni_contact.objects.filter(university=uni).delete()
            stats.objects.filter(university=uni).delete()
            videos_links.objects.filter(university=uni).delete()
            university_ranking.objects.filter(university=uni).delete()
            faqs.objects.filter(university=uni).delete()

            # Create new related model entries
            # 1. AdmissionStats
            if 'admission_stats' in data:
                for stat_data in data['admission_stats']:
                    if 'admission_type' not in stat_data:
                        continue
                    stat = AdmissionStats(university=uni, admission_type=stat_data['admission_type'])
                    stat_fields = ['GPA_min', 'GPA_max', 'SAT_min', 'SAT_max', 
                                'ACT_min', 'ACT_max', 'IELTS_min', 'IELTS_max']
                    for field in stat_fields:
                        if field in stat_data:
                            # Convert the value to Decimal and enforce one decimal place
                            value = stat_data[field]
                            if isinstance(value, (int, float, str)):
                                try:
                                    decimal_value = Decimal(str(value)).quantize(Decimal('0.0'), rounding=ROUND_DOWN)
                                    setattr(stat, field, decimal_value)
                                except (ValueError, TypeError):
                                    return JsonResponse({"error": f"Invalid value for {field}: {value}"}, status=400)
                    stat.full_clean()
                    stat.save()

            # 2. Visa
            if 'visas' in data:
                for visa_data in data['visas']:
                    if 'name' not in visa_data or 'type_of_visa' not in visa_data:
                        continue
                    visa = Visa(
                        university=uni, 
                        name=visa_data['name'], 
                        type_of_visa=visa_data['type_of_visa']
                    )
                    if 'cost' in visa_data:
                        visa.cost = visa_data['cost']
                    if 'describe' in visa_data:
                        visa.describe = visa_data['describe']
                    visa.full_clean()
                    visa.save()

            # 3. WorkOpportunity
            if 'work_opportunities' in data:
                for wo_data in data['work_opportunities']:
                    if 'name' not in wo_data:
                        continue
                    wo = WorkOpportunity(university=uni, name=wo_data['name'])
                    wo.full_clean()
                    wo.save()

            # 4. Uni_contact
            if 'contacts' in data:
                for contact_data in data['contacts']:
                    if 'name' not in contact_data or 'email' not in contact_data:
                        continue
                    contact = Uni_contact(
                        university=uni, 
                        name=contact_data['name'], 
                        email=contact_data['email']
                    )
                    if 'designation' in contact_data:
                        contact.designation = contact_data['designation']
                    if 'phone' in contact_data:
                        contact.phone = contact_data['phone']
                    contact.full_clean()
                    contact.save()

            # 5. stats
            if 'statistics' in data:
                for stat_data in data['statistics']:
                    if 'name' not in stat_data or 'value' not in stat_data:
                        continue
                    stat = stats(university=uni, name=stat_data['name'], value=stat_data['value'])
                    stat.full_clean()
                    stat.save()

            # 6. videos_links
            if 'video_links' in data:
                for video_data in data['video_links']:
                    if 'url' not in video_data:
                        continue
                    video = videos_links(university=uni, url=video_data['url'])
                    video.full_clean()
                    video.save()

            # 7. university_ranking
            if 'rankings' in data:
                for rank_data in data['rankings']:
                    if 'rank' not in rank_data or 'ranking_agency' not in rank_data:
                        continue
                    try:
                        agency = ranking_agency.objects.get(name=rank_data['ranking_agency'])
                        rank = university_ranking(university=uni, ranking_agency=agency, rank=rank_data['rank'])
                        rank.full_clean()
                        rank.save()
                    except ranking_agency.DoesNotExist:
                        return JsonResponse({"error": f"Ranking agency '{rank_data['ranking_agency']}' not found"}, status=400)

            # 8. faqs
            if 'faqs' in data:
                for faq_data in data['faqs']:
                    if 'question' not in faq_data or 'answer' not in faq_data:
                        continue
                    faq = faqs(university=uni, question=faq_data['question'], answer=faq_data['answer'])
                    faq.full_clean()
                    faq.save()

            # Set university status to PUBLISH
            uni.status = 'PUBLISH'
            uni.full_clean()
            uni.save()

            return JsonResponse({"message": f"University '{uni.name}' updated and set to PUBLISH"}, status=200)

        except ValidationError as e:
            return JsonResponse({"error": f"Validation error: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def university_details(request):
    if request.method == 'GET':
        # Extract university name from query parameters
        university_name = request.GET.get('name')
        if not university_name:
            return JsonResponse({"error": "University name is required"}, status=400)

        try:
            # Find the university
            uni = university.objects.get(name=university_name)
        except ObjectDoesNotExist:
            return JsonResponse({"error": f"No university found with name '{university_name}'"}, status=404)

        try:
            # Prepare response data
            data = {
                'id': uni.id,
                'name': uni.name,
                'cover_url': uni.cover_url,
                'cover_origin': uni.cover_origin,
                'type': uni.type,
                'establish_year': uni.establish_year,
                'location': {
                    'city': uni.location.city,
                    'state': uni.location.state,
                    'country': uni.location.country
                },
                'about': uni.about,
                'admission_requirements': uni.admission_requirements,
                'location_map_link': uni.location_map_link,
                'review_rating': float(uni.review_rating),  # Convert Decimal to float for JSON
                'avg_acceptance_rate': uni.avg_acceptance_rate,
                'avg_tution_fee': uni.avg_tution_fee,
                'status': uni.status,
                'admission_stats': [
                    {
                        'admission_type': stat.admission_type,
                        'GPA_min': float(stat.GPA_min),
                        'GPA_max': float(stat.GPA_max),
                        'SAT_min': float(stat.SAT_min),
                        'SAT_max': float(stat.SAT_max),
                        'ACT_min': float(stat.ACT_min),
                        'ACT_max': float(stat.ACT_max),
                        'IELTS_min': float(stat.IELTS_min),
                        'IELTS_max': float(stat.IELTS_max)
                    } for stat in uni.admissionstats_set.all()
                ],
                'visas': [
                    {
                        'name': visa.name,
                        'type_of_visa': visa.type_of_visa,
                        'cost': visa.cost,
                        'describe': visa.describe
                    } for visa in uni.visa_set.all()
                ],
                'work_opportunities': [
                    {'name': wo.name} for wo in uni.workopportunity_set.all()
                ],
                'contacts': [
                    {
                        'name': contact.name,
                        'email': contact.email,
                        'designation': contact.designation,
                        'phone': contact.phone
                    } for contact in uni.contacts.all()
                ],
                'statistics': [
                    {
                        'name': stat.name,
                        'value': stat.value
                    } for stat in uni.statistics.all()
                ],
                'video_links': [
                    {'url': video.url} for video in uni.video_links.all()
                ],
                'rankings': [
                    {
                        'ranking_agency': rank.ranking_agency.name,
                        'rank': rank.rank
                    } for rank in uni.rankings.all()
                ],
                'faqs': [
                    {
                        'question': faq.question,
                        'answer': faq.answer
                    } for faq in uni.faqs.all()
                ]
            }

            return JsonResponse(data, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def location_search(request):
    if request.method == 'GET':
        # Extract query parameters
        city = request.GET.get('city')
        state = request.GET.get('state')
        country = request.GET.get('country')

        # Validate required parameters
        if not all([city, state, country]):
            return JsonResponse({"error": "City, state, and country are required"}, status=400)

        try:
            # Find the location
            loc = location.objects.get(city=city, state=state, country=country)
            return JsonResponse({"id": loc.id}, status=200)

        except ObjectDoesNotExist:
            return JsonResponse({"error": f"No location found for city='{city}', state='{state}', country='{country}'"}, status=404)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def ranking_agencies(request):
    if request.method == 'GET':
        try:
            # Fetch all ranking agencies
            agencies = ranking_agency.objects.all()
            data = [
                {
                    'name': agency.name,
                    'description': agency.description,
                    'logo': agency.logo
                } for agency in agencies
            ]
            return JsonResponse({"ranking_agencies": data}, status=200)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)