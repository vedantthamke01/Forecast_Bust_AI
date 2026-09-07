@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  FORECAST BUST AI — ANDROID RELEASE BUILD PIPELINE
echo ============================================================

set JAVA_HOME=C:\Users\tejas\jdk-17
set ANDROID_HOME=C:\Users\tejas\Android\Sdk
set PATH=C:\Users\tejas\flutter\bin;%JAVA_HOME%\bin;%PATH%

cd apps\flutter_app
echo [1/3] Running flutter pub get...
call flutter pub get
if %errorlevel% neq 0 (
    echo Error during flutter pub get.
    exit /b %errorlevel%
)

echo [2/3] Building release APK (flutter build apk --release)...
call flutter build apk --release
if %errorlevel% neq 0 (
    echo Error during flutter build apk.
    exit /b %errorlevel%
)

cd ..\..
if not exist dist mkdir dist
copy apps\flutter_app\build\app\outputs\flutter-apk\app-release.apk dist\forecast-bust-ai.apk /Y

echo [3/3] Release APK successfully built and copied:
echo Path: %CD%\dist\forecast-bust-ai.apk
echo.
echo To start the LAN APK download and QR server, run:
echo python tools\apk_server.py
echo ============================================================
