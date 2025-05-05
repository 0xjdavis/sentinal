import streamlit as st
import time
import json
import requests
from datetime import datetime
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# API Keys
TOMORROW_API_KEY = 'fJXZ5YVJ48PQqc7Nk5cLQ850iLfLVx9b'

# API endpoint functionality
def handle_api_requests():
    """Handle API requests through URL parameters"""
    params = st.query_params
    
    # Check if this is an API request
    if "request_type" in params:
        request_type = params.get("request_type")
        
        # Get common parameters
        try:
            lat = float(params.get("lat", "0"))
            lon = float(params.get("lon", "0"))
            source = params.get("source", "nws")
            
            # Process different request types
            if request_type == "weather":
                # Weather request
                st.session_state.api_response = process_weather_request(lat, lon, source)
                return True
                
            elif request_type == "forecast":
                # Forecast request
                st.session_state.api_response = process_forecast_request(lat, lon, source)
                return True
                
            elif request_type == "geocoding":
                # Geocoding request
                query = params.get("query", "")
                st.session_state.api_response = process_geocoding_request(query)
                return True
                
            elif request_type == "healthcheck":
                # Health check endpoint
                st.session_state.api_response = {"status": "ok", "message": "Weather API is running"}
                return True
        except Exception as e:
            st.session_state.api_response = {"success": False, "error": str(e)}
            return True
    
    return False

# Process weather request
def process_weather_request(lat, lon, source):
    """Process a weather data request"""
    if "ui_agent" not in st.session_state:
        return {"success": False, "message": "Weather service not initialized"}
    
    result = st.session_state.ui_agent.get_weather_for_location(lat, lon, source)
    return result

# Process forecast request
def process_forecast_request(lat, lon, source):
    """Process a forecast data request"""
    if "ui_agent" not in st.session_state:
        return {"success": False, "message": "Weather service not initialized"}
    
    result = st.session_state.ui_agent.get_forecast_for_location(lat, lon, source)
    return result

# Process geocoding request
def process_geocoding_request(query):
    """Process a geocoding request"""
    if "geocoding_agent" not in st.session_state:
        return {"success": False, "message": "Geocoding service not initialized"}
    
    result = st.session_state.geocoding_agent.search_location(query)
    return result

# Display API response for API requests
def display_api_response():
    """Display API response for API requests"""
    if "api_response" in st.session_state:
        # Display the response in a code block
        st.json(st.session_state.api_response)
        
        # Add information about how to use the API
        st.markdown("""
        ## Weather API
        
        This endpoint can be used by other applications to get weather data.
        
        ### Example Requests:
        
        **Get Weather:**
        ```
        GET /?request_type=weather&lat=39.1395453&lon=-120.1664349&source=nws
        ```
        
        **Get Forecast:**
        ```
        GET /?request_type=forecast&lat=39.1395453&lon=-120.1664349&source=tomorrow
        ```
        
        **Geocode Location:**
        ```
        GET /?request_type=geocoding&query=donner+lake
        ```
        
        **Health Check:**
        ```
        GET /?request_type=healthcheck
        ```
        """)
        
        # Don't continue with normal app rendering
        st.stop()

# Weather Data Agent - Agent responsible for fetching and processing weather data
class WeatherDataAgent:
    def __init__(self):
        self.name = "WeatherDataAgent"
        self.cache = {}  # Simple cache for weather data
        
    # Method to receive messages from other agents
    def receive_message(self, message):
        st.session_state.logs.append(f"{self.name} received: {json.dumps(message)}")
        
        if message["type"] == "WEATHER_REQUEST":
            return self.handle_weather_request(message["data"])
        elif message["type"] == "FORECAST_REQUEST":
            return self.handle_forecast_request(message["data"])
        else:
            return {
                "type": "ERROR",
                "data": "Unknown message type"
            }
    
    # Handle weather data requests
    def handle_weather_request(self, data):
        # Extract parameters
        longitude = data["longitude"]
        latitude = data["latitude"]
        source = data.get("source", "nws")  # Default to NWS
        
        # Create cache key
        cache_key = f"{source}_{latitude}_{longitude}"
        
        # Check cache first (with a 15-minute expiration)
        current_time = time.time()
        if cache_key in self.cache and current_time - self.cache[cache_key]["timestamp"] < 900:  # 15 minutes
            st.session_state.logs.append(f"{self.name}: Using cached data for {latitude}, {longitude} from {source}")
            return {
                "type": "WEATHER_RESPONSE",
                "data": self.cache[cache_key]["data"]
            }
        
        # Log data retrieval
        st.session_state.logs.append(f"{self.name}: Fetching weather data for {latitude}, {longitude} from {source}")
        
        try:
            # Fetch data from appropriate source
            if source == "nws":
                weather_data = self.fetch_nws_data(longitude, latitude)
            elif source == "tomorrow":
                weather_data = self.fetch_tomorrow_data(longitude, latitude)
            else:
                return {
                    "type": "ERROR",
                    "data": f"Unknown source: {source}"
                }
            
            # Store in cache with timestamp
            self.cache[cache_key] = {
                "timestamp": current_time,
                "data": weather_data
            }
            
            return {
                "type": "WEATHER_RESPONSE",
                "data": weather_data
            }
            
        except Exception as e:
            st.session_state.logs.append(f"{self.name}: Error fetching data: {str(e)}")
            return {
                "type": "ERROR",
                "data": f"Error fetching data: {str(e)}"
            }
    
    # Handle forecast requests
    def handle_forecast_request(self, data):
        # Extract parameters
        longitude = data["longitude"]
        latitude = data["latitude"]
        source = data.get("source", "nws")  # Default to NWS
        
        # Create cache key
        cache_key = f"forecast_{source}_{latitude}_{longitude}"
        
        # Check cache first (with a 30-minute expiration)
        current_time = time.time()
        if cache_key in self.cache and current_time - self.cache[cache_key]["timestamp"] < 1800:  # 30 minutes
            st.session_state.logs.append(f"{self.name}: Using cached forecast for {latitude}, {longitude} from {source}")
            return {
                "type": "FORECAST_RESPONSE",
                "data": self.cache[cache_key]["data"]
            }
        
        try:
            # Fetch forecast data from appropriate source
            if source == "nws":
                forecast_data = self.fetch_nws_forecast(longitude, latitude)
            elif source == "tomorrow":
                forecast_data = self.fetch_tomorrow_forecast(longitude, latitude)
            else:
                return {
                    "type": "ERROR",
                    "data": f"Unknown source: {source}"
                }
            
            # Store in cache with timestamp
            self.cache[cache_key] = {
                "timestamp": current_time,
                "data": forecast_data
            }
            
            return {
                "type": "FORECAST_RESPONSE",
                "data": forecast_data
            }
            
        except Exception as e:
            st.session_state.logs.append(f"{self.name}: Error fetching forecast: {str(e)}")
            return {
                "type": "ERROR",
                "data": f"Error fetching forecast: {str(e)}"
            }
    
    # Fetch data from National Weather Service API
    def fetch_nws_data(self, longitude, latitude):
        # First, fetch metadata for the point to get the forecast URL
        point_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        point_response = requests.get(point_url)
        
        if not point_response.ok:
            raise Exception(f"Failed to fetch point metadata: {point_response.status_code}")
        
        point_data = point_response.json()
        
        # Fetch the forecast data
        forecast_url = point_data["properties"]["forecast"]
        forecast_response = requests.get(forecast_url)
        
        if not forecast_response.ok:
            raise Exception(f"Failed to fetch forecast data: {forecast_response.status_code}")
        
        forecast_data = forecast_response.json()
        
        # Fetch the hourly forecast data for more detailed precipitation information
        hourly_forecast_url = point_data["properties"]["forecastHourly"]
        hourly_forecast_response = requests.get(hourly_forecast_url)
        
        if not hourly_forecast_response.ok:
            raise Exception(f"Failed to fetch hourly forecast data: {hourly_forecast_response.status_code}")
        
        hourly_data = hourly_forecast_response.json()
        
        # Determine current precipitation type from forecast data
        precip_type = self.determine_precipitation_type(forecast_data, hourly_data)
        
        # Build the response data structure
        current_period = forecast_data["properties"]["periods"][0]
        location = point_data["properties"]["relativeLocation"]["properties"]
        
        response_data = {
            "source": "nws",
            "location": {
                "city": location["city"],
                "state": location["state"]
            },
            "current": {
                "temperature": current_period["temperature"],
                "temperatureUnit": current_period["temperatureUnit"],
                "shortForecast": current_period["shortForecast"],
                "detailedForecast": current_period["detailedForecast"],
                "windSpeed": current_period["windSpeed"],
                "windDirection": current_period["windDirection"],
                "icon": current_period["icon"],
                "precipitationType": precip_type,
                "probabilityOfPrecipitation": current_period.get("probabilityOfPrecipitation", {}).get("value", 0)
            },
            "pointData": point_data,
            "forecastData": forecast_data,
            "hourlyData": hourly_data
        }
        
        return response_data
    
    # Fetch data from Tomorrow.io API
    def fetch_tomorrow_data(self, longitude, latitude):
        # Format the request URL
        url = f"https://api.tomorrow.io/v4/weather/realtime?location={latitude},{longitude}&apikey={TOMORROW_API_KEY}"
        
        # Make the request
        response = requests.get(url)
        
        if not response.ok:
            raise Exception(f"Failed to fetch Tomorrow.io data: {response.status_code}")
        
        # Parse the response
        data = response.json()
        
        # Extract the current conditions
        values = data["data"]["values"]
        
        # Build the response data structure
        response_data = {
            "source": "tomorrow",
            "location": {
                "coordinates": {
                    "lat": latitude,
                    "lon": longitude
                }
            },
            "current": {
                "temperature": values["temperature"],
                "temperatureApparent": values["temperatureApparent"],
                "weatherCode": values["weatherCode"],
                "weatherText": self.get_weather_text(values["weatherCode"]),
                "windSpeed": values["windSpeed"],
                "windDirection": values["windDirection"],
                "windGust": values.get("windGust", 0),
                "humidity": values["humidity"],
                "precipitationProbability": values.get("precipitationProbability", 0),
                "precipitationType": values.get("precipitationType", 0),
                "visibility": values.get("visibility", 0),
                "cloudCover": values.get("cloudCover", 0),
                "uvIndex": values.get("uvIndex", 0)
            },
            "rawData": data
        }
        
        return response_data
    
    # Fetch forecast data from NWS
    def fetch_nws_forecast(self, longitude, latitude):
        # We already have the forecast data in the weather call, so reuse it
        weather_data = self.fetch_nws_data(longitude, latitude)
        
        # Extract forecast periods from the data
        periods = weather_data["forecastData"]["properties"]["periods"]
        hourly_periods = weather_data["hourlyData"]["properties"]["periods"]
        
        # Build a list of forecast periods
        forecast_periods = []
        
        for period in periods:
            forecast_periods.append({
                "name": period["name"],
                "startTime": period["startTime"],
                "endTime": period["endTime"],
                "temperature": period["temperature"],
                "temperatureUnit": period["temperatureUnit"],
                "shortForecast": period["shortForecast"],
                "detailedForecast": period["detailedForecast"],
                "windSpeed": period["windSpeed"],
                "windDirection": period["windDirection"],
                "icon": period["icon"],
                "isDaytime": period["isDaytime"],
                "probabilityOfPrecipitation": period.get("probabilityOfPrecipitation", {}).get("value", 0)
            })
        
        # Build a list of hourly forecasts (first 24 hours)
        hourly_forecasts = []
        
        for period in hourly_periods[:24]:
            hourly_forecasts.append({
                "time": period["startTime"],
                "temperature": period["temperature"],
                "temperatureUnit": period["temperatureUnit"],
                "shortForecast": period["shortForecast"],
                "windSpeed": period["windSpeed"],
                "windDirection": period["windDirection"],
                "icon": period["icon"],
                "probabilityOfPrecipitation": period.get("probabilityOfPrecipitation", {}).get("value", 0)
            })
        
        return {
            "source": "nws",
            "forecastPeriods": forecast_periods,
            "hourlyForecasts": hourly_forecasts,
            "location": weather_data["location"]
        }
    
    # Fetch forecast data from Tomorrow.io
    def fetch_tomorrow_forecast(self, longitude, latitude):
        # Format the request URL
        url = f"https://api.tomorrow.io/v4/weather/forecast?location={latitude},{longitude}&apikey={TOMORROW_API_KEY}"
        
        # Make the request
        response = requests.get(url)
        
        if not response.ok:
            raise Exception(f"Failed to fetch Tomorrow.io forecast data: {response.status_code}")
        
        # Parse the response
        data = response.json()
        
        # Return the forecast data
        return {
            "source": "tomorrow",
            "location": {
                "coordinates": {
                    "lat": latitude,
                    "lon": longitude
                }
            },
            "timelines": data["timelines"]
        }
    
    # Determine the current precipitation type
    def determine_precipitation_type(self, forecast, hourly_forecast):
        # Get the current period from the forecast
        current_period = forecast["properties"]["periods"][0]
        
        # Get the current hour from hourly forecast
        current_hour = hourly_forecast["properties"]["periods"][0]
        
        # Check for precipitation type in the forecast text
        forecast_text = current_period["detailedForecast"].lower()
        short_forecast = current_period["shortForecast"].lower()
        
        if "snow" in forecast_text or "snow" in short_forecast:
            return "snow"
        elif "rain" in forecast_text or "rain" in short_forecast or "shower" in forecast_text or "shower" in short_forecast:
            return "rain"
        # Fix: Check if probabilityOfPrecipitation exists and has a value before comparing
        elif "precipitation" in forecast_text or (
                "probabilityOfPrecipitation" in current_period and 
                current_period["probabilityOfPrecipitation"] and
                "value" in current_period["probabilityOfPrecipitation"] and
                current_period["probabilityOfPrecipitation"]["value"] and
                current_period["probabilityOfPrecipitation"]["value"] > 30
            ):
            # If specific type not mentioned but precipitation is likely
            if current_period["temperature"] < 36:
                return "snow"
            else:
                return "rain"
        else:
            return None
    
    # Get weather text from Tomorrow.io weather code
    def get_weather_text(self, code):
        weather_codes = {
            0: "Unknown",
            1000: "Clear, Sunny",
            1001: "Cloudy",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            3000: "Light Wind",
            3001: "Wind",
            3002: "Strong Wind",
            4000: "Drizzle",
            4001: "Rain",
            4200: "Light Rain",
            4201: "Heavy Rain",
            5000: "Snow",
            5001: "Flurries",
            5100: "Light Snow",
            5101: "Heavy Snow",
            6000: "Freezing Drizzle",
            6001: "Freezing Rain",
            6200: "Light Freezing Rain",
            6201: "Heavy Freezing Rain",
            7000: "Ice Pellets",
            7101: "Heavy Ice Pellets",
            7102: "Light Ice Pellets",
            8000: "Thunderstorm"
        }
        return weather_codes.get(code, f"Unknown ({code})")

# User Interface Agent - Handles user interaction and response formatting
class UIAgent:
    def __init__(self, data_agent):
        self.name = "UIAgent"
        self.data_agent = data_agent  # Reference to the data agent for communication
    
    # Method to receive messages from users for weather at a location
    def get_weather_for_location(self, latitude, longitude, source="nws"):
        st.session_state.logs.append(f"{self.name} requesting weather for lat:{latitude}, lon:{longitude} from {source}")
        
        # Send message to data agent
        message = {
            "type": "WEATHER_REQUEST",
            "data": {
                "latitude": latitude,
                "longitude": longitude,
                "source": source
            }
        }
        
        st.session_state.logs.append(f"{self.name} sending message to {self.data_agent.name}")
        response = self.data_agent.receive_message(message)
        
        # Process response
        if response["type"] == "WEATHER_RESPONSE":
            return self.format_weather_display(response["data"])
        else:
            return {
                "success": False,
                "message": response.get("data", "Unknown error")
            }
    
    # Method to receive messages from users for forecast at a location
    def get_forecast_for_location(self, latitude, longitude, source="nws"):
        st.session_state.logs.append(f"{self.name} requesting forecast for lat:{latitude}, lon:{longitude} from {source}")
        
        # Send message to data agent
        message = {
            "type": "FORECAST_REQUEST",
            "data": {
                "latitude": latitude,
                "longitude": longitude,
                "source": source
            }
        }
        
        st.session_state.logs.append(f"{self.name} sending message to {self.data_agent.name}")
        response = self.data_agent.receive_message(message)
        
        # Process response
        if response["type"] == "FORECAST_RESPONSE":
            return {
                "success": True,
                "data": response["data"]
            }
        else:
            return {
                "success": False,
                "message": response.get("data", "Unknown error")
            }
    
    # Format weather data for display
    def format_weather_display(self, weather_data):
        source = weather_data["source"]
        
        if source == "nws":
            # Fix: Handle potential None value in precipitation_prob
            precip_prob = weather_data['current']['probabilityOfPrecipitation']
            if precip_prob is None:
                precip_prob = 0
                
            return {
                "success": True,
                "data": weather_data,
                "display": {
                    "location": f"{weather_data['location']['city']}, {weather_data['location']['state']}",
                    "temperature": f"{weather_data['current']['temperature']}°{weather_data['current']['temperatureUnit']}",
                    "conditions": weather_data['current']['shortForecast'],
                    "wind": f"{weather_data['current']['windSpeed']} {weather_data['current']['windDirection']}",
                    "precipitation_type": weather_data['current']['precipitationType'],
                    "precipitation_prob": precip_prob,
                    "forecast": weather_data['current']['detailedForecast'],
                    "icon": weather_data['current']['icon'],
                    "alerts": []  # NWS alerts would be fetched separately
                }
            }
        elif source == "tomorrow":
            # Convert temperature from C to F for display
            temp_f = round(weather_data['current']['temperature'] * 9/5 + 32)
            feels_like_f = round(weather_data['current']['temperatureApparent'] * 9/5 + 32)
            
            # Determine precipitation type text - Fix: Add validation to prevent NoneType errors
            precip_type_index = weather_data['current']['precipitationType'] 
            precip_types = ['', 'Rain', 'Snow', 'Freezing Rain', 'Ice Pellets']
            
            # Fix: Check if precipitationType exists and is within valid range
            if precip_type_index is not None and 0 <= precip_type_index < len(precip_types):
                precip_type = precip_types[precip_type_index]
            else:
                precip_type = 'Unknown'
            
            # Fix: Check if precipitationProbability exists before comparing
            precip_prob = weather_data['current'].get('precipitationProbability', 0)
            
            return {
                "success": True,
                "data": weather_data,
                "display": {
                    "location": f"Lat: {weather_data['location']['coordinates']['lat']}, Lon: {weather_data['location']['coordinates']['lon']}",
                    "temperature": f"{temp_f}°F (Feels like: {feels_like_f}°F)",
                    "conditions": weather_data['current']['weatherText'],
                    "wind": f"{round(weather_data['current']['windSpeed'])} mph {self.get_wind_direction(weather_data['current']['windDirection'])}",
                    "precipitation_type": precip_type.lower() if precip_prob > 10 else None,
                    "precipitation_prob": precip_prob,
                    "humidity": weather_data['current'].get('humidity', 0),
                    "visibility": weather_data['current'].get('visibility', 0),
                    "uv_index": weather_data['current'].get('uvIndex', 0),
                    "alerts": weather_data.get('rawData', {}).get('alerts', [])
                }
            }
        else:
            return {
                "success": False,
                "message": f"Unknown source: {source}"
            }
    
    # Format forecast data for display
    def format_forecast_display(self, forecast_data, display_type="chart"):
        source = forecast_data["source"]
        
        if source == "nws":
            if display_type == "chart":
                return self.create_nws_forecast_chart(forecast_data)
            else:
                return {
                    "success": True,
                    "data": forecast_data,
                    "periods": forecast_data["forecastPeriods"]
                }
        elif source == "tomorrow":
            if display_type == "chart":
                return self.create_tomorrow_forecast_chart(forecast_data)
            else:
                return {
                    "success": True,
                    "data": forecast_data,
                    "timelines": forecast_data["timelines"]
                }
        else:
            return {
                "success": False,
                "message": f"Unknown source: {source}"
            }
    
    # Create forecast chart from NWS data
    def create_nws_forecast_chart(self, forecast_data):
        # Extract hourly forecasts for the chart
        hourly = forecast_data["hourlyForecasts"]
        
        # Create a DataFrame for the chart
        df = pd.DataFrame([
            {
                "Time": datetime.fromisoformat(period["time"].replace("Z", "+00:00")),
                "Temperature": period["temperature"],
                "Conditions": period["shortForecast"],
                "Precipitation": period["probabilityOfPrecipitation"]
            }
            for period in hourly
        ])
        
        # Create the chart
        fig = go.Figure()
        
        # Add temperature line
        fig.add_trace(go.Scatter(
            x=df["Time"],
            y=df["Temperature"],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF9500', width=3),
            marker=dict(size=8)
        ))
        
        # Add precipitation bars
        fig.add_trace(go.Bar(
            x=df["Time"],
            y=df["Precipitation"],
            name='Precipitation Chance (%)',
            marker_color='rgba(0, 120, 212, 0.6)',
            yaxis='y2'
        ))
        
        # Customize the layout - using proper title format
        fig.update_layout(
            title='24-Hour Forecast',
            xaxis=dict(title='Time'),
            yaxis=dict(
                title=dict(text='Temperature (°F)', font=dict(color='#FF9500')),
                tickfont=dict(color='#FF9500')
            ),
            yaxis2=dict(
                title=dict(text='Precipitation Chance (%)', font=dict(color='#0078D4')),
                tickfont=dict(color='#0078D4'),
                anchor='x',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            height=400
        )
        
        return {
            "success": True,
            "chart": fig,
            "data": forecast_data
        }
    
    # Create forecast chart from Tomorrow.io data
    def create_tomorrow_forecast_chart(self, forecast_data):
        # Extract hourly forecasts for the chart (first 24 hours)
        hourly = forecast_data["timelines"]["hourly"][:24]
        
        # Create a DataFrame for the chart
        df = pd.DataFrame([
            {
                "Time": datetime.fromisoformat(period["time"].replace("Z", "+00:00")),
                "Temperature": round(period["values"]["temperature"] * 9/5 + 32),  # Convert C to F
                "Conditions": self.data_agent.get_weather_text(period["values"]["weatherCode"]),
                "Precipitation": period["values"].get("precipitationProbability", 0)
            }
            for period in hourly
        ])
        
        # Create the chart
        fig = go.Figure()
        
        # Add temperature line
        fig.add_trace(go.Scatter(
            x=df["Time"],
            y=df["Temperature"],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF9500', width=3),
            marker=dict(size=8)
        ))
        
        # Add precipitation bars
        fig.add_trace(go.Bar(
            x=df["Time"],
            y=df["Precipitation"],
            name='Precipitation Chance (%)',
            marker_color='rgba(0, 120, 212, 0.6)',
            yaxis='y2'
        ))
        
        # Customize the layout - using proper title format
        fig.update_layout(
            title='24-Hour Forecast',
            xaxis=dict(title='Time'),
            yaxis=dict(
                title=dict(text='Temperature (°F)', font=dict(color='#FF9500')),
                tickfont=dict(color='#FF9500')
            ),
            yaxis2=dict(
                title=dict(text='Precipitation Chance (%)', font=dict(color='#0078D4')),
                tickfont=dict(color='#0078D4'),
                anchor='x',
                overlaying='y',
                side='right',
                range=[0, 100]
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            margin=dict(l=20, r=20, t=60, b=20),
            height=400
        )
        
        return {
            "success": True,
            "chart": fig,
            "data": forecast_data
        }
    
    # Get wind direction text from degrees
    def get_wind_direction(self, degrees):
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    # Get weather icon class based on conditions
    def get_weather_icon(self, condition, is_day=True):
        condition_lower = condition.lower()
        
        if "clear" in condition_lower or "sunny" in condition_lower:
            return "☀️" if is_day else "🌙"
        elif "cloud" in condition_lower or "overcast" in condition_lower:
            return "🌤️" if is_day else "☁️"
        elif "rain" in condition_lower or "shower" in condition_lower:
            return "🌧️"
        elif "snow" in condition_lower:
            return "❄️"
        elif "thunder" in condition_lower or "storm" in condition_lower:
            return "⚡"
        elif "fog" in condition_lower or "mist" in condition_lower:
            return "🌫️"
        elif "wind" in condition_lower:
            return "💨"
        else:
            return "☁️"

# Geocoding Agent - Helps with location searches
class GeocodingAgent:
    def __init__(self):
        self.name = "GeocodingAgent"
        self.cache = {}  # Cache for geocoding results
    
    # Search for a location
    def search_location(self, query):
        st.session_state.logs.append(f"{self.name} searching for location: {query}")
        
        # Check cache first
        if query in self.cache:
            st.session_state.logs.append(f"{self.name}: Using cached geocoding for {query}")
            return self.cache[query]
        
        try:
            # Use MapBox Geocoding API
            # For simplicity in this demo, we'll use a simpler approach with predefined locations
            result = self.mock_geocoding(query)
            
            # Cache the result
            self.cache[query] = result
            
            return result
        except Exception as e:
            st.session_state.logs.append(f"{self.name}: Error geocoding location: {str(e)}")
            return {
                "success": False,
                "message": f"Error geocoding location: {str(e)}"
            }
    
    # Mock geocoding for demonstration purposes
    def mock_geocoding(self, query):
        # List of predefined locations
        locations = {
            "new york": {
                "name": "New York, NY",
                "lat": 40.7128,
                "lon": -74.0060
            },
            "los angeles": {
                "name": "Los Angeles, CA",
                "lat": 34.0522,
                "lon": -118.2437
            },
            "chicago": {
                "name": "Chicago, IL",
                "lat": 41.8781,
                "lon": -87.6298
            },
            "houston": {
                "name": "Houston, TX",
                "lat": 29.7604,
                "lon": -95.3698
            },
            "miami": {
                "name": "Miami, FL",
                "lat": 25.7617,
                "lon": -80.1918
            },
            "seattle": {
                "name": "Seattle, WA",
                "lat": 47.6062,
                "lon": -122.3321
            },
            "san francisco": {
                "name": "San Francisco, CA",
                "lat": 37.7749,
                "lon": -122.4194
            },
            "denver": {
                "name": "Denver, CO",
                "lat": 39.7392,
                "lon": -104.9903
            },
            "truckee": {
                "name": "Truckee, CA",
                "lat": 39.3280,
                "lon": -120.1833
            },
            "donner lake": {
                "name": "Donner Lake, CA",
                "lat": 39.1395453,
                "lon": -120.1664349
            }
        }
        
        # Search for location
        query_lower = query.lower()
        
        # Direct match
        if query_lower in locations:
            return {
                "success": True,
                "results": [locations[query_lower]]
            }
        
        # Partial match
        matches = []
        for key, location in locations.items():
            if query_lower in key or query_lower in location["name"].lower():
                matches.append(location)
        
        if matches:
            return {
                "success": True,
                "results": matches
            }
        
        # No match
        return {
            "success": False,
            "message": f"No location found matching '{query}'",
            "results": []
        }

# Main Streamlit app
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Weather Assistant",
        page_icon="🌤️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check for API requests at the beginning
    is_api_request = handle_api_requests()
    
    # If this is an API request, display the response and stop
    if is_api_request:
        display_api_response()
    
    # Add custom CSS to make elements use full width
    st.markdown("""
    <style>
    .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 0rem;
    }
    .st-emotion-cache-x78sv8 {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .st-emotion-cache-z5fcl4 {
        padding-top: 0rem;
    }
    .stTable {
        width: 100% !important;
    }
    th, td {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🌤️ Weather Assistant")
    st.subheader("Multi-Agent System Demo")
    
    # Initialize session state for agents and data
    if "logs" not in st.session_state:
        st.session_state.logs = []
        
    if "weather_history" not in st.session_state:
        st.session_state.weather_history = []
        
    if "data_agent" not in st.session_state:
        st.session_state.data_agent = WeatherDataAgent()
        
    if "ui_agent" not in st.session_state:
        st.session_state.ui_agent = UIAgent(st.session_state.data_agent)
        
    if "geocoding_agent" not in st.session_state:
        st.session_state.geocoding_agent = GeocodingAgent()
    
    # Set default location (Donner Lake, California)
    if "current_location" not in st.session_state:
        st.session_state.current_location = {
            "name": "Donner Lake, CA",
            "lat": 39.1395453,
            "lon": -120.1664349
        }
    
    if "current_source" not in st.session_state:
        st.session_state.current_source = "nws"  # Default data source
    
    # Create sidebar for location search and options
    with st.sidebar:
        st.header("Location")
        
        # Location search
        with st.form(key="location_form"):
            search_query = st.text_input("Search for a location:", 
                                        placeholder="Enter city name or address")
            search_button = st.form_submit_button("Search")
            
            if search_button and search_query:
                # Search for location using geocoding agent
                search_result = st.session_state.geocoding_agent.search_location(search_query)
                
                if search_result["success"] and search_result["results"]:
                    if len(search_result["results"]) == 1:
                        # Single result - use it directly
                        st.session_state.current_location = search_result["results"][0]
                        st.success(f"Location set to {search_result['results'][0]['name']}")
                    else:
                        # Multiple results - let user choose
                        st.session_state.search_results = search_result["results"]
                        st.info(f"Found {len(search_result['results'])} matching locations. Please select one below.")
                else:
                    st.error(search_result.get("message", "Location not found"))
        
        # Display search results if available
        if "search_results" in st.session_state and st.session_state.search_results:
            st.subheader("Select a location:")
            
            for i, location in enumerate(st.session_state.search_results):
                if st.button(f"{location['name']}", key=f"loc_{i}"):
                    st.session_state.current_location = location
                    st.success(f"Location set to {location['name']}")
                    st.session_state.search_results = []  # Clear results after selection
                    st.rerun()  # Refresh to update weather data
        
        # Data source selection
        st.subheader("Data Source")
        source_options = ["National Weather Service", "Tomorrow.io"]
        source_keys = ["nws", "tomorrow"]
        selected_source = st.radio("Choose weather data source:", 
                               source_options, 
                               index=source_keys.index(st.session_state.current_source))
        
        # Update source if changed
        selected_source_key = source_keys[source_options.index(selected_source)]
        if st.session_state.current_source != selected_source_key:
            st.session_state.current_source = selected_source_key
            st.rerun()  # Refresh to update weather data
        
        # Debug toggle
        st.subheader("Debug")
        show_debug = st.checkbox("Show agent communication logs", value=False)
        
        # Add API documentation to sidebar
        st.divider()
        with st.expander("API Documentation", expanded=False):
            st.subheader("Weather API Endpoints")
            st.markdown("""
            This app provides API endpoints for other applications to access weather data.
            
            URL parameter-based API:
            
            - **Weather:** `/?request_type=weather&lat=LAT&lon=LON&source=SOURCE`
            - **Forecast:** `/?request_type=forecast&lat=LAT&lon=LON&source=SOURCE`
            - **Geocoding:** `/?request_type=geocoding&query=LOCATION`
            - **Health Check:** `/?request_type=healthcheck`
            """)
    
    # Create two equal columns for current weather and forecast
    col1, col2 = st.columns(2)
    
    with col1:
        # Current weather section
        st.header(f"Current Weather")
        st.caption(f"Location: {st.session_state.current_location['name']}")
        
        # Get weather information
        weather_result = st.session_state.ui_agent.get_weather_for_location(
            st.session_state.current_location["lat"],
            st.session_state.current_location["lon"],
            st.session_state.current_source
        )
        
        if weather_result["success"]:
            display = weather_result["display"]
            
            # Add CSS to make the container full width
            st.markdown("""
            <style>
            div[data-testid="stExpander"] {
                width: 100%;
            }
            div[data-testid="stHorizontalBlock"] {
                width: 100%;
            }
            div[data-testid="stVerticalBlock"] {
                width: 100%;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create a nice weather card with full width
            with st.container(border=True):
                current_time = datetime.now().strftime("%I:%M %p - %a, %b %d, %Y")
                st.caption(f"As of {current_time}")
                
                # Weather icon and temperature
                cols = st.columns([1, 3])
                with cols[0]:
                    # Weather icon (emoji for simplicity)
                    icon = st.session_state.ui_agent.get_weather_icon(
                        display["conditions"],
                        datetime.now().hour >= 6 and datetime.now().hour < 18
                    )
                    st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{icon}</h1>", unsafe_allow_html=True)
                
                with cols[1]:
                    # Temperature and conditions
                    st.markdown(f"<h2 style='margin-bottom: 0;'>{display['temperature']}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='font-size: 1.2rem; margin-top: 0;'>{display['conditions']}</p>", unsafe_allow_html=True)
                
                # Additional weather details
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Wind", display["wind"])
                
                with col2:
                    if "humidity" in display:
                        st.metric("Humidity", f"{display['humidity']}%")
                    elif "precipitation_prob" in display:
                        st.metric("Precipitation", f"{display['precipitation_prob']}%")
                
                with col3:
                    if display["precipitation_type"]:
                        st.metric("Precipitation Type", display["precipitation_type"].capitalize())
                    elif "uv_index" in display:
                        st.metric("UV Index", display["uv_index"])
                
                # Forecast text
                if "forecast" in display:
                    st.markdown("### Forecast")
                    st.write(display["forecast"])
                
                # Alerts (if any)
                if "alerts" in display and display["alerts"]:
                    st.markdown("### Weather Alerts")
                    for alert in display["alerts"]:
                        with st.warning():
                            st.markdown(f"**{alert.get('title', 'Weather Alert')}**")
                            st.write(alert.get("description", "No details available"))
        else:
            st.error(f"Error loading weather data: {weather_result.get('message', 'Unknown error')}")
    
    with col2:
        # Forecast section
        st.header("Forecast")
        
        # Get forecast information
        forecast_result = st.session_state.ui_agent.get_forecast_for_location(
            st.session_state.current_location["lat"],
            st.session_state.current_location["lon"],
            st.session_state.current_source
        )
        
        if forecast_result["success"]:
            # Display forecast chart
            chart_result = st.session_state.ui_agent.format_forecast_display(
                forecast_result["data"], 
                display_type="chart"
            )
            
            if chart_result["success"]:
                st.plotly_chart(chart_result["chart"], use_container_width=True)
            
            # Display forecast details as tables
            st.markdown("### 2-Day Forecast")
            
            if st.session_state.current_source == "nws":
                # Create a DataFrame for the NWS forecast periods (first 4)
                periods = forecast_result["data"]["forecastPeriods"][:4]
                
                # Create a DataFrame for the table
                forecast_df = pd.DataFrame([
                    {
                        "Period": period["name"],
                        "Temperature": f"{period['temperature']}°{period['temperatureUnit']}",
                        "Wind": f"{period['windSpeed']} {period['windDirection']}",
                        "Conditions": period["shortForecast"]
                    }
                    for period in periods
                ])
                
                # Display the table with full width
                st.dataframe(forecast_df, use_container_width=True)
                
            else:
                # Display Tomorrow.io daily forecast
                if "timelines" in forecast_result["data"] and "daily" in forecast_result["data"]["timelines"]:
                    daily_data = forecast_result["data"]["timelines"]["daily"][:4]  # Show up to 4 days
                    
                    # Create a DataFrame for the table
                    forecast_df = pd.DataFrame([
                        {
                            "Day": datetime.fromisoformat(day["time"].replace("Z", "+00:00")).strftime('%A, %b %d'),
                            "Temperature": f"{round(day['values']['temperatureMin'] * 9/5 + 32)}°F to {round(day['values']['temperatureMax'] * 9/5 + 32)}°F",
                            "Wind": f"{round(day['values'].get('windSpeedAvg', 0))} mph {st.session_state.ui_agent.get_wind_direction(day['values'].get('windDirectionAvg', 0))}",
                            "Conditions": st.session_state.data_agent.get_weather_text(day['values'].get('weatherCodeMax', 1001))
                        }
                        for day in daily_data
                    ])
                    
                    # Display the table with full width
                    st.dataframe(forecast_df, use_container_width=True)
        else:
            st.error(f"Error loading forecast data: {forecast_result.get('message', 'Unknown error')}")
    
    # Display communication logs if debug is enabled
    if show_debug:
        st.header("Agent Communication Logs")
        log_container = st.container(height=200)
        with log_container:
            for log in st.session_state.logs:
                st.text(log)
            
        if st.button("Clear Logs"):
            st.session_state.logs = []
            st.rerun()

if __name__ == "__main__":
    main()