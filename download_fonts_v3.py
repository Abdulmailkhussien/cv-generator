
import os
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def download_file(url, filename):
    try:
        print(f"Downloading {filename}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        print(f"Success: {filename}")
    except Exception as e:
        print(f"Failed {filename}: {e}")

if not os.path.exists('fonts'):
    os.makedirs('fonts')

# Tajawal for Arabic (Clean, modern, readable)
download_file("https://raw.githubusercontent.com/google/fonts/main/ofl/tajawal/Tajawal-Regular.ttf", "fonts/Tajawal-Regular.ttf")
download_file("https://raw.githubusercontent.com/google/fonts/main/ofl/tajawal/Tajawal-Bold.ttf", "fonts/Tajawal-Bold.ttf")

# Arimo for English (Arial Metric Compatible)
download_file("https://raw.githubusercontent.com/google/fonts/main/apache/arimo/Arimo-Regular.ttf", "fonts/Arimo-Regular.ttf")
download_file("https://raw.githubusercontent.com/google/fonts/main/apache/arimo/Arimo-Bold.ttf", "fonts/Arimo-Bold.ttf")
