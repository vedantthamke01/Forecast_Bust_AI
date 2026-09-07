import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import '../../core/constants.dart';
import '../../models/risk_models.dart';
import '../../providers/app_providers.dart';
import 'widgets/station_detail_dialog.dart';

class RiskMapScreen extends ConsumerWidget {
  const RiskMapScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final mapDataAsync = ref.watch(spatialRiskMapProvider);
    final selectedHours = ref.watch(selectedLeadHoursProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Spatial Risk Map',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        '25 Indian synoptic stations · Day ${(selectedHours / 24).round()} (${selectedHours}h)',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textDim,
                        ),
                      ),
                    ],
                  ),
                  // Horizon selector dropdown
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.card2,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.stroke),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        value: selectedHours,
                        dropdownColor: AppColors.card,
                        icon: const Icon(Icons.arrow_drop_down, color: AppColors.green, size: 20),
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700, color: AppColors.green),
                        items: AppConstants.operationalLeadHours.map((h) {
                          return DropdownMenuItem(
                            value: h,
                            child: Text(AppConstants.dayLabelForHours(h)),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            ref.read(selectedLeadHoursProvider.notifier).state = val;
                          }
                        },
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Legend Chips Row (Full Screen Responsive)
              Row(
                children: [
                  _buildLegendChip(label: 'Low', color: AppColors.green),
                  const SizedBox(width: 8),
                  _buildLegendChip(label: 'Moderate', color: AppColors.amber),
                  const SizedBox(width: 8),
                  _buildLegendChip(label: 'High', color: AppColors.orange),
                  const SizedBox(width: 8),
                  _buildLegendChip(label: 'V.High', color: AppColors.red),
                ],
              ),
              const SizedBox(height: 12),

              // FULL-SCREEN RESPONSIVE MAP with flutter_map (Dark Tile Layer)
              Container(
                height: (MediaQuery.sizeOf(context).height * 0.44).clamp(320.0, 480.0),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.stroke),
                ),
                clipBehavior: Clip.antiAlias,
                child: mapDataAsync.when(
                  data: (stations) {
                    final points = stations.isNotEmpty
                        ? stations
                        : [
                            const StationRiskPoint(
                              stationName: 'Nagpur',
                              latitude: 21.1458,
                              longitude: 79.0882,
                              bustProbability: 0.007,
                              reliabilityScore: 0.993,
                              riskLevel: 'LOW',
                              riskBadge: '🟢 LOW',
                            ),
                          ];

                    return FlutterMap(
                      options: const MapOptions(
                        initialCenter: LatLng(22.0, 79.0), // Center of India
                        initialZoom: 4.5,
                        minZoom: 3.5,
                        maxZoom: 9.0,
                      ),
                      children: [
                        TileLayer(
                          urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                          subdomains: const ['a', 'b', 'c', 'd'],
                          userAgentPackageName: 'com.forecastbustai.app',
                        ),
                        MarkerLayer(
                          markers: points.map((st) {
                            final color = AppColors.forRiskLevel(st.riskLevel);
                            return Marker(
                              point: LatLng(st.latitude, st.longitude),
                              width: 26,
                              height: 26,
                              child: GestureDetector(
                                onTap: () {
                                  showDialog(
                                    context: context,
                                    builder: (_) => StationDetailDialog(station: st),
                                  );
                                },
                                child: Container(
                                  decoration: BoxDecoration(
                                    color: color,
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(
                                        color: color.withOpacity(0.6),
                                        blurRadius: 8,
                                        spreadRadius: 2,
                                      ),
                                    ],
                                  ),
                                  child: const Center(
                                    child: Icon(Icons.circle, color: Colors.black, size: 5),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ],
                    );
                  },
                  loading: () => Container(
                    color: AppColors.card2,
                    child: const Center(
                      child: CircularProgressIndicator(color: AppColors.green),
                    ),
                  ),
                  error: (err, _) => Container(
                    color: AppColors.card2,
                    child: Center(
                      child: Text(
                        'Map data offline: $err',
                        style: const TextStyle(color: AppColors.red, fontSize: 12),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Nearby Stations Header
              const Text(
                'NEARBY STATIONS',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textDim,
                  letterSpacing: 0.05,
                ),
              ),
              const SizedBox(height: 8),

              // Dynamic Stations List
              mapDataAsync.when(
                data: (stations) {
                  final displayList = stations.take(6).toList();
                  if (displayList.isEmpty) {
                    return const Text(
                      'No stations available for this horizon.',
                      style: TextStyle(fontSize: 12, color: AppColors.textFaint),
                    );
                  }
                  return Column(
                    children: displayList.map((st) {
                      final riskColor = AppColors.forRiskLevel(st.riskLevel);
                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: AppColors.card2,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.stroke),
                        ),
                        child: InkWell(
                          onTap: () {
                            showDialog(
                              context: context,
                              builder: (_) => StationDetailDialog(station: st),
                            );
                          },
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      st.stationName,
                                      style: const TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.text,
                                      ),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${st.latitude.toStringAsFixed(2)}°N, ${st.longitude.toStringAsFixed(2)}°E · Bust Risk ${(st.bustProbability * 100).toStringAsFixed(1)}%',
                                      style: const TextStyle(
                                        fontSize: 11,
                                        color: AppColors.textFaint,
                                      ),
                                    ),
                                  ],
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: riskColor.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    st.riskLevel,
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w800,
                                      color: riskColor,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  );
                },
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: CircularProgressIndicator(color: AppColors.green, strokeWidth: 2),
                  ),
                ),
                error: (_, __) => const Text(
                  'Stations unavailable.',
                  style: TextStyle(color: AppColors.red, fontSize: 12),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildLegendChip({required String label, required Color color}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
          ),
        ],
      ),
    );
  }
}
