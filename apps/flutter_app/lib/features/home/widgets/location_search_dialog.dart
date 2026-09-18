import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants.dart';
import '../../../models/weather_models.dart';
import '../../../providers/app_providers.dart';

class LocationSearchDialog extends ConsumerStatefulWidget {
  const LocationSearchDialog({super.key});

  @override
  ConsumerState<LocationSearchDialog> createState() => _LocationSearchDialogState();
}

class _LocationSearchDialogState extends ConsumerState<LocationSearchDialog> {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _latController = TextEditingController();
  final TextEditingController _lonController = TextEditingController();

  List<LocationModel> _searchResults = [];
  bool _isLoading = false;
  String? _error;
  bool _showCoordinateInput = false;

  @override
  void dispose() {
    _searchController.dispose();
    _latController.dispose();
    _lonController.dispose();
    super.dispose();
  }

  Future<void> _performSearch(String q) async {
    if (q.trim().isEmpty) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final api = ref.read(apiServiceProvider);
      final results = await api.searchLocations(q.trim());
      if (mounted) {
        setState(() {
          _searchResults = results;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Search failed. Check network or server connection.';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _detectGpsLocation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final locService = ref.read(locationServiceProvider);
      final loc = await locService.getCurrentGpsLocation();
      if (loc != null && mounted) {
        ref.read(activeLocationProvider.notifier).state = loc;
        await locService.saveLocation(loc);
        if (mounted) Navigator.of(context).pop();
      } else if (mounted) {
        setState(() {
          _error = 'GPS unavailable or permission denied.';
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Error querying GPS: $e';
          _isLoading = false;
        });
      }
    }
  }

  void _applyManualCoordinates() {
    final latText = _latController.text.trim();
    final lonText = _lonController.text.trim();

    final lat = double.tryParse(latText);
    final lon = double.tryParse(lonText);

    if (lat == null || lat < -90.0 || lat > 90.0) {
      setState(() {
        _error = 'Latitude must be a valid number between -90.0 and 90.0';
      });
      return;
    }

    if (lon == null || lon < -180.0 || lon > 180.0) {
      setState(() {
        _error = 'Longitude must be a valid number between -180.0 and 180.0';
      });
      return;
    }

    final loc = LocationModel(
      name: 'Custom Location',
      state: AppConstants.formatLat(lat),
      country: AppConstants.formatLon(lon),
      latitude: lat,
      longitude: lon,
    );

    ref.read(activeLocationProvider.notifier).state = loc;
    ref.read(locationServiceProvider).saveLocation(loc);
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: AppColors.strokeStrong, width: 1),
      ),
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Select Location (Global)',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AppColors.text,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: AppColors.textDim, size: 20),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // GPS Auto-detect Button
              InkWell(
                onTap: _detectGpsLocation,
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  decoration: BoxDecoration(
                    color: AppColors.green.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.green.withOpacity(0.3)),
                  ),
                  child: Row(
                    children: const [
                      Icon(Icons.my_location, color: AppColors.green, size: 18),
                      SizedBox(width: 8),
                      Text(
                        'Use Device GPS Location',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppColors.green,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // Search Bar
              TextField(
                controller: _searchController,
                onSubmitted: _performSearch,
                style: const TextStyle(color: AppColors.text, fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Search worldwide city or observatory...',
                  hintStyle: const TextStyle(color: AppColors.textFaint, fontSize: 12),
                  prefixIcon: const Icon(Icons.search, color: AppColors.textDim, size: 18),
                  suffixIcon: IconButton(
                    icon: const Icon(Icons.arrow_forward, color: AppColors.green, size: 18),
                    onPressed: () => _performSearch(_searchController.text),
                  ),
                  filled: true,
                  fillColor: AppColors.card2,
                  contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
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
              const SizedBox(height: 10),

              // Toggle Manual Coordinates
              InkWell(
                onTap: () {
                  setState(() {
                    _showCoordinateInput = !_showCoordinateInput;
                  });
                },
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    children: [
                      Icon(
                        _showCoordinateInput ? Icons.tune : Icons.add_location_alt_outlined,
                        color: AppColors.green,
                        size: 16,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        _showCoordinateInput ? 'Hide Coordinate Input' : 'Enter Custom Lat / Lon Coordinates',
                        style: const TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w700,
                          color: AppColors.green,
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Manual Coordinates Section
              if (_showCoordinateInput) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.card2,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.strokeStrong),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'GLOBAL COORDINATE INPUT',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textDim,
                          letterSpacing: 0.05,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _latController,
                              keyboardType: const TextInputType.numberWithOptions(signed: true, decimal: true),
                              style: const TextStyle(color: AppColors.text, fontSize: 12.5),
                              decoration: InputDecoration(
                                labelText: 'Latitude (-90 to 90)',
                                labelStyle: const TextStyle(color: AppColors.textFaint, fontSize: 11),
                                hintText: 'e.g. 35.6762',
                                hintStyle: const TextStyle(color: AppColors.textFaint, fontSize: 11),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: TextField(
                              controller: _lonController,
                              keyboardType: const TextInputType.numberWithOptions(signed: true, decimal: true),
                              style: const TextStyle(color: AppColors.text, fontSize: 12.5),
                              decoration: InputDecoration(
                                labelText: 'Longitude (-180 to 180)',
                                labelStyle: const TextStyle(color: AppColors.textFaint, fontSize: 11),
                                hintText: 'e.g. 139.6503',
                                hintStyle: const TextStyle(color: AppColors.textFaint, fontSize: 11),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: _applyManualCoordinates,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.green,
                            foregroundColor: AppColors.bgDark,
                            padding: const EdgeInsets.symmetric(vertical: 8),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          icon: const Icon(Icons.check_circle_outline, size: 16),
                          label: const Text(
                            'Apply Coordinates',
                            style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 12),

              if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: CircularProgressIndicator(color: AppColors.green),
                  ),
                )
              else if (_error != null)
                Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: AppColors.red, fontSize: 11),
                  ),
                )
              else if (_searchResults.isNotEmpty)
                ConstrainedBox(
                  constraints: const BoxConstraints(maxHeight: 220),
                  child: ListView.separated(
                    shrinkWrap: true,
                    itemCount: _searchResults.length,
                    separatorBuilder: (_, __) => const Divider(color: AppColors.stroke, height: 1),
                    itemBuilder: (context, i) {
                      final item = _searchResults[i];
                      return ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                        dense: true,
                        title: Text(
                          item.displayName,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.text),
                        ),
                        subtitle: Text(
                          item.formattedCoordinates,
                          style: const TextStyle(fontSize: 10, color: AppColors.textFaint),
                        ),
                        trailing: const Icon(Icons.chevron_right, color: AppColors.green, size: 18),
                        onTap: () {
                          ref.read(activeLocationProvider.notifier).state = item;
                          ref.read(locationServiceProvider).saveLocation(item);
                          Navigator.of(context).pop();
                        },
                      );
                    },
                  ),
                )
              else
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'GLOBAL BENCHMARK OBSERVATORIES',
                      style: TextStyle(
                        fontSize: 8.5,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textDim,
                        letterSpacing: 0.05,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: AppConstants.presetCities.map((c) {
                        final isDefault = c['name'] == AppConstants.defaultCity;
                        return InkWell(
                          onTap: () {
                            final loc = LocationModel(
                              name: c['name'] as String,
                              state: c['state'] as String?,
                              country: c['country'] as String?,
                              latitude: (c['lat'] as num).toDouble(),
                              longitude: (c['lon'] as num).toDouble(),
                            );
                            ref.read(activeLocationProvider.notifier).state = loc;
                            ref.read(locationServiceProvider).saveLocation(loc);
                            Navigator.of(context).pop();
                          },
                          borderRadius: BorderRadius.circular(10),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                            decoration: BoxDecoration(
                              color: isDefault ? AppColors.green.withOpacity(0.15) : AppColors.card2,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: isDefault ? AppColors.green : AppColors.stroke,
                              ),
                            ),
                            child: Text(
                              '${c['name']}${c['country'] != null ? ' (${c['country']})' : ''}',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: isDefault ? AppColors.green : AppColors.text,
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }
}
