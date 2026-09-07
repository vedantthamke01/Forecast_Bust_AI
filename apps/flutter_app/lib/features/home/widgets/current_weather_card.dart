import 'package:flutter/material.dart';
import '../../../core/constants.dart';
import '../../../models/weather_models.dart';

class CurrentWeatherCard extends StatelessWidget {
  final CurrentWeather weather;

  const CurrentWeatherCard({super.key, required this.weather});

  IconData _getWeatherIcon(String cond) {
    switch (cond.toLowerCase()) {
      case 'clear sky':
        return Icons.wb_sunny_rounded;
      case 'partly cloudy':
        return Icons.cloud_queue_rounded;
      case 'overcast':
        return Icons.cloud_rounded;
      case 'light rain':
      case 'heavy rain':
        return Icons.water_drop_rounded;
      case 'windy':
        return Icons.air_rounded;
      default:
        return Icons.wb_cloudy_rounded;
    }
  }

  Color _getWeatherIconColor(String cond) {
    switch (cond.toLowerCase()) {
      case 'clear sky':
        return const Color(0xFFFFD15C);
      case 'partly cloudy':
      case 'overcast':
        return const Color(0xFFB0C5D8);
      case 'light rain':
      case 'heavy rain':
        return const Color(0xFF67B7FF);
      default:
        return AppColors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    final cond = weather.conditionText;
    final iconColor = _getWeatherIconColor(cond);

    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.stroke),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'CURRENT WEATHER',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textDim,
                  letterSpacing: 0.05,
                ),
              ),
              Builder(
                builder: (context) {
                  final isDemo = weather.provider == 'demo_verified';
                  final statusColor = isDemo ? AppColors.amber : AppColors.green;
                  final statusText = isDemo ? 'DEMO BENCHMARK (OFFLINE)' : 'LIVE CONDITIONS';

                  return Row(
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: statusColor,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 5),
                      Text(
                        statusText,
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: statusColor,
                          letterSpacing: 0.03,
                        ),
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Weather Hero Row
          Row(
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  gradient: RadialGradient(
                    center: const Alignment(-0.3, -0.3),
                    colors: [
                      iconColor.withOpacity(0.9),
                      iconColor.withOpacity(0.4),
                    ],
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: iconColor.withOpacity(0.2),
                      blurRadius: 12,
                      spreadRadius: 1,
                    ),
                  ],
                ),
                child: Center(
                  child: Icon(
                    _getWeatherIcon(cond),
                    color: Colors.white,
                    size: 32,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${weather.temperatureC.toStringAsFixed(1)}°C',
                      style: const TextStyle(
                        fontSize: 38,
                        fontWeight: FontWeight.w800,
                        color: AppColors.text,
                        letterSpacing: -0.5,
                      ),
                    ),
                    Row(
                      children: [
                        Text(
                          cond,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textDim,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '· ${weather.provider}',
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textFaint,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 3 or 4-Tile Stat Grid (Rain, Humidity, Wind, Pressure)
          Row(
            children: [
              Expanded(
                child: _buildStatTile(
                  value: '${weather.precipitationMm.toStringAsFixed(1)}mm',
                  label: 'Rain',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildStatTile(
                  value: '${(weather.humidityPercent ?? 0).round()}%',
                  label: 'Humidity',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildStatTile(
                  value: '${weather.windSpeedMps.toStringAsFixed(1)}m/s',
                  label: 'Wind',
                ),
              ),
              if (weather.pressureHpa != null) ...[
                const SizedBox(width: 8),
                Expanded(
                  child: _buildStatTile(
                    value: '${weather.pressureHpa!.round()}hPa',
                    label: 'Pressure',
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatTile({required String value, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 6),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 3),
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w600,
              color: AppColors.textFaint,
              letterSpacing: 0.04,
            ),
          ),
        ],
      ),
    );
  }
}
