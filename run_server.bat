@echo off
echo Checking dependencies...
pip install -r requirements.txt

echo.
echo ====================================================
echo Starting CV Generator Server...
echo URL: http://localhost:1000
echo.
echo To STOP the server: Press Ctrl + C and then Y
echo or simply close this window.
echo ====================================================
echo.

python app.py
pause
