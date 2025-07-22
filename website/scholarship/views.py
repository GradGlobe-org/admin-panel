from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from .models import Scholarship
from website.utils import api_key_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def scholarship_details(request):
    with connection.cursor() as cursor:
        # Main scholarship query with related data
        cursor.execute("""
            SELECT 
                s.id,
                s.name,
                s.awarded_by,
                s.overview,
                s.details,
                s.amount_details,
                s.course,
                s.deadline,
                s.intake_year,
                s.amount,
                s.no_of_students,
                s.type_of_scholarship,
                s.brochure,
                c.name as country_name,
                c.id as country_id
            FROM scholarship_scholarship s
            LEFT JOIN university_country c ON s.country_id = c.id
            ORDER BY s.name
        """)
        
        scholarships_data = cursor.fetchall()
        scholarships = []
        
        for row in scholarships_data:
            scholarship_id = row[0]
            
            # Get associated universities (only ID and name)
            cursor.execute("""
                SELECT u.id, u.name
                FROM scholarship_scholarship_university su
                JOIN university_university u ON su.university_id = u.id
                WHERE su.scholarship_id = %s
                ORDER BY u.name
            """, [scholarship_id])
            
            universities = [
                {
                    'id': uni[0],
                    'name': uni[1]
                }
                for uni in cursor.fetchall()
            ]
            
            # Get eligible nationalities
            cursor.execute("""
                SELECT c.id, c.name
                FROM scholarship_scholarship_eligible_nationalities sen
                JOIN university_country c ON sen.country_id = c.id
                WHERE sen.scholarship_id = %s
                ORDER BY c.name
            """, [scholarship_id])
            
            eligible_nationalities = [
                {
                    'id': nat[0],
                    'name': nat[1]
                }
                for nat in cursor.fetchall()
            ]
            
            # Get expense coverages
            cursor.execute("""
                SELECT et.name, sec.is_covered
                FROM scholarship_scholarshipexpensecoverage sec
                JOIN scholarship_expensetype et ON sec.expense_type_id = et.id
                WHERE sec.scholarship_id = %s
                ORDER BY et.name
            """, [scholarship_id])
            
            expense_coverages = [
                {
                    'expense_type': exp[0],
                    'is_covered': exp[1]
                }
                for exp in cursor.fetchall()
            ]
            
            # Get FAQs
            cursor.execute("""
                SELECT question, answer
                FROM scholarship_faq
                WHERE scholarship_id = %s
                ORDER BY id
            """, [scholarship_id])
            
            faqs = [
                {
                    'question': faq[0],
                    'answer': faq[1]
                }
                for faq in cursor.fetchall()
            ]
            
            # Build scholarship object
            scholarship = {
                'id': row[0],
                'name': row[1],
                'awarded_by': row[2],
                'overview': row[3],
                'details': row[4],
                'amount_details': row[5],
                'course': row[6],
                'deadline': row[7].strftime('%Y-%m-%d') if row[7] else None,
                'intake_year': row[8].strftime('%Y-%m-%d') if row[8] else None,
                'amount': row[9],
                'no_of_students': row[10],
                'type_of_scholarship': row[11],
                'brochure': row[12],
                'country': {
                    'id': row[14],
                    'name': row[13]
                } if row[13] else None,
                'universities': universities,  # Only id and name
                'eligible_nationalities': eligible_nationalities,
                'expense_coverages': expense_coverages,
                'faqs': faqs
            }
            
            scholarships.append(scholarship)
    
    return JsonResponse({
        'status': 'success',
        'count': len(scholarships),
        'data': scholarships
    }, safe=False)
