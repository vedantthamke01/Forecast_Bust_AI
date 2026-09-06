import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/providers/weather_provider.dart';

class RiskMapScreen extends ConsumerWidget {
  const RiskMapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final gridAsync = ref.watch(riskMapGridProvider);
    final leadHours = ref.watch(selectedLeadHoursProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Spatial Risk Map (Day ${(leadHours / 24).floor()})'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(riskMapGridProvider),
          ),
        ],
      ),
      body: gridAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Map data error: $err')),
        data: (grid) {
          final markers = grid.map((pt) {
            final lat = (pt['latitude'] as num).toDouble();
            final lon = (pt['longitude'] as num).toDouble();
            final riskLevel = pt['risk_level'] as String? ?? 'LOW';

            Color color = AppConstants.riskLow;
            if (riskLevel == 'MODERATE') color = AppConstants.riskModerate;
            if (riskLevel == 'HIGH') color = AppConstants.riskHigh;
            if (riskLevel == 'VERY HIGH') color = AppConstants.riskVeryHigh;

            return Marker(
              point: LatLng(lat, lon),
              width: 32,
              height: 32,
              child: GestureDetector(
                onTap: () {
                  _showStationDetails(context, pt);
                },
                child: Container(
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                    boxShadow: [
                      BoxShadow(color: color.withOpacity(0.5), blurRadius: 6),
                    ],
                  ),
                ),
              ),
            );
          }).toList();

          return Stack(
            children: [
              FlutterMap(
                options: const MapOptions(
                  initialCenter: LatLng(20.5937, 78.9629), // Center of India
                  initialZoom: 5.0,
                ),
                children: [
                  TileLayer(
                    urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                    userAgentPackageName: 'in.gov.moes.ncmrwf.bustdetection',
                  ),
                  MarkerLayer(markers: markers),
                ],
              ),
              // Floating Map Legend
              Positioned(
                bottom: 16,
                left: 16,
                right: 16,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppConstants.cardDark.withOpacity(0.92),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.blueGrey.withOpacity(0.4)),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _LegendItem(color: AppConstants.riskLow, label: 'Low (<25%)'),
                      _LegendItem(color: AppConstants.riskModerate, label: 'Mod (25-50%)'),
                      _LegendItem(color: AppConstants.riskHigh, label: 'High (50-75%)'),
                      _LegendItem(color: AppConstants.riskVeryHigh, label: 'Very High'),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showStationDetails(BuildContext context, Map<String, dynamic> pt) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppConstants.cardDark,
      builder: (ctx) {
        final prob = ((pt['bust_probability'] as num?)?.toDouble() ?? 0.0) * 100;
        final rel = ((pt['reliability_score'] as num?)?.toDouble() ?? 1.0) * 100;
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${pt['name']}, ${pt['state'] ?? "India"}',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              Text(
                'Lat: ${(pt['latitude'] as num).toDouble().toStringAsFixed(2)}°, Lon: ${(pt['longitude'] as num).toDouble().toStringAsFixed(2)}°',
                style: const TextStyle(color: Colors.grey, fontSize: 12),
              ),
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  Column(
                    children: [
                      const Text('Bust Risk', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      Text('${prob.toStringAsFixed(1)}%',
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppConstants.riskHigh)),
                    ],
                  ),
                  Column(
                    children: [
                      const Text('Reliability', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      Text('${rel.toStringAsFixed(1)}%',
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: AppConstants.accentBlue)),
                    ],
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.white70)),
      ],
    );
  }
}
