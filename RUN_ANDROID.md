# Forecast Bust AI — Developer & Execution Guide

This document contains exact commands to test, build, and run the **Forecast Bust AI** Android application and distribution services.

---

## 1. Prerequisites & Environment Setup

Ensure `JAVA_HOME` and `ANDROID_HOME` are set in your environment:

### Windows (PowerShell):
```powershell
$env:JAVA_HOME = "C:\Users\tejas\jdk-17"
$env:ANDROID_HOME = "C:\Users\tejas\Android\Sdk"
$env:PATH = "C:\Users\tejas\flutter\bin;$env:JAVA_HOME\bin;$env:PATH"
```

---

## 2. Running Automated Tests & Static Analysis

From the repository root:

### Run Static Analysis:
```powershell
cd apps\flutter_app
flutter analyze
```
*Expected: `No issues found!`*

### Run Test Suite:
```powershell
flutter test
```
*Expected: `All tests passed!` (6 passed, 0 failed)*

---

## 3. Building the Release Android APK

### Option A: Using the Automated Build Script
From the repository root:
```cmd
tools\build_android.bat
```

### Option B: Using Flutter CLI Directly
```powershell
cd apps\flutter_app
flutter build apk --release
```
The output APK is generated at:
```text
apps/flutter_app/build/app/outputs/flutter-apk/app-release.apk
```
And copied to:
```text
dist/forecast-bust-ai.apk
```

---

## 4. Starting the Local APK Distribution & QR Server

To serve the built APK to Android phones on the local network:
```powershell
python tools/apk_server.py
```
This runs a lightweight local HTTP server on port 8080.
- Scan the displayed QR code or open `http://<PC_IP>:8080` in your phone browser.

---

## 5. Running the Backend Server

Start the operational FastAPI backend:
```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```
- Web Dashboard: `http://localhost:8000/dashboard/`
- API Health: `http://localhost:8000/health`
- Mobile Client connection: `http://<PC_IP>:8000`

---

## 6. Running the App in Development Mode

To run on a connected Android phone or emulator:
```powershell
cd apps\flutter_app
flutter run
```
