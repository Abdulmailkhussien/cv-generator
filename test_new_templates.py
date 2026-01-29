"""Test script for CV Generator - Testing new templates"""
import requests
import json

# Test Arabic data
data = {
    "language": "ar",
    "template": "executive",
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

# Test Executive template
print("Testing Executive template (Arabic)...")
try:
    data["template"] = "executive"
    response = requests.post("http://127.0.0.1:1000/generate", json=data, timeout=30)
    if response.status_code == 200:
        with open("test_executive.pdf", "wb") as f:
            f.write(response.content)
        print("SUCCESS! Executive PDF saved")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

# Test Compact template
print("Testing Compact template (Arabic)...")
try:
    data["template"] = "compact"
    response = requests.post("http://127.0.0.1:1000/generate", json=data, timeout=30)
    if response.status_code == 200:
        with open("test_compact.pdf", "wb") as f:
            f.write(response.content)
        print("SUCCESS! Compact PDF saved")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")

print("Done!")
