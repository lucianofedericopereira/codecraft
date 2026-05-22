---
title: "Waybar Weather Widget: Live Weather in Your Status Bar"
date: 2026-04-06
comments: true
---

**Waybar Weather Widget**: A lightweight Python script that queries the OpenWeather API and displays current weather conditions in Waybar — your Wayland status bar — using Nerd Font icons and minimal JSON output.

## The Wayland Status Bar

Waybar is the standard status bar for Sway and other wlroots-based Wayland compositors. It displays workspaces, system stats, and custom modules. The custom module interface is clean: Waybar runs a script periodically, reads its JSON output, and displays it. The script can be anything.

```json
{
  "text": " 18°C",
  "tooltip": "Buenos Aires — Partly Cloudy\nHumidity: 65%\nWind: 12 km/h NE",
  "class": "partly-cloudy"
}
```

That's the contract. Output this JSON, and Waybar handles the display.

## The Script

```python
#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.parse

API_KEY = "your_openweather_api_key"
CITY    = "Buenos Aires"
UNITS   = "metric"

ICONS = {
    "Clear":        "",   # sun
    "Clouds":       "",   # cloud
    "Rain":         "",   # rain
    "Drizzle":      "",   # drizzle
    "Thunderstorm": "",   # thunder
    "Snow":         "",   # snow
    "Mist":         "",   # mist
    "Fog":          "",   # fog
}

def fetch_weather(city: str, api_key: str, units: str) -> dict:
    params = urllib.parse.urlencode({
        "q":     city,
        "appid": api_key,
        "units": units,
    })
    url = f"https://api.openweathermap.org/data/2.5/weather?{params}"
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read())

def main():
    try:
        data = fetch_weather(CITY, API_KEY, UNITS)
        condition = data["weather"][0]["main"]
        temp      = round(data["main"]["temp"])
        humidity  = data["main"]["humidity"]
        wind      = round(data["wind"]["speed"] * 3.6)  # m/s → km/h
        direction = data["wind"].get("deg", 0)

        icon = ICONS.get(condition, "")
        compass = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        wind_dir = compass[round(direction / 45) % 8]

        output = {
            "text":    f"{icon} {temp}°C",
            "tooltip": f"{CITY} — {condition}\nHumidity: {humidity}%\nWind: {wind} km/h {wind_dir}",
            "class":   condition.lower().replace(" ", "-"),
        }
        print(json.dumps(output))

    except Exception as e:
        print(json.dumps({"text": " --", "tooltip": str(e), "class": "error"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

The error handling matters: if the API is unreachable or the key is expired, Waybar should show a graceful placeholder, not break your entire status bar.

## Waybar Configuration

```json
"custom/weather": {
    "exec":          "~/.local/bin/waybar-weather",
    "interval":      1800,
    "return-type":   "json",
    "format":        "{}",
    "on-click":      "xdg-open 'https://openweathermap.org/city/'"
}
```

`interval: 1800` refreshes every 30 minutes. Weather doesn't change faster than that, and the OpenWeather free tier allows 1000 calls/day — easily accommodated.

## CSS Styling

The `class` field lets you style each weather condition differently:

```css
#custom-weather {
    padding: 0 10px;
    color: @text;
}

#custom-weather.clear {
    color: #fabd2f;   /* Gruvbox yellow for sunny */
}

#custom-weather.rain,
#custom-weather.drizzle {
    color: #83a598;   /* Gruvbox blue for rain */
}

#custom-weather.thunderstorm {
    color: #d3869b;   /* Gruvbox purple for storms */
}

#custom-weather.snow {
    color: #8ec07c;   /* Gruvbox green for snow */
}
```

## Installation

```bash
# Clone and install
git clone https://github.com/lucianofedericopereira/waybar-weather-widget
cp waybar-weather-widget/weather.py ~/.local/bin/waybar-weather
chmod +x ~/.local/bin/waybar-weather

# Set your API key and city in the script
# Get a free key at openweathermap.org

# Test it
~/.local/bin/waybar-weather
```

The script uses only Python's standard library — `json`, `urllib`, `sys`. No `pip install` required.

## Why Python for a System Widget

Same logic as other tools in this collection: Python is pre-installed on virtually every Linux system. A script that uses only the standard library runs on any Python 3.6+ installation without a virtualenv, without pip, without anything beyond the interpreter that's already there.

For a script that runs every 30 minutes and takes 200ms to execute, startup time and memory footprint are irrelevant. Readability and zero-dependency deployment are what matter.

## Links

- **GitHub**: [lucianofedericopereira/waybar-weather-widget](https://github.com/lucianofedericopereira/waybar-weather-widget)
- **OpenWeather API**: [openweathermap.org/api](https://openweathermap.org/api)

## License

MIT
