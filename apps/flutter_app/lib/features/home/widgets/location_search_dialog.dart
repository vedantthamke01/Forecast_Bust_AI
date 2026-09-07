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
  List<LocationModel> _searchResults = [];
  bool _isLoading = false;
  String? _error;

  @override
  void dispose() {
    _searchController.dispose();
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

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: AppColors.strokeStrong, width: 1),
      ),
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
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
                  'Select Location',
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
                hintText: 'Search city or observatory...',
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
              Flexible(
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
                        '${item.latitude.toStringAsFixed(2)}°N, ${item.longitude.toStringAsFixed(2)}°E',
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
                    'POPULAR SYNOPTIC STATIONS',
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
                      return InkWell(
                        onTap: () {
                          final loc = LocationModel(
                            name: c['name'] as String,
                            state: c['state'] as String,
                            country: 'India',
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
                            color: AppColors.card2,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.stroke),
                          ),
                          child: Text(
                            c['name'] as String,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: AppColors.text,
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
    );
  }
}
