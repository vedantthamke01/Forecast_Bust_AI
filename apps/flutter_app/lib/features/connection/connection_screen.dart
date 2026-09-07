import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/app_providers.dart';
import 'qr_scanner_screen.dart';

class ConnectionScreen extends ConsumerStatefulWidget {
  const ConnectionScreen({super.key});

  @override
  ConsumerState<ConnectionScreen> createState() => _ConnectionScreenState();
}

class _ConnectionScreenState extends ConsumerState<ConnectionScreen> {
  late TextEditingController _urlController;
  int? _latencyMs;
  bool _isTesting = false;
  String? _statusMessage;
  bool _isConnected = false;

  @override
  void initState() {
    super.initState();
    final client = ref.read(apiClientProvider);
    _urlController = TextEditingController(text: client.baseUrl);
    _runTest();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _runTest([String? targetUrl]) async {
    final candidateUrl = (targetUrl ?? _urlController.text).trim();
    setState(() {
      _isTesting = true;
      _statusMessage = null;
    });

    final client = ref.read(apiClientProvider);
    final latency = await client.testConnection(candidateUrl);

    if (mounted) {
      setState(() {
        _isTesting = false;
        _latencyMs = latency;
        _isConnected = latency != null;
        _statusMessage = _isConnected
            ? 'Connected successfully ($latency ms)'
            : 'Server unreachable at $candidateUrl. Verify host IP, port 8000, and same Wi-Fi.';
      });
    }
  }

  void _saveUrl() {
    final newUrl = _urlController.text.trim();
    if (newUrl.isNotEmpty) {
      ref.read(apiClientProvider).updateBaseUrl(newUrl);
      _invalidateAllProviders();
      _runTest(newUrl);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Server connected & active: $newUrl'),
          backgroundColor: AppColors.green,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  void _invalidateAllProviders() {
    ref.invalidate(currentWeatherProvider);
    ref.invalidate(forecastTimelineProvider);
    ref.invalidate(riskPredictionProvider);
    ref.invalidate(spatialRiskMapProvider);
    ref.invalidate(historicalVerificationProvider);
    ref.invalidate(modelEvaluationProvider);
    ref.invalidate(datasetStatusProvider);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        title: const Text('Backend Connection', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
        backgroundColor: AppColors.bgDark,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.card,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _isConnected ? AppColors.green.withOpacity(0.4) : AppColors.red.withOpacity(0.4),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'SERVER STATUS',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textDim,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: (_isConnected ? AppColors.green : AppColors.red).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          _isConnected ? 'CONNECTED ✓' : 'OFFLINE ✕',
                          style: TextStyle(
                            fontSize: 9.5,
                            fontWeight: FontWeight.w800,
                            color: _isConnected ? AppColors.green : AppColors.red,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _urlController.text,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.text,
                      fontFamily: 'monospace',
                    ),
                  ),
                  if (_latencyMs != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      'Latency: $_latencyMs ms',
                      style: const TextStyle(fontSize: 11, color: AppColors.green),
                    ),
                  ],
                  if (_statusMessage != null) ...[
                    const SizedBox(height: 6),
                    Text(
                      _statusMessage!,
                      style: TextStyle(
                        fontSize: 11,
                        color: _isConnected ? AppColors.textDim : AppColors.red,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Server Input & QR
            const Text(
              'CONFIGURE SERVER URL',
              style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.textDim),
            ),
            const SizedBox(height: 8),

            TextField(
              controller: _urlController,
              style: const TextStyle(color: AppColors.text, fontSize: 13, fontFamily: 'monospace'),
              decoration: InputDecoration(
                hintText: 'e.g. http://192.168.1.100:8000',
                hintStyle: const TextStyle(color: AppColors.textFaint),
                filled: true,
                fillColor: AppColors.card2,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.stroke),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.green),
                ),
              ),
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.card2,
                      foregroundColor: AppColors.green,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                        side: const BorderSide(color: AppColors.stroke),
                      ),
                    ),
                    icon: _isTesting
                        ? const SizedBox(
                            width: 14,
                            height: 14,
                            child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.green),
                          )
                        : const Icon(Icons.network_check, size: 16),
                    label: const Text('TEST', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
                    onPressed: _isTesting ? null : _runTest,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.green,
                      foregroundColor: AppColors.bgDark,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    icon: const Icon(Icons.save, size: 16),
                    label: const Text('APPLY', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800)),
                    onPressed: _saveUrl,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Scan QR Button
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppColors.text,
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  side: const BorderSide(color: AppColors.strokeStrong),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                icon: const Icon(Icons.qr_code_scanner, color: AppColors.green, size: 18),
                label: const Text(
                  'SCAN SERVER CONFIG QR',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800),
                ),
                onPressed: () async {
                  final res = await Navigator.of(context).push<bool>(
                    MaterialPageRoute(builder: (_) => const QrScannerScreen()),
                  );
                  if (res == true && mounted) {
                    _urlController.text = ref.read(apiClientProvider).baseUrl;
                    _invalidateAllProviders();
                    _runTest();
                  }
                },
              ),
            ),
            const SizedBox(height: 20),

            // LAN Troubleshooting Guide
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.card2,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    '💡 LAN SETUP INSTRUCTIONS',
                    style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: AppColors.green),
                  ),
                  SizedBox(height: 6),
                  Text(
                    '1. Ensure phone and developer PC are connected to the same Wi-Fi network.\n'
                    '2. Find your PC IPv4 address (Windows: run "ipconfig", look for Wireless LAN IPv4).\n'
                    '3. Start FastAPI backend with: "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000".\n'
                    '4. Enter "http://<PC_IP>:8000" above or scan the server QR code.',
                    style: TextStyle(fontSize: 10, color: AppColors.textDim, height: 1.4),
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
