import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../../core/constants.dart';
import '../../providers/app_providers.dart';

class InstallGuideScreen extends ConsumerWidget {
  const InstallGuideScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final client = ref.watch(apiClientProvider);
    // Derive APK download URL from server URL or default to port 8080
    final uri = Uri.tryParse(client.baseUrl);
    final host = uri?.host ?? '192.168.1.100';
    final apkUrl = 'http://$host:8080/forecast-bust-ai.apk';
    final webUrl = 'http://$host:8080/';

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('Install Forecast Bust AI', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
        backgroundColor: AppColors.bgDark,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // METHOD 1: QR CODE
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.strokeStrong),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: const [
                      Text(
                        'METHOD 1: SCAN QR CODE',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: AppColors.green,
                          letterSpacing: 0.04,
                        ),
                      ),
                      Icon(Icons.qr_code_2, color: AppColors.green, size: 18),
                    ],
                  ),
                  const SizedBox(height: 14),

                  // QR Code
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: QrImageView(
                      data: apkUrl,
                      version: QrVersions.auto,
                      size: 180,
                    ),
                  ),
                  const SizedBox(height: 12),

                  Text(
                    apkUrl,
                    style: const TextStyle(
                      fontSize: 10,
                      color: AppColors.textDim,
                      fontFamily: 'monospace',
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),

                  ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.card2,
                      foregroundColor: AppColors.green,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: AppColors.stroke),
                      ),
                    ),
                    icon: const Icon(Icons.copy, size: 14),
                    label: const Text('COPY APK LINK', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800)),
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: apkUrl));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('APK download link copied to clipboard!')),
                      );
                    },
                  ),
                  const SizedBox(height: 10),

                  const Text(
                    'Steps:\n'
                    '1. Scan QR with Android camera or scanner.\n'
                    '2. Open browser and download APK.\n'
                    '3. Tap APK to install (enable "Install from unknown sources" if prompted).',
                    style: TextStyle(fontSize: 10, color: AppColors.textDim, height: 1.4),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // METHOD 2: SAME WI-FI BROWSER
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'METHOD 2: SAME WI-FI BROWSER',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: AppColors.text,
                      letterSpacing: 0.04,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Open Chrome or mobile browser on your Android phone and navigate to:\n$webUrl',
                    style: const TextStyle(fontSize: 11, color: AppColors.textDim, height: 1.35),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.green,
                      side: const BorderSide(color: AppColors.stroke),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                    icon: const Icon(Icons.copy, size: 14),
                    label: const Text('COPY PORTAL URL', style: TextStyle(fontSize: 10)),
                    onPressed: () {
                      Clipboard.setData(ClipboardData(text: webUrl));
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Portal URL copied!')),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // METHOD 3: DIRECT FILE TRANSFER
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    'METHOD 3: DIRECT FILE TRANSFER',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: AppColors.text,
                      letterSpacing: 0.04,
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    '1. Connect Android phone to PC via USB cable.\n'
                    '2. Transfer "dist/forecast-bust-ai.apk" to phone Downloads folder.\n'
                    '3. Alternatively, use Windows Nearby Share / Quick Share or Bluetooth.\n'
                    '4. Open the Files app on Android, tap the APK, and install.',
                    style: TextStyle(fontSize: 10.5, color: AppColors.textDim, height: 1.4),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
