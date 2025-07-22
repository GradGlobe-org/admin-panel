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
        # Single query to fetch scholarships and all related data
        cursor.execute("""
            SELECT 
                s.id AS scholarship_id,
                s.name AS scholarship_name,
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
                c.id AS country_id,
                c.name AS country_name,
                -- Universities
                u.id AS university_id,
                u.name AS university_name,
                -- Eligible Nationalities
                en.id AS nationality_id,
                en.name AS nationality_name,
                -- Expense Coverages
                et.id AS expense_type_id,
                et.name AS expense_type_name,
                sec.is_covered,
                -- FAQs
                faq.id AS faq_id,
                faq.question,
                faq.answer
            FROM scholarship_scholarship s
            LEFT JOIN university_country c ON s.country_id = c.id
            LEFT JOIN scholarship_scholarship_university su ON s.id = su.scholarship_id
            LEFT JOIN university_university u ON su.university_id = u.id
            LEFT JOIN scholarship_scholarship_eligible_nationalities sen ON s.id = sen.scholarship_id
            LEFT JOIN university_country en ON sen.country_id = en.id
            LEFT JOIN scholarship_scholarshipexpensecoverage sec ON s.id = sec.scholarship_id
            LEFT JOIN scholarship_expensetype et ON sec.expense_type_id = et.id
            LEFT JOIN scholarship_faq faq ON s.id = faq.scholarship_id
            ORDER BY s.name, u.name, en.name, et.name, faq.id
        """)
        
        rows = cursor.fetchall()
        scholarships = {}
        
        for row in rows:
            scholarship_id = row[0]
            
            # Initialize scholarship if not already in dict
            if scholarship_id not in scholarships:
                scholarships[scholarship_id] = {
                    'id': scholarship_id,
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
                        'id': row[13],
                        'name': row[14]
                    } if row[13] else None,
                    'universities': [],
                    'eligible_nationalities': [],
                    'expense_coverages': [],
                    'faqs': []
                }
            
            scholarship = scholarships[scholarship_id]
            
            # Add university if exists and not already added
            if row[15] and {'id': row[15], 'name': row[16]} not in scholarship['universities']:
                scholarship['universities'].append({
                    'id': row[15],
                    'name': row[16]
                })
            
            # Add eligible nationality if exists and not already added
            if row[17] and {'id': row[17], 'name': row[18]} not in scholarship['eligible_nationalities']:
                scholarship['eligible_nationalities'].append({
                    'id': row[17],
                    'name': row[18]
                })
            
            # Add expense coverage if exists and not already added
            if row[19] and {'expense_type': row[20], 'is_covered': row[21]} not in scholarship['expense_coverages']:
                scholarship['expense_coverages'].append({
                    'expense_type': row[20],
                    'is_covered': row[21]
                })
            
            # Add FAQ if exists and not already added
            if row[22] and {'question': row[23], 'answer': row[24]} not in scholarship['faqs']:
                scholarship['faqs'].append({
                    'question': row[23],
                    'answer': row[24]
                })
        
        # Convert scholarships dict to list
        scholarships_list = list(scholarships.values())
    
    return JsonResponse({
        'status': 'success',
        'count': len(scholarships_list),
        'data': scholarships_list
    }, safe=False)