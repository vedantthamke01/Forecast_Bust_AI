import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import '../../core/constants.dart';
import '../../providers/app_providers.dart';

class QrScannerScreen extends ConsumerStatefulWidget {
  const QrScannerScreen({super.key});

  @override
  ConsumerState<QrScannerScreen> createState() => _QrScannerScreenState();
}

class _QrScannerScreenState extends ConsumerState<QrScannerScreen> {
  final MobileScannerController _controller = MobileScannerController();
  bool _scanned = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _onDetect(BarcodeCapture capture) {
    if (_scanned) return;
    final barcode = capture.barcodes.firstOrNull;
    if (barcode == null || barcode.rawValue == null) return;

    final val = barcode.rawValue!.trim();
    String? targetUrl;

    if (val.startsWith('{') && val.endsWith('}')) {
      try {
        final json = jsonDecode(val) as Map<String, dynamic>;
        targetUrl = json['baseUrl'] as String?;
      } catch (_) {}
    } else if (val.startsWith('http://') || val.startsWith('https://')) {
      targetUrl = val;
    }

    if (targetUrl != null && targetUrl.isNotEmpty) {
      _scanned = true;
      ref.read(apiClientProvider).updateBaseUrl(targetUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Configured server: $targetUrl'),
          backgroundColor: AppColors.greenDeep,
        ),
      );
      Navigator.of(context).pop(true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('Scan Server QR', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
        backgroundColor: AppColors.bgDark,
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: _controller,
            onDetect: _onDetect,
          ),
          Center(
            child: Container(
              width: 240,
              height: 240,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.green, width: 2),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
          Positioned(
            bottom: 40,
            left: 20,
            right: 20,
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.7),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Text(
                'Point camera at the server configuration QR displayed in terminal or on the APK landing page.',
                style: TextStyle(color: Colors.white, fontSize: 11),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
