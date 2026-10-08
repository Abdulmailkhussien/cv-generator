# CV Generator (Arabic & English)

A professional CV generator web application with full Arabic language support, multiple templates, and PDF export functionality.

## Features
- **Bilingual Support**: Full RTL support for Arabic and LTR for English.
- **Multiple Templates**: Classic, Modern, Minimal, Executive, Compact.
- **PDF Generation**: High-quality PDF output using ReportLab.
- **Security**: Rate limiting enabled to prevent abuse.
- **Portability**: Fonts are bundled, so it works on Linux/Docker/Windows.

## Environment Variables (Render -> Environment)

Set on the server only. Never commit a key: this repository is public, and a
value committed once stays in git history after it is deleted.

| Variable | Required | What it does |
|---|---|---|
| `GEMINI_API_KEY` | for AI features | Google **AI Studio** key. The consumer Gemini Pro subscription is a different product and does not work here. |
| `GEMINI_MODEL` | no | Defaults to `gemini-2.0-flash`. Override when a model is retired. |
| `ADMIN_TOKEN` | recommended | Guards `/admin/test`, reached at `/admin/test?t=<value>`. Unset means the route returns 404. |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | no | Existing monitoring. |

Without `GEMINI_API_KEY` the site still works: the three import doors report
that AI is unavailable and the manual form is unaffected.

To see which models a key can reach:

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"
```

## Installation

1. **Install Python**: Ensure Python 3.8+ is installed.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If the server does not auto-install libraries, you must run this manually.*

3. **Font Setup**:
   The project includes a `download_fonts.py` script. The application tries to use local fonts in `fonts/` folder first.
   ```bash
   python download_fonts.py
   ```


## Server Management Commands

### 🖥️ Windows (Local Testing)
**Start Server:**
```powershell
python app.py
```
**Stop Server:**
- Click inside the terminal and press `Ctrl + C`.

---

### 🐧 Linux (Production Server)

**Option 1: Simple Start (Foreground)**
Good for testing. The server stops if you close the terminal.
```bash
python3 app.py
```
**Stop:** `Ctrl + C`

**Option 2: Run in Background (Recommended)**
Keeps running even after you exit the terminal.

**Start:**
```bash
nohup python3 app.py > server.log 2>&1 &
echo "Server started in background."
```

**Stop:**
```bash
pkill -f "python3 app.py"
echo "Server stopped."
```

**Check Status:**
```bash
ps aux | grep "python3 app.py"
```

## Security Tests

To verify stability and security, run the stress test script:
```bash
python stress_test.py
```

## Deployment Notes

- **Linux/Ubuntu**: The application handles fonts locally using the `fonts/` directory, so you do NOT need to install system fonts.
- **Rate Limiting**: Configured to 200 requests per day per IP. To adjust, edit `app.py`.
