# Forecast Bust AI — Android Installation Guide

This document describes how to install the **Forecast Bust AI** (`com.forecastbustai.app`) native Android application on any standard Android phone (Android 8.0+ / API 26+) without requiring Android Studio.

---

## Prerequisites

1. **Android Phone**: Running Android 8.0 (Oreo) or later.
2. **Same Local Network (Wi-Fi)**: For live operational backend inference, the phone and the computer running the backend server should be connected to the same Wi-Fi network.

---

## METHOD 1 — QR Code Install (Recommended for Judges & Demos)

This method requires no typing on the mobile device.

### Step 1: Start the Local APK Distribution Server on PC
In your terminal on the PC, run:
```bash
python tools/apk_server.py
```
The server will output:
```text
============================================================
 FORECAST BUST AI — LOCAL APK DISTRIBUTION SERVER
============================================================
Local Host:    http://127.0.0.1:8080/
LAN Portal:    http://192.168.1.100:8080/
Direct APK:    http://192.168.1.100:8080/forecast-bust-ai.apk
Backend Server:http://192.168.1.100:8000
============================================================
```

### Step 2: Scan QR Code on Phone
1. Open the **Camera** or any **QR Code Scanner** on the Android device.
2. Point the camera at the QR code displayed on the PC screen (or in terminal).
3. Tap the link to open the web download portal.

### Step 3: Download and Install
1. Tap **DOWNLOAD APK**.
2. When the download finishes, tap the notification or open the downloaded file.
3. If Android displays: *"For your security, your phone is not allowed to install unknown apps from this source"*:
   - Tap **Settings**.
   - Toggle **Allow from this source** to **ON**.
   - Press **Back** and tap **Install**.
4. Tap **Open** to launch **Forecast Bust AI**!

---

## METHOD 2 — Same Wi-Fi Browser Download

If you prefer not to scan a QR code:

1. Connect the phone to the same Wi-Fi as the host PC.
2. Find the host PC's LAN IP (run `ipconfig` on Windows or `ip addr` on Linux, e.g. `192.168.1.100`).
3. Ensure the APK server is running:
   ```bash
   python tools/apk_server.py
   ```
4. On the Android phone, open Chrome or Samsung Internet and navigate to:
   ```text
   http://<PC_IP>:8080
   ```
   *(Example: `http://192.168.1.100:8080`)*
5. Tap **DOWNLOAD APK** and complete installation.

---

## METHOD 3 — Direct File Transfer (USB / Nearby Share / Bluetooth)

For completely offline installation without running an HTTP server:

1. Locate the built APK on the PC:
   ```text
   dist/forecast-bust-ai.apk
   ```
   *(Or `apps/flutter_app/build/app/outputs/flutter-apk/app-release.apk`)*
2. Transfer the APK to the phone using:
   - **USB Cable**: Copy to the phone's `Downloads` folder.
   - **Windows Nearby Share / Quick Share**: Right-click APK -> Share -> select Android phone.
   - **Bluetooth**: Send file via Bluetooth transfer.
3. On the phone, open the **Files** app -> **Downloads**.
4. Tap `forecast-bust-ai.apk` and select **Install**.

---

## Connecting the App to the Backend Server

Once installed, the app can perform live operational inference by connecting to your PC's backend:

1. **Start the Backend Server on PC**:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
2. **In the Android App**:
   - Open **Forecast Bust AI**.
   - Tap the **Advanced** tab in the bottom navigation.
   - Tap **Server Connection**.
   - Enter your PC's IP address: `http://<PC_IP>:8000` (e.g. `http://192.168.1.100:8000`).
   - Tap **TEST** -> status will display **CONNECTED ✓**.
   - Tap **APPLY** to save.
3. The app will now fetch live weather, NWP forecasts, and TreeSHAP-calibrated reliability predictions directly from the active backend!

---

## Firewall Troubleshooting

If the phone cannot connect to the PC:

### Windows Defender Firewall:
Allow Python and Port 8000 / 8080 through Windows Firewall:
```powershell
New-NetFirewallRule -DisplayName "Forecast Bust AI Backend (8000)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Forecast Bust AI APK Server (8080)" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

### Linux / Fedora:
```bash
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```
