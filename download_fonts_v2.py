
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

# Try specific static paths for Noto Sans Arabic
# Note: Google Fonts structure changes. If 'static' doesn't exist, we might have to use the variable one.
# But ReportLab needs TTF.
base = "https://github.com/google/fonts/raw/main/ofl/notosansarabic/static"
download_file(f"{base}/NotoSansArabic-Regular.ttf", "fonts/NotoSansArabic-Regular.ttf")
download_file(f"{base}/NotoSansArabic-Bold.ttf", "fonts/NotoSansArabic-Bold.ttf")

# Arimo for English (already downloaded successfully? checking...)
arimo_base = "https://github.com/google/fonts/raw/main/apache/arimo"
download_file(f"{arimo_base}/Arimo-Regular.ttf", "fonts/Arimo-Regular.ttf")
download_file(f"{arimo_base}/Arimo-Bold.ttf", "fonts/Arimo-Bold.ttf")
