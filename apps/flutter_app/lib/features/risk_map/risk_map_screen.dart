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
    final currentRegion = ref.watch(mapRegionProvider);
    final isExtended = AppConstants.isExtendedRange(selectedHours);
    final dayNum = (selectedHours / 24).round();

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
                        currentRegion == 'india'
                            ? 'Indian Synoptic Network (25 IMD Stations) · Day $dayNum'
                            : 'Global Synoptic Network · Day $dayNum',
                        style: const TextStyle(
                          fontSize: 11.5,
                          color: AppColors.textDim,
                        ),
                      ),
                    ],
                  ),
                  // Horizon selector dropdown (Day 1 to Day 30)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.card2,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: isExtended ? AppColors.orange.withOpacity(0.4) : AppColors.stroke,
                      ),
                    ),
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<int>(
                        value: selectedHours,
                        dropdownColor: AppColors.card,
                        icon: Icon(
                          Icons.arrow_drop_down,
                          color: isExtended ? AppColors.orange : AppColors.green,
                          size: 20,
                        ),
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: isExtended ? AppColors.orange : AppColors.green,
                        ),
                        items: AppConstants.operationalLeadHours.map((h) {
                          final d = (h / 24).round();
                          final ext = AppConstants.isExtendedRange(h);
                          return DropdownMenuItem(
                            value: h,
                            child: Text(
                              ext ? 'Day $d (Ext)' : 'Day $d',
                              style: TextStyle(
                                color: ext ? AppColors.orange : AppColors.green,
                                fontSize: 11.5,
                              ),
                            ),
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
              const SizedBox(height: 10),

              // Domain Scope Toggle (India Synoptic Grid vs Global Benchmark Network)
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: AppColors.card2,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.stroke),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          ref.read(mapRegionProvider.notifier).state = 'india';
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 7),
                          decoration: BoxDecoration(
                            color: currentRegion == 'india'
                                ? AppColors.green.withOpacity(0.15)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(8),
                            border: currentRegion == 'india'
                                ? Border.all(color: AppColors.green.withOpacity(0.3))
                                : null,
                          ),
                          child: Center(
                            child: Text(
                              '🇮🇳 India Synoptic (25 IMD)',
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                color: currentRegion == 'india' ? AppColors.green : AppColors.textDim,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Expanded(
                      child: InkWell(
                        onTap: () {
                          ref.read(mapRegionProvider.notifier).state = 'global';
                        },
                        borderRadius: BorderRadius.circular(8),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 7),
                          decoration: BoxDecoration(
                            color: currentRegion == 'global'
                                ? AppColors.green.withOpacity(0.15)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(8),
                            border: currentRegion == 'global'
                                ? Border.all(color: AppColors.green.withOpacity(0.3))
                                : null,
                          ),
                          child: Center(
                            child: Text(
                              '🌐 Global Network',
                              style: TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                color: currentRegion == 'global' ? AppColors.green : AppColors.textDim,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              // Extended Range Alert Banner for Days 8-30
              if (isExtended) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.orange.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.orange.withOpacity(0.35)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.info_outline, color: AppColors.orange, size: 16),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Day $dayNum ($selectedHours h): UNVALIDATED EXTENDED RANGE — exploratory estimate only.',
                          style: const TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: AppColors.orange,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
              ],

              // Legend Chips Row
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

                    // Region-dependent initial center and zoom
                    final initialCenter = currentRegion == 'india'
                        ? const LatLng(22.0, 79.0) // Center of India
                        : const LatLng(20.0, 15.0); // Global viewpoint
                    final initialZoom = currentRegion == 'india' ? 4.5 : 2.0;

                    return FlutterMap(
                      key: ValueKey('${currentRegion}_$selectedHours'),
                      options: MapOptions(
                        initialCenter: initialCenter,
                        initialZoom: initialZoom,
                        minZoom: 1.5,
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

              // Network Stations Header
              Text(
                currentRegion == 'india' ? 'INDIAN SYNOPTIC STATIONS' : 'GLOBAL BENCHMARK STATIONS',
                style: const TextStyle(
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
                  final displayList = stations.take(8).toList();
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
                                      '${AppConstants.formatCoordinates(st.latitude, st.longitude)} · Bust Risk ${(st.bustProbability * 100).toStringAsFixed(1)}%',
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
