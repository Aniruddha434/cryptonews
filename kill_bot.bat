@echo off
echo Killing all Python processes...
taskkill /F /IM python.exe /T 2>nul
if %errorlevel% equ 0 (
    echo All Python processes killed!
) else (
    echo No Python processes found running.
)
echo.
echo You can now run: python bot.py
pause

