@echo off
cd /d %~dp0
title Logistradar Bot
echo === Logistradar Bot ishga tushmoqda ===

REM Eski proceslarni to'xtatish
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /nh 2^>nul') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr "main.py" >nul 2>&1
    if not errorlevel 1 taskkill /pid %%i /f >nul 2>&1
)
taskkill /f /im cloudflared.exe >nul 2>&1

REM Cloudflare tunnel ishga tushirish
echo Cloudflare tunnel ishga tushmoqda...
del cf.log >nul 2>&1
start /min "" "C:\Users\user\cloudflared.exe" tunnel --url http://localhost:8888 --logfile cf.log

REM URL chiqishini kutish (10 soniya)
echo URL kutilmoqda...
set WEBAPP_URL=
for /l %%i in (1,1,20) do (
    timeout /t 1 /nobreak >nul
    for /f "tokens=*" %%u in ('powershell -Command "if(Test-Path 'cf.log'){Get-Content 'cf.log' | Select-String 'trycloudflare.com|cloudflare.com/.*\|' | ForEach-Object{if($_ -match 'https://[a-z0-9\-]+\.trycloudflare\.com'){$Matches[0]}} | Select-Object -First 1 -ExpandProperty Line 2>$null}else{''}}" 2^>nul') do (
        if not "%%u"=="" set WEBAPP_URL=%%u
    )
    if not "%WEBAPP_URL%"=="" goto :got_url
)

:got_url
if "%WEBAPP_URL%"=="" (
    echo OGOHLANTIRISH: Tunnel URL topilmadi, polling mode da ishlaydi
) else (
    echo Tunnel URL: %WEBAPP_URL%
    REM .env ni yangilash
    powershell -Command "(Get-Content '.env') -replace 'WEBAPP_URL=.*', 'WEBAPP_URL=%WEBAPP_URL%' | Set-Content '.env'"
    echo .env yangilandi
)

REM Bot ishga tushirish
echo Bot ishga tushmoqda...
python main.py

pause
