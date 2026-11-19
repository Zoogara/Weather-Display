# Weather-Display

ESPHome weather display for the Waveshare ESP32-S3-Touch-LCD-7 (16 MB flash), with Home Assistant supplying the data and images.
Tested on ESPHome 2026.10.2.

- `screentest.yaml` - the display config; it just lists the feature packages in `packages/screentest/` (hardware, core, weather, hourly, forecast, radar, history, lights, settings). Keep that folder next to it. Needs `wifi_ssid`, `wifi_password`, `ap_password` and `screentest__encryption_key` (a 32 byte base64 key, e.g. `openssl rand -base64 32`) in `secrets.yaml`. The API and OTA are both encrypted with that key. Set your own latitude/longitude and Home Assistant address (`192.168.0.100:8123`).
- `screentest-host.yaml` and `packages/host/` - a host (SDL window) build of the same UI for testing the layout on a Mac / Linux machine; swaps only the hardware package. See the comments at the top of the file.
- `radar_base.png` - radar base map (map tiles plus town labels) drawn under the radar frames.
- `fonts/` - fonts used by the display.
- `homeassistant/` - the Home Assistant side:
  - `radar.yaml` - downloads Rainviewer radar frames to `/config/www/radar/` so the display fetches them over plain local HTTP.
  - `satellite.yaml` - downloads the latest NASA GIBS Himawari infrared image to `/config/www/` and exposes its time.
  - `template.yaml` - the template sensors (radar urls/timestamps, forecasts, icons, hourly data) and `tools.jinja`, its helper macros (copy to `/config/custom_templates/`).

The radar is six frames, replaced only once the whole new set has loaded. Double-tap the forecast panel to switch between the 7-day view and the long today/tomorrow text.
