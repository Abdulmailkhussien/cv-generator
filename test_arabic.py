"""Test script for CV Generator"""
import requests
import json

# Test Arabic data
data = {
    "language": "ar",
    "full_name": "محمد أحمد",
    "job_title": "مهندس برمجيات",
    "email": "test@example.com",
    "phone": "+966 50 123 4567",
    "location": "الرياض، السعودية",
    "linkedin": "linkedin.com/in/test",
    "summary": "مهندس برمجيات خبير مع أكثر من 5 سنوات في تطوير البرمجيات",
    "skills": "Python, JavaScript, React, Node.js",
    "experiences": [
        {
            "title": "مطور أول",
            "company": "شركة التقنية",
            "start_date": "2020",
            "end_date": "الآن",
            "description": "تطوير تطبيقات الويب"
        }
    ],
    "education": [
        {
            "degree": "بكالوريوس علوم حاسب",
            "school": "جامعة الملك سعود",
            "field": "علوم الحاسب",
            "year": "2019"
        }
    ]
}

print("Testing Arabic CV generation...")
try:
    response = requests.post(
        "http://127.0.0.1:1000/generate",
        json=data,
        timeout=30
    )
    
    if response.status_code == 200:
        with open("test_arabic.pdf", "wb") as f:
            f.write(response.content)
        print("SUCCESS! Arabic PDF saved as test_arabic.pdf")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
