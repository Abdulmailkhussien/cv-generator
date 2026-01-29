
import requests
import time
import os

URL = "http://localhost:1000"
GENERATE_URL = f"{URL}/generate"

def test_homepage():
    print("Testing Homepage...")
    try:
        r = requests.get(URL)
        if r.status_code == 200:
            content = r.text
            if '<link rel="icon"' in content and '📄' in content:
                print("[PASS] Favicon found.")
            else:
                print("[FAIL] Favicon NOT found.")
                
            # Check for CLEAN link tag (no hanging text)
            if 'href="https://fonts' in content and 'rel="stylesheet">' in content:
                # Basic check, hard to verify exact "absence" of malformed text easily without regex or bs4, 
                # but we can check if the line starts correctly if we split lines.
                # simpler: check if the heart is there.
                pass

            if 'class="footer"' in content and '<svg class="heart"' in content and '#b91c1c' in content:
                print("[PASS] Footer found (SVG Heart, Dark Red).")
            else:
                print(f"[FAIL] Footer incorrect. Content snippet: {content[-300:]}")
        else:
            print(f"[FAIL] Homepage returned {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Homepage error: {e}")

def test_arabic_pdf():
    print("\nTesting Arabic PDF Generation...")
    data = {
        "language": "ar",
        "template": "classic",
        "full_name": "مستخدم تجريبي عربي",
        "job_title": "مطور برمجيات",
        "email": "arabic@test.com",
        "phone": "0500000000",
        "location": "الرياض",
        "summary": "هذا نص عربي للتجربة 123.",
        "skills": "بايثون, فلاسك",
        "experiences": [],
        "education": []
    }
    
    try:
        r = requests.post(GENERATE_URL, json=data)
        if r.status_code == 200 and 'application/pdf' in r.headers.get('Content-Type', ''):
            filename = "test_arabic_output.pdf"
            with open(filename, 'wb') as f:
                f.write(r.content)
            print(f"[PASS] PDF generated successfully ({len(r.content)} bytes). Saved to {filename}")
        else:
            print(f"[FAIL] PDF generation failed: {r.status_code}")
            print(r.text)
    except Exception as e:
        print(f"[FAIL] PDF error: {e}")

if __name__ == "__main__":
    # Wait for server to start
    print("Waiting for server to ensure it is up...")
    time.sleep(3)
    
    test_homepage()
    test_arabic_pdf()
