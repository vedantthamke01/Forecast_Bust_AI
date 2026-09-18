#!/usr/bin/env python3
"""
Server Configuration QR Generator
Generates connection payload and instructions for instant mobile app pairing.
Defaults to the production Render cloud backend (https://forecast-bust-api.onrender.com).
"""
import socket
import json
import sys
import argparse

RENDER_PRODUCTION_URL = "https://forecast-bust-api.onrender.com"

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Generate Server Configuration QR code for Forecast Bust AI Android App")
    parser.add_argument("--local", action="store_true", help="Use local machine LAN IP (port 8000) instead of production Render cloud")
    parser.add_argument("--url", type=str, default=None, help="Custom server base URL")
    args = parser.parse_args()

    if args.url:
        base_url = args.url.strip()
    elif args.local:
        lan_ip = get_lan_ip()
        base_url = f"http://{lan_ip}:8000"
    else:
        base_url = RENDER_PRODUCTION_URL

    is_production = (base_url == RENDER_PRODUCTION_URL)

    config = {
        "type": "forecast_bust_server",
        "baseUrl": base_url,
        "mode": "production_cloud" if is_production else "development_local",
        "organization": "NCMRWF / MoES",
        "service": "forecast-bust-detection"
    }

    payload = json.dumps(config)

    print("=" * 60)
    print(" FORECAST BUST AI — SERVER CONFIGURATION PAIRING")
    print("=" * 60)
    print(f"Target Environment: {'PRODUCTION CLOUD (Render)' if is_production else 'LOCAL DEVELOPMENT LAN'}")
    print(f"Backend Base URL:   {base_url}")
    print("\nJSON Configuration Payload:")
    print(json.dumps(config, indent=2))

    try:
        import qrcode
        qr = qrcode.QRCode(border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        print("\nScan this QR code in Forecast Bust AI (Advanced -> Server Connection):")
        qr.print_ascii(invert=True)
        
        # Also save PNG
        import os
        os.makedirs("dist", exist_ok=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save("dist/server_qr.png")
        print("\nSaved QR image to: dist/server_qr.png")
    except Exception as e:
        print(f"\nCould not generate terminal QR: {e}")

    print("\nMobile Pairing Instructions:")
    print("1. Open Forecast Bust AI on Android.")
    print("2. Navigate to: Advanced -> Server Connection.")
    print("3. Tap 'SCAN SERVER CONFIG QR' or enter:")
    print(f"   {base_url}")
    print("=" * 60)

if __name__ == '__main__':
    main()
