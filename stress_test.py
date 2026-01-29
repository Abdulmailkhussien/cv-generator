
import os
import requests
import threading
import time

URL = "http://localhost:1000"
GENERATE_URL = f"{URL}/generate"
NUM_THREADS = 10
REQUESTS_PER_THREAD = 5

test_data = {
    "language": "en",
    "template": "classic",
    "full_name": "Performance Test",
    "job_title": "Load Tester",
    "email": "test@example.com",
    "phone": "+1234567890",
    "location": "Server Room",
    "summary": "Testing server stability...",
    "skills": "Load Testing, Stress Testing, Python",
    "experiences": [],
    "education": []
}

def send_requests(thread_id):
    success_count = 0
    error_count = 0
    
    print(f"Thread {thread_id} starting...")
    for i in range(REQUESTS_PER_THREAD):
        try:
            # Test simple load
            r = requests.get(URL)
            if r.status_code == 200:
                pass
            else:
                print(f"Thread {thread_id}: Main page failed with {r.status_code}")
                error_count += 1
                
            # Test PDF generation (heavier)
            r = requests.post(GENERATE_URL, json=test_data)
            if r.status_code == 200:
                success_count += 1
            elif r.status_code == 429:
                print(f"Thread {thread_id}: Rate limit hit (Expected)")
                # Rate limit is expected, sort of a success for security test
                success_count += 1
            else:
                print(f"Thread {thread_id}: Generation failed with {r.status_code}")
                error_count += 1
                
        except Exception as e:
            print(f"Thread {thread_id}: Error: {e}")
            error_count += 1
            
    print(f"Thread {thread_id} finished. Success: {success_count}, Errors: {error_count}")

def run_stress_test():
    print(f"Starting stress test with {NUM_THREADS} threads...")
    threads = []
    start_time = time.time()
    
    for i in range(NUM_THREADS):
        t = threading.Thread(target=send_requests, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    duration = time.time() - start_time
    print(f"\nStress test completed in {duration:.2f} seconds.")
    print("If no critical errors occurred, the server is stable.")

if __name__ == "__main__":
    if requests.get(URL).status_code != 200:
        print("ERROR: Server does not appear to be running on localhost:1000")
        exit(1)
        
    run_stress_test()
