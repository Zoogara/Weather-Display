# Weather-Display

ESPHome weather display for the Waveshare ESP32-S3-Touch-LCD-7 (16 MB flash), with Home Assistant supplying the data and images.
Tested on ESPHome 2026.10.2.

- `screentest.yaml` - the display config. Needs `wifi_ssid`, `wifi_password`, `weather_ap_password` and `weather_ota_password` in `secrets.yaml`. Set your own latitude/longitude and Home Assistant address (`192.168.0.100:8123`).
- `radar_base.png` - radar base map (map tiles plus town labels) drawn under the radar frames.
- `fonts/` - fonts used by the display.
- `homeassistant/` - the Home Assistant side:
  - `radar.yaml` - downloads Rainviewer radar frames to `/config/www/radar/` so the display fetches them over plain local HTTP.
  - `satellite.yaml` - downloads the latest NASA GIBS Himawari infrared image to `/config/www/` and exposes its time.
  - `template.yaml` - the template sensors (radar urls/timestamps, forecasts, icons, hourly data) and `tools.jinja`, its helper macros (copy to `/config/custom_templates/`).

The radar is six frames, replaced only once the whole new set has loaded. Double-tap the forecast panel to switch between the 7-day view and the long today/tomorrow text.
