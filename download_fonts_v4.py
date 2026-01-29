
import os
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download_file(urls, filename):
    for url in urls:
        try:
            print(f"Attempting {url}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                content = response.read()
                if len(content) > 1000:
                    with open(filename, 'wb') as f:
                        f.write(content)
                    print(f"Success: {filename}")
                    return
        except Exception as e:
            print(f"Failed {url}: {e}")
    print(f"ERROR: Could not be downloaded: {filename}")

if not os.path.exists('fonts'):
    os.makedirs('fonts')

# Use 'github.com/.../raw/main/...' format which worked for Amiri
# Arimo (English sans serif)
download_file([
    "https://github.com/google/fonts/raw/main/apache/arimo/Arimo-Regular.ttf",
    "https://github.com/google/fonts/raw/main/apache/arimo/static/Arimo-Regular.ttf"
], "fonts/Arimo-Regular.ttf")

download_file([
    "https://github.com/google/fonts/raw/main/apache/arimo/Arimo-Bold.ttf",
    "https://github.com/google/fonts/raw/main/apache/arimo/static/Arimo-Bold.ttf"
], "fonts/Arimo-Bold.ttf")

# Tajawal (Arabic sans serif)
download_file([
    "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Regular.ttf"
], "fonts/Tajawal-Regular.ttf")

download_file([
    "https://github.com/google/fonts/raw/main/ofl/tajawal/Tajawal-Bold.ttf"
], "fonts/Tajawal-Bold.ttf")
