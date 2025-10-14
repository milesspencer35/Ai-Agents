import asyncio
import httpx

import httpx
import logging
from fastmcp import FastMCP
from datetime import datetime
import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create an MCP server
mcp = FastMCP("Weather")

async def get_coordinates(client: httpx.AsyncClient, city: str) -> tuple[float, float]:
    """
    Fetch the latitude and longitude for a given city using the Open-Meteo Geocoding API.

    :param client: An instance of httpx.AsyncClient
    :param city: The name of the city to fetch coordinates for
    :return: A tuple (latitude, longitude)
    :raises ValueError: If the coordinates cannot be retrieved
    """
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    # let httpx encode for you
    geo_response = await client.get(geo_url, params={"name": city})

    geo_response = await client.get(
        f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    )
    if geo_response.status_code != 200 or "results" not in geo_response.json():
        raise ValueError(f"Error: Could not retrieve coordinates for {city}.")

    geo_data = geo_response.json()["results"][0]
    return geo_data["latitude"], geo_data["longitude"]


async def lookup_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        # Get coordinates using the Geocoding API
        try:
            try:
                latitude, longitude = await get_coordinates(client, city)
            except ValueError as e:
                return {'Error': f"Getting coordinates for city: {str(e)}"}
            # Get weather data using the Forecast API
            url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,weather_code&timezone=GMT&forecast_days=1"
            logger.info(f"api: {url}")
            weather_response = await client.get(url)
            if weather_response.status_code != 200:
                return {'Error': f"Could not retrieve weather information for {city}."}

            weather_data = weather_response.json()
        except Exception as e:
            logger.exception(f"API invoke error: {str(e)}")
            weather_data = {'Error': f"URL: {url} produced error: {str(e)}"}
        return weather_data


@mcp.tool
async def get_weather(location: str, unit: str = "f") -> dict:
    """Get current weather information for a specified city.
     It extracts the current hour's temperature and weather code, maps
     the weather code to a human-readable description, and returns a formatted summary.

    Parameters
    - location: city name or free-form location string
    - unit: "c" for Celsius or "f" for Fahrenheit. Defaults to Fahrenheit.

    Returns a JSON-serializable dict.
    """
    logger.info(f"Getting weather for {location} with unit: {unit}")

    unit = (unit or "f").lower()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    weather_data = await lookup_weather(location)
    if "Error" in weather_data:
        # return a clean error result instead of raising
        return {"location": location, "observed_at": now, "error": weather_data["Error"]}

    hourly = weather_data["hourly"]
    cur_idx = utils.get_closest_utc_index(hourly["time"])
    temp_c = hourly["temperature_2m"][cur_idx]
    weather_code = hourly["weather_code"][cur_idx]
    relative_humidity = hourly["relative_humidity_2m"][cur_idx]
    dew_point_c = hourly["dew_point_2m"][cur_idx]

    if unit == "f":
        temperature = f"{round((temp_c * 9 / 5) + 32, 1)}°F"
        dewpoint = f"{round((dew_point_c * 9 / 5) + 32, 1)}°F"
    else:
        temperature = f"{round(temp_c, 1)}°C"
        dewpoint = f"{round(dew_point_c, 1)}°C"

    return {
        "location": location,
        "observed_at": f"{now} GMT",
        "temperature": temperature,
        "conditions": utils.weather_descriptions.get(weather_code, "Unknown"),
        "humidity": relative_humidity,
        "dewpoint": dewpoint,
        "source": "Open-Meteo",
    }


from typing import Any, Dict
import yfinance as yf

@mcp.tool
def get_stock_quote(ticker: str) -> Dict[str, Any]:
    """Return a simple last price for a stock (Yahoo Finance via yfinance)."""
    t = yf.Ticker(ticker)
    info = getattr(t, "fast_info", {})
    last = getattr(info, "last_price", None) or (info.get("last_price") if isinstance(info, dict) else None)
    if last is None:
        hist = t.history(period="1d")
        last = float(hist["Close"][-1]) if len(hist) else None
    return {"ticker": ticker.upper(), "last_price": last}

async def main():
    weather = await get_weather("Highland, UT")
    print(weather)

if __name__ == "__main__":
    asyncio.run(main())