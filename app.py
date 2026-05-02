from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

WEATHER_API_KEY = "7a7cb98646bf48c3974131113260205"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EuropeWeatherApp/1.0)"
}

def get_europe_countries():
    url = "https://restcountries.com/v3.1/region/europe"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    countries = []
    for country in data:
        capitals = country.get("capital", [])
        capital = capitals[0] if capitals else "N/A"
        flags = country.get("flags", {})
        flag_url = flags.get("png", flags.get("svg", ""))
        countries.append({
            "name": country.get("name", {}).get("common", "Unknown"),
            "capital": capital,
            "flag": flag_url,
            "population": country.get("population", 0),
        })
    countries.sort(key=lambda x: x["name"])
    return countries

def get_weather(city):
    if not city or city == "N/A":
        return None
    url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHER_API_KEY, "q": city, "aqi": "no"}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        current = data["current"]
        condition = current["condition"]
        return {
            "temp_c":       current["temp_c"],
            "temp_f":       current["temp_f"],
            "feels_like_c": current["feelslike_c"],
            "humidity":     current["humidity"],
            "wind_kph":     current["wind_kph"],
            "condition":    condition["text"],
            "icon":         "https:" + condition["icon"],
            "uv":           current.get("uv", 0),
        }
    except Exception as e:
        return {"error": str(e)}

_countries_cache = None

def countries_cached():
    global _countries_cache
    if _countries_cache is None:
        _countries_cache = get_europe_countries()
    return _countries_cache

@app.route("/")
def index():
    return render_template("index.html", countries=countries_cached())

@app.route("/api/country")
def country_data():
    name = request.args.get("name", "")
    country = next((c for c in countries_cached() if c["name"] == name), None)
    if not country:
        return jsonify({"error": "Country not found"}), 404
    result = dict(country)
    result["weather"] = get_weather(country["capital"])
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)