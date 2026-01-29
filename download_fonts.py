
import os
import urllib.request
import ssl

# Bypass SSL errors if any (unverified context)
ssl._create_default_https_context = ssl._create_unverified_context

def download_file(urls, filename):
    for url in urls:
        try:
            print(f"Attempting to download {filename} from {url}...")
            # Fake user agent to avoid 403
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                with open(filename, 'wb') as f:
                    f.write(response.read())
            
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                print(f"Successfully downloaded {filename}")
                return
        except Exception as e:
            print(f"Failed from {url}: {e}")
    print(f"ERROR: Could not download {filename} from any source.")

if not os.path.exists('fonts'):
    os.makedirs('fonts')

# Arimo (Arial compatible)
urls_arimo_reg = [
    'https://github.com/google/fonts/raw/main/apache/arimo/Arimo-Regular.ttf',
    'https://raw.githubusercontent.com/google/fonts/main/apache/arimo/Arimo-Regular.ttf'
]
urls_arimo_bold = [
    'https://github.com/google/fonts/raw/main/apache/arimo/Arimo-Bold.ttf',
    'https://raw.githubusercontent.com/google/fonts/main/apache/arimo/Arimo-Bold.ttf'
]

# Noto Sans Arabic (Clean Arabic font, closer to Arial's look than Cairo/Amiri)
urls_noto_reg = [
    'https://github.com/google/fonts/raw/main/ofl/notosansarabic/NotoSansArabic-Regular.ttf',
    'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansarabic/NotoSansArabic-Regular.ttf'
]
urls_noto_bold = [
    'https://github.com/google/fonts/raw/main/ofl/notosansarabic/NotoSansArabic-Bold.ttf',
    'https://raw.githubusercontent.com/google/fonts/main/ofl/notosansarabic/NotoSansArabic-Bold.ttf'
]

download_file(urls_arimo_reg, 'fonts/Arimo-Regular.ttf')
download_file(urls_arimo_bold, 'fonts/Arimo-Bold.ttf')
download_file(urls_noto_reg, 'fonts/NotoSansArabic-Regular.ttf')
download_file(urls_noto_bold, 'fonts/NotoSansArabic-Bold.ttf')
