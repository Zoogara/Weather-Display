# Weather-Display

ESPHome weather display for the Waveshare ESP32-S3-Touch-LCD-7 (16 MB flash), with Home Assistant supplying the data and images.
Tested on ESPHome 2026.10.2.

- `weather-lcd7.yaml` - the display config; it just lists the feature packages in `packages/weather-lcd7/` (hardware, core, weather, hourly, forecast, radar, history, lights, settings). Keep that folder next to it. Needs `wifi_ssid`, `wifi_password`, `ap_password` and `weather_lcd7__encryption_key` (a 32 byte base64 key, e.g. `openssl rand -base64 32`) in `secrets.yaml`. The API and OTA are both encrypted with that key. Set your own latitude/longitude and Home Assistant address (`192.168.0.100:8123`).
- `weather-lcd7-host.yaml` and `packages/host/` - a host (SDL window) build of the same UI for testing the layout on a Mac / Linux machine; swaps only the hardware package. See the comments at the top of the file.
- `maps/` - the radar base maps (map tiles, town names and a marker) drawn under the radar frames, one per zoom level (`radar_base_z5/z6/z7.png`). `python3 tools/make_radar_base.py LATITUDE LONGITUDE --out maps` makes them for your own location.
- `fonts/` - fonts used by the display.
- `homeassistant/` - the Home Assistant side:
  - `radar.yaml` - downloads Rainviewer radar frames to `/config/www/radar/` (zoom 5, 6 and 7: `<id>_z5.png`, `<id>.png`, `<id>_z7.png`) so the display, or any other display, fetches them over plain local HTTP.
  - `satellite.yaml` - downloads the latest NASA GIBS Himawari infrared image to `/config/www/` and exposes its time.
  - `template.yaml` - the template sensors (radar urls/timestamps, forecasts, icons, hourly data) and `tools.jinja`, its helper macros (copy to `/config/custom_templates/`).

The radar is six frames, replaced only once the whole new set has loaded. The + and - buttons on the radar zoom in (2x) and out (1/2x); the radar goes back to 1x when the screen sleeps. Double-tap the forecast panel to switch between the 7-day view and the long today/tomorrow text.
