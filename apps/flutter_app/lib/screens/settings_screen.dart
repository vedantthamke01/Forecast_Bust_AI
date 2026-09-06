import 'package:flutter/material.dart';
import 'package:forecast_bust_detection/core/constants.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('System Settings & Scientific Info')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Scientific Disclaimer Card
          Card(
            color: AppConstants.cardDark,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.shield_outlined, color: AppConstants.accentBlue),
                      SizedBox(width: 8),
                      Text('Scientific Mandate', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ],
                  ),
                  SizedBox(height: 10),
                  Text(
                    AppConstants.scientificDisclaimer,
                    style: TextStyle(fontSize: 12, color: Colors.white70, height: 1.4),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Provider & Budget Status
          Card(
            color: AppConstants.cardDark,
            child: Column(
              children: [
                const ListTile(
                  leading: Icon(Icons.currency_rupee, color: Colors.green),
                  title: Text('Operational Budget'),
                  subtitle: Text('Strict ₹0 (100% Free & Open-Source)'),
                ),
                const Divider(height: 1),
                const ListTile(
                  leading: Icon(Icons.cloud_sync, color: AppConstants.accentBlue),
                  title: Text('Data Providers'),
                  subtitle: Text('Open-Meteo (Free NWP) + ERA5 Reanalysis + Benchmark Demo'),
                ),
                const Divider(height: 1),
                const ListTile(
                  leading: Icon(Icons.map, color: Colors.amber),
                  title: Text('Spatial Mapping Engine'),
                  subtitle: Text('OpenStreetMap (ODbL) + Leaflet / flutter_map'),
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.psychology, color: Colors.purpleAccent),
                  title: const Text('ML Model Architecture'),
                  subtitle: const Text('LightGBM + Isotonic Calibration + TreeSHAP (Local CPU)'),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppConstants.riskLow.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('PRODUCTION', style: TextStyle(color: AppConstants.riskLow, fontSize: 11, fontWeight: FontWeight.bold)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Project Metadata
          Card(
            color: AppConstants.cardDark,
            child: const Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('About the Project', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  SizedBox(height: 8),
                  Text('Problem Statement: SIH26079', style: TextStyle(fontSize: 13, color: Colors.grey)),
                  Text('Department: National Centre for Medium Range Weather Forecasting (NCMRWF)', style: TextStyle(fontSize: 13, color: Colors.grey)),
                  Text('Ministry: Ministry of Earth Sciences (MoES), Government of India', style: TextStyle(fontSize: 13, color: Colors.grey)),
                  Text('Version: 1.0.0 (Production Quality)', style: TextStyle(fontSize: 13, color: Colors.grey)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
