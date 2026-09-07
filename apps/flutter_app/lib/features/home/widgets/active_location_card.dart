import 'package:flutter/material.dart';
import '../../../core/constants.dart';
import '../../../models/weather_models.dart';
import 'location_search_dialog.dart';

class ActiveLocationCard extends StatefulWidget {
  final LocationModel location;

  const ActiveLocationCard({super.key, required this.location});

  @override
  State<ActiveLocationCard> createState() => _ActiveLocationCardState();
}

class _ActiveLocationCardState extends State<ActiveLocationCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.stroke),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'ACTIVE LOCATION',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textDim,
                        letterSpacing: 0.05,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      widget.location.displayName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: AppColors.text,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              Row(
                children: [
                  InkWell(
                    onTap: () {
                      setState(() {
                        _expanded = !_expanded;
                      });
                    },
                    borderRadius: BorderRadius.circular(8),
                    child: Padding(
                      padding: const EdgeInsets.all(6.0),
                      child: Icon(
                        _expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                        color: AppColors.textDim,
                        size: 20,
                      ),
                    ),
                  ),
                  const SizedBox(width: 6),
                  InkWell(
                    onTap: () {
                      showDialog(
                        context: context,
                        builder: (_) => const LocationSearchDialog(),
                      );
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                      decoration: BoxDecoration(
                        color: AppColors.green,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Text(
                        'Change',
                        style: TextStyle(
                          fontSize: 11.5,
                          fontWeight: FontWeight.w800,
                          color: AppColors.bgDark,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),

          // Expandable Synoptic Info & Coordinates Drawer
          if (_expanded) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.card2,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'LAT: ${widget.location.latitude.toStringAsFixed(4)}°N',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textDim,
                      fontFamily: 'monospace',
                    ),
                  ),
                  Text(
                    'LON: ${widget.location.longitude.toStringAsFixed(4)}°E',
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textDim,
                      fontFamily: 'monospace',
                    ),
                  ),
                  const Text(
                    'IMD SYNOP',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: AppColors.green,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}
