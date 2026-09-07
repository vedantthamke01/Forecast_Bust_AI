#!/usr/bin/env python3
"""
Forecast Bust AI - Local APK Distribution & QR Server
Serves the release APK on LAN (port 8080) with a browser landing page and QR code.
"""
import http.server
import socket
import socketserver
import os
import sys

PORT = 8080

def get_lan_ip():
    """Detect local LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually connect, but resolves route interface
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def find_apk_path():
    candidates = [
        os.path.abspath(os.path.join("dist", "forecast-bust-ai.apk")),
        os.path.abspath(os.path.join("apps", "flutter_app", "build", "app", "outputs", "flutter-apk", "app-release.apk")),
        os.path.abspath(os.path.join("..", "dist", "forecast-bust-ai.apk")),
        os.path.abspath(os.path.join("apps", "flutter_app", "build", "app", "outputs", "apk", "release", "app-release.apk")),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

class ApkDistributionHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        lan_ip = get_lan_ip()
        apk_path = find_apk_path()

        if self.path in ('/forecast-bust-ai.apk', '/app-release.apk'):
            if os.path.exists(apk_path):
                file_size = os.path.getsize(apk_path)
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.android.package-archive')
                self.send_header('Content-Disposition', 'attachment; filename="forecast-bust-ai.apk"')
                self.send_header('Content-Length', str(file_size))
                self.end_headers()
                with open(apk_path, 'rb') as f:
                    while chunk := f.read(65536):
                        self.wfile.write(chunk)
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"APK build not found. Please run 'flutter build apk --release' first.")
            return

        # Web landing page
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()

        apk_available = os.path.exists(apk_path)
        apk_size_mb = f"{os.path.getsize(apk_path) / (1024*1024):.1f} MB" if apk_available else "Not built yet"
        download_url = f"http://{lan_ip}:{PORT}/forecast-bust-ai.apk"
        backend_url = f"http://{lan_ip}:8000"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Install Forecast Bust AI</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"></script>
  <style>
    :root {{
      --bg: #06110C;
      --card: #0E1A14;
      --card2: #12211A;
      --green: #8CFF6E;
      --text: #EAF5EE;
      --dim: #8FA89B;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0; padding: 24px;
      display: flex; flex-direction: column; align-items: center;
    }}
    .box {{
      max-width: 440px; width: 100%;
      background: var(--card);
      border: 1px solid rgba(140,255,110,0.25);
      border-radius: 20px;
      padding: 24px; box-sizing: border-box;
      box-shadow: 0 10px 40px rgba(0,0,0,0.6);
      text-align: center;
    }}
    h1 {{ font-size: 20px; margin: 0 0 4px 0; color: var(--text); font-weight: 800; }}
    p.sub {{ font-size: 11px; color: var(--dim); margin: 0 0 20px 0; }}
    #qrcode {{
      background: #fff; padding: 12px; border-radius: 14px;
      display: inline-block; margin: 10px 0;
    }}
    .btn {{
      display: inline-block; width: 100%; box-sizing: border-box;
      background: var(--green); color: #040806;
      text-decoration: none; font-weight: 800; font-size: 13px;
      padding: 14px; border-radius: 12px; margin-top: 14px;
    }}
    .url {{
      font-family: monospace; font-size: 10px; color: var(--dim);
      word-break: break-all; margin: 8px 0;
    }}
    .meta {{
      background: var(--card2); border-radius: 10px; padding: 10px;
      margin: 16px 0; font-size: 11px; text-align: left;
    }}
    .meta div {{ margin: 4px 0; }}
    ol {{ text-align: left; font-size: 11px; color: var(--dim); line-height: 1.5; padding-left: 20px; }}
  </style>
</head>
<body>
  <div class="box">
    <h1>Forecast Bust AI</h1>
    <p class="sub">Reliability Intelligence · Days 3–10 · Android APK</p>

    <div id="qrcode"></div>
    <div class="url">{download_url}</div>

    <a href="/forecast-bust-ai.apk" class="btn">DOWNLOAD APK ({apk_size_mb})</a>

    <div class="meta">
      <div><strong>Status:</strong> {'Ready for Installation' if apk_available else '⚠️ Release APK building...'}</div>
      <div><strong>Backend API:</strong> {backend_url}</div>
      <div><strong>Target OS:</strong> Android 8.0+ (ARM64 / x86_64)</div>
    </div>

    <h3 style="font-size: 12px; text-align: left; margin-bottom: 4px;">INSTALLATION INSTRUCTIONS:</h3>
    <ol>
      <li>Scan the QR code with your Android camera or browser.</li>
      <li>Tap <strong>Download APK</strong> and save the file.</li>
      <li>Open the downloaded APK from notification or Files app.</li>
      <li>Allow "Install unknown apps" from browser if Android prompts.</li>
      <li>Launch <strong>Forecast Bust AI</strong>!</li>
    </ol>
  </div>

  <script>
    new QRCode(document.getElementById("qrcode"), {{
      text: "{download_url}",
      width: 180,
      height: 180,
      colorDark : "#000000",
      colorLight : "#ffffff",
      correctLevel : QRCode.CorrectLevel.M
    }});
  </script>
</body>
</html>"""
        self.wfile.write(html.encode('utf-8'))

def run_server():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    lan_ip = get_lan_ip()
    apk_path = find_apk_path()
    apk_found = os.path.exists(apk_path)

    print("=" * 60)
    print(" FORECAST BUST AI — LOCAL APK DISTRIBUTION SERVER")
    print("=" * 60)
    print(f"Local Host:    http://127.0.0.1:{PORT}/")
    print(f"LAN Portal:    http://{lan_ip}:{PORT}/")
    print(f"Direct APK:    http://{lan_ip}:{PORT}/forecast-bust-ai.apk")
    print(f"Backend Server:http://{lan_ip}:8000")
    print(f"APK Status:    {'FOUND (' + str(round(os.path.getsize(apk_path)/(1024*1024), 1)) + ' MB)' if apk_found else 'NOT FOUND'}")
    print("=" * 60)
    print(f"Open http://{lan_ip}:{PORT}/ in your phone browser to install.")

    try:
        import qrcode
        qr = qrcode.QRCode(border=2)
        download_url = f"http://{lan_ip}:{PORT}/forecast-bust-ai.apk"
        qr.add_data(download_url)
        qr.make(fit=True)
        print("\nScan this QR code with your phone camera to download APK directly:")
        qr.print_ascii(invert=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("dist/apk_download_qr.png")
        print("Saved APK QR to: dist/apk_download_qr.png\n")
    except Exception as e:
        pass

    print("Press Ctrl+C to stop server.\n")

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(('0.0.0.0', PORT), ApkDistributionHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nAPK server stopped.")

if __name__ == '__main__':
    run_server()
