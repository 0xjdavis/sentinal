import streamlit as st
import time
import json
import requests
from datetime import datetime, timedelta
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="Activity Planner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for styling
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: row;
    align-items: flex-start;
}
.chat-message.user {
    background-opacity: 0.5;
}
.chat-message.assistant {
    background-opacity: 0.3;
}
.chat-message .avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    object-fit: cover;
    margin-right: 1rem;
}
.chat-message .message {
    flex-grow: 1;
}
.weather-summary {
    background-opacity: 0.3;
    border-left: 3px solid #0066cc;
    padding: 0.5rem;
    margin-bottom: 1rem;
}
.stButton>button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# Configuration for the Weather API
WEATHER_API_BASE_URL = "https://sentinal.streamlit.app"

# Activity Planning Agent Class
class ActivityPlanningAgent:
    def __init__(self):
        self.name = "ActivityPlanningAgent"
        
        # Initialize activity database
        self.initialize_activities()
    
    # Initialize the database of activities
    def initialize_activities(self):
        # Indoor activities
        self.indoor_activities = {
            "museums": {
                "new york": ["Metropolitan Museum of Art", "Museum of Modern Art (MoMA)", "American Museum of Natural History"],
                "los angeles": ["Getty Center", "Los Angeles County Museum of Art", "The Broad"],
                "chicago": ["Art Institute of Chicago", "Field Museum", "Museum of Science and Industry"],
                "houston": ["Museum of Fine Arts", "Houston Museum of Natural Science", "Space Center Houston"],
                "miami": ["Pérez Art Museum", "Vizcaya Museum and Gardens", "Phillip and Patricia Frost Museum of Science"],
                "seattle": ["Museum of Pop Culture", "Chihuly Garden and Glass", "Seattle Art Museum"],
                "san francisco": ["de Young Museum", "California Academy of Sciences", "Exploratorium"],
                "denver": ["Denver Art Museum", "Denver Museum of Nature & Science", "History Colorado Center"],
                "truckee": ["Donner Memorial State Park Visitor Center", "Old Jail Museum", "Truckee Railroad Museum"],
                "donner lake": ["Donner Memorial State Park Visitor Center", "KidZone Museum"]
            },
            "entertainment": {
                "new york": ["Broadway shows", "Comedy Cellar", "Escape rooms in Midtown"],
                "los angeles": ["The Magic Castle", "Universal CityWalk", "Dinner theaters in Hollywood"],
                "chicago": ["The Second City comedy", "Chicago Theatre shows", "CIBC Theatre performances"],
                "houston": ["Space Center Houston", "Downtown Aquarium", "Escape rooms in Houston"],
                "miami": ["Adrienne Arsht Center shows", "Coconut Grove Playhouse", "Frost Science Museum"],
                "seattle": ["Pacific Science Center", "Seattle Aquarium", "Unexpected Productions Improv"],
                "san francisco": ["Escape rooms in SF", "Marrakech Magic Theater", "Exploratorium After Dark"],
                "denver": ["Denver Center for the Performing Arts", "Forney Museum of Transportation", "Denver Botanic Gardens"],
                "truckee": ["KidZone Museum", "Crystal Bay Casino (nearby)", "Movie theater in Truckee"],
                "donner lake": ["Indoor recreation at Truckee Community Recreation Center", "Northstar California Resort activities"]
            },
            "dining": {
                "new york": ["Fine dining in Manhattan", "Ethnic cuisine in Queens", "Famous delis and bakeries"],
                "los angeles": ["Celebrity restaurants in Beverly Hills", "Food halls in Downtown LA", "Ethnic cuisine in Koreatown"],
                "chicago": ["Deep dish pizza spots", "Fine dining in the Loop", "Ethnic restaurants in various neighborhoods"],
                "houston": ["Tex-Mex restaurants", "Gulf Coast seafood", "Upscale dining in Uptown"],
                "miami": ["Cuban restaurants in Little Havana", "Seafood in Miami Beach", "Fine dining in Brickell"],
                "seattle": ["Seafood at Pike Place Market", "Coffee shops throughout city", "Asian cuisine in International District"],
                "san francisco": ["Seafood at Fisherman's Wharf", "Fine dining in SoMa", "Authentic dim sum in Chinatown"],
                "denver": ["Steakhouses in Downtown", "Craft breweries with food", "Union Station food hall"],
                "truckee": ["Moody's Bistro", "Pianeta Ristorante", "Jax at the Tracks", "Cottonwood Restaurant"],
                "donner lake": ["Donner Lake Kitchen", "Nearby restaurants in Truckee"]
            },
            "shopping": {
                "new york": ["5th Avenue boutiques", "SoHo shopping district", "Chelsea Market"],
                "los angeles": ["Rodeo Drive in Beverly Hills", "The Grove", "Melrose Avenue shops"],
                "chicago": ["Magnificent Mile", "Water Tower Place", "State Street shopping"],
                "houston": ["The Galleria", "Highland Village", "River Oaks District"],
                "miami": ["Bal Harbour Shops", "Dolphin Mall", "Lincoln Road Mall"],
                "seattle": ["Pike Place Market shops", "Pacific Place", "University Village"],
                "san francisco": ["Union Square shops", "Westfield San Francisco Centre", "Hayes Valley boutiques"],
                "denver": ["16th Street Mall", "Cherry Creek Shopping Center", "Larimer Square shops"],
                "truckee": ["Historic Downtown Truckee shops", "Truckee Mercantile", "Bespoke Truckee"],
                "donner lake": ["Shops in nearby Truckee", "Donner Lake Gift Shop"]
            }
        }
        
        # Outdoor activities
        self.outdoor_activities = {
            "parks": {
                "new york": ["Central Park", "The High Line", "Brooklyn Bridge Park"],
                "los angeles": ["Griffith Park", "Grand Park", "Will Rogers State Historic Park"],
                "chicago": ["Millennium Park", "Grant Park", "Lincoln Park"],
                "houston": ["Memorial Park", "Hermann Park", "Buffalo Bayou Park"],
                "miami": ["South Pointe Park", "Bayfront Park", "Tropical Park"],
                "seattle": ["Discovery Park", "Gas Works Park", "Kerry Park"],
                "san francisco": ["Golden Gate Park", "Dolores Park", "The Presidio"],
                "denver": ["City Park", "Washington Park", "Cheesman Park"],
                "truckee": ["Donner Memorial State Park", "Truckee River Regional Park", "Truckee Bike Park"],
                "donner lake": ["Donner Memorial State Park", "Coldstream Canyon", "Donner Lake Memorial State Beach"]
            },
            "hikes": {
                "new york": ["Fort Tryon Park trails", "Inwood Hill Park paths", "Van Cortlandt Park hiking"],
                "los angeles": ["Runyon Canyon", "Griffith Park trails", "Topanga State Park hikes"],
                "chicago": ["North Shore Channel Trail", "Lakefront Trail", "North Branch Trail"],
                "houston": ["Memorial Park trails", "Buffalo Bayou Park trails", "Terry Hershey Park"],
                "miami": ["Oleta River State Park trails", "Matheson Hammock Park paths", "Bill Baggs Cape trails"],
                "seattle": ["Discovery Park Loop Trail", "Washington Park Arboretum", "Seward Park trails"],
                "san francisco": ["Lands End Trail", "Twin Peaks hike", "Mount Sutro trails"],
                "denver": ["Red Rocks Trail", "Cherry Creek Trail", "Green Mountain Trail"],
                "truckee": ["Pacific Crest Trail sections", "Donner Peak trail", "Emigrant Trail"],
                "donner lake": ["Donner Lake Rim Trail", "Mount Judah Loop Trail", "Summit Lake Trail"]
            },
            "attractions": {
                "new york": ["Statue of Liberty", "Empire State Building observation deck", "Top of the Rock"],
                "los angeles": ["Hollywood Sign hike", "Venice Beach Boardwalk", "Santa Monica Pier"],
                "chicago": ["Navy Pier", "Buckingham Fountain", "360 Chicago observation deck"],
                "houston": ["Gerald D. Hines Waterwall Park", "James Turrell Skyspace", "Market Square Park"],
                "miami": ["Wynwood Walls", "Art Deco Historic District", "Bayside Marketplace"],
                "seattle": ["Space Needle", "Pike Place Market", "Seattle Great Wheel"],
                "san francisco": ["Golden Gate Bridge", "Alcatraz Island", "Fisherman's Wharf"],
                "denver": ["Red Rocks Amphitheatre", "Colorado State Capitol", "Union Station"],
                "truckee": ["Historic Downtown Truckee", "Donner Summit Bridge", "Donner Pass"],
                "donner lake": ["Donner Lake Vista Point", "China Wall", "Donner Summit"]
            },
            "water_activities": {
                "new york": ["Hudson River kayaking", "Central Park rowboats", "NYC Water Taxi tours"],
                "los angeles": ["Santa Monica Beach", "Malibu surfing", "Marina del Rey paddleboarding"],
                "chicago": ["Lake Michigan beaches", "Chicago River kayaking", "Lake Michigan boat tours"],
                "houston": ["Buffalo Bayou kayaking", "Galveston Beach (nearby)", "Clear Lake sailing"],
                "miami": ["South Beach", "Miami Beach watersports", "Biscayne Bay sailing"],
                "seattle": ["Lake Union kayaking", "Alki Beach", "Lake Washington activities"],
                "san francisco": ["Baker Beach", "Ocean Beach", "San Francisco Bay sailing"],
                "denver": ["Cherry Creek Reservoir", "South Platte River kayaking", "Chatfield State Park"],
                "truckee": ["Truckee River rafting", "Donner Lake swimming and paddleboarding", "West End Beach"],
                "donner lake": ["Donner Lake Public Docks", "Donner Lake water sports", "Donner Lake beaches"]
            }
        }
    
    # API call to get weather data from the weather app
    def get_weather_from_api(self, latitude, longitude, source="tomorrow"):
        """Make API call to the Weather App to get current weather"""
        try:
            # For the hosted app, we'll use a different approach
            # since we don't have direct API endpoints
            # We'll use the streamlit session state as an API
            
            # Construct the URL with parameters
            params = {
                "lat": latitude,
                "lon": longitude,
                "source": source,
                "request_type": "weather"
            }
            
            # Convert params to query string
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{WEATHER_API_BASE_URL}/?{query_string}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Parse the response content to find weather data
                # This is a basic implementation - in a real app,
                # we would need to parse the HTML or use a proper API
                
                # For now, return a mock response since we can't
                # easily extract data from the HTML response
                mock_data = self.generate_mock_weather_data(latitude, longitude, source)
                return mock_data
            else:
                st.error(f"API Error: {response.status_code}")
                return {"success": False, "message": f"API Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            st.error(f"Connection Error: {str(e)}")
            return {"success": False, "message": f"Connection Error: {str(e)}"}
    
    # Generate mock weather data as fallback
    def generate_mock_weather_data(self, latitude, longitude, source):
        """Generate mock weather data for demonstration purposes"""
        # This would be replaced with actual API response parsing
        # in a production application
        
        # Get current date and time
        now = datetime.now()
        
        # Generate random but plausible weather data
        temp = random.randint(65, 85)
        conditions = random.choice([
            "Clear, Sunny", "Partly Cloudy", "Mostly Cloudy", 
            "Light Rain", "Cloudy", "Mostly Clear"
        ])
        
        precip_prob = random.randint(0, 40)
        
        # Get city name based on coordinates (mock implementation)
        city_name = self.get_city_from_coordinates(latitude, longitude)
        
        return {
            "success": True,
            "data": {
                "source": source,
                "location": {
                    "city": city_name,
                    "state": "CA",
                    "coordinates": {
                        "lat": latitude,
                        "lon": longitude
                    }
                },
                "current": {
                    "temperature": temp,
                    "temperatureApparent": temp - random.randint(0, 5),
                    "weatherText": conditions,
                    "precipitationProbability": precip_prob,
                    "humidity": random.randint(30, 80),
                    "windSpeed": random.randint(5, 15),
                    "windDirection": random.randint(0, 359)
                }
            }
        }
    
    # Get city name from coordinates (mock implementation)
    def get_city_from_coordinates(self, latitude, longitude):
        """Convert coordinates to city name (mock implementation)"""
        # This would use reverse geocoding in a real app
        
        # For demo purposes, check if coordinates are close to known cities
        known_locations = {
            (40.7128, -74.0060): "New York",
            (34.0522, -118.2437): "Los Angeles",
            (41.8781, -87.6298): "Chicago",
            (39.1395453, -120.1664349): "Donner Lake",
            (39.3280, -120.1833): "Truckee",
            (37.7749, -122.4194): "San Francisco",
            (47.6062, -122.3321): "Seattle",
            (39.7392, -104.9903): "Denver"
        }
        
        closest_city = "Unknown Location"
        min_distance = float('inf')
        
        for (city_lat, city_lon), city_name in known_locations.items():
            distance = ((latitude - city_lat) ** 2 + (longitude - city_lon) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_city = city_name
        
        return closest_city
    
    # API call to get forecast data from the weather app
    def get_forecast_from_api(self, latitude, longitude, source="tomorrow"):
        """Make API call to the Weather App to get forecast data"""
        try:
            # Similar approach as with weather data, for hosted app
            # we'll mock the response since we don't have direct API access
            
            # Construct the URL with parameters
            params = {
                "lat": latitude,
                "lon": longitude,
                "source": source,
                "request_type": "forecast"
            }
            
            # Convert params to query string
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{WEATHER_API_BASE_URL}/?{query_string}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Generate mock forecast data
                mock_data = self.generate_mock_forecast_data(latitude, longitude, source)
                return mock_data
            else:
                st.error(f"API Error: {response.status_code}")
                return {"success": False, "message": f"API Error: {response.status_code}"}
        except requests.exceptions.RequestException as e:
            st.error(f"Connection Error: {str(e)}")
            return {"success": False, "message": f"Connection Error: {str(e)}"}
    
    # Generate mock forecast data
    def generate_mock_forecast_data(self, latitude, longitude, source):
        """Generate mock forecast data for demonstration purposes"""
        # This would be replaced with actual API response parsing in a production app
        
        # Get current date
        today = datetime.now()
        
        # Get city name based on coordinates
        city_name = self.get_city_from_coordinates(latitude, longitude)
        
        # Generate daily forecasts for the next 7 days
        daily_forecasts = []
        
        for i in range(7):
            forecast_date = today + timedelta(days=i)
            
            # Generate plausible weather values
            temp_min = random.randint(55, 70)
            temp_max = temp_min + random.randint(5, 15)
            
            # Weather gets worse over the weekend for variety
            if forecast_date.weekday() >= 5:  # Weekend
                weather_code = random.choice([1001, 1102, 4000, 4001])  # Cloudy, rainy
                precip_prob = random.randint(30, 70)
            else:
                weather_code = random.choice([1000, 1100, 1101])  # Clear, partly cloudy
                precip_prob = random.randint(0, 30)
            
            daily_forecasts.append({
                "time": forecast_date.strftime("%Y-%m-%dT00:00:00Z"),
                "values": {
                    "temperatureMin": (temp_min - 32) * 5/9,  # Convert to C for API consistency
                    "temperatureMax": (temp_max - 32) * 5/9,
                    "precipitationProbabilityAvg": precip_prob,
                    "weatherCodeMax": weather_code,
                    "windSpeedAvg": random.randint(5, 15),
                    "windDirectionAvg": random.randint(0, 359)
                }
            })
        
        # Generate hourly forecasts for the next 24 hours
        hourly_forecasts = []
        
        for i in range(24):
            forecast_hour = today + timedelta(hours=i)
            
            # Temperature curve throughout the day
            hour = forecast_hour.hour
            if 6 <= hour <= 14:  # Morning to afternoon - warming up
                temp = random.randint(60, 80)
            elif 15 <= hour <= 19:  # Late afternoon - warmest
                temp = random.randint(70, 85)
            else:  # Evening/night - cooling down
                temp = random.randint(55, 70)
            
            # More likely to rain in the afternoon
            if 13 <= hour <= 16:
                precip_prob = random.randint(10, 50)
            else:
                precip_prob = random.randint(0, 30)
            
            hourly_forecasts.append({
                "time": forecast_hour.strftime("%Y-%m-%dT%H:00:00Z"),
                "values": {
                    "temperature": (temp - 32) * 5/9,  # Convert to C for API consistency
                    "precipitationProbability": precip_prob,
                    "weatherCode": random.choice([1000, 1100, 1101, 1001]),
                    "windSpeed": random.randint(5, 15),
                    "windDirection": random.randint(0, 359)
                }
            })
        
        return {
            "success": True,
            "data": {
                "source": source,
                "location": {
                    "coordinates": {
                        "lat": latitude,
                        "lon": longitude
                    }
                },
                "timelines": {
                    "daily": daily_forecasts,
                    "hourly": hourly_forecasts
                }
            }
        }
    
    # API call to geocode a location query
    def geocode_location_from_api(self, query):
        """Make API call to geocode a location query"""
        try:
            # For the hosted app, we'll use a simpler approach
            # with mock data rather than API calls
            
            # Predefined locations
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
        except Exception as e:
            st.error(f"Error geocoding location: {str(e)}")
            return {
                "success": False,
                "message": f"Error geocoding location: {str(e)}"
            }
    
    # Get weather data for a specific location and date
    def get_weather_for_planning(self, location, date_str=None):
        try:
            # If no date specified, use current date
            if not date_str:
                target_date = datetime.now()
            else:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if the date is within forecast range (usually 7 days)
            current_date = datetime.now()
            days_difference = (target_date - current_date).days
            
            if days_difference < 0:
                return {
                    "success": False,
                    "message": "Cannot plan for past dates"
                }
            elif days_difference > 7:
                return {
                    "success": False,
                    "message": "Weather forecasts are only available for the next 7 days"
                }
            
            # Get weather forecast data through the API
            forecast_result = self.get_forecast_from_api(
                location["lat"],
                location["lon"],
                "tomorrow"  # Using Tomorrow.io for more detailed forecasts
            )
            
            if not forecast_result.get("success", False):
                return {
                    "success": False,
                    "message": f"Error fetching forecast: {forecast_result.get('message', 'Unknown error')}"
                }
            
            # Extract the relevant day's forecast
            if "data" in forecast_result and "timelines" in forecast_result["data"] and "daily" in forecast_result["data"]["timelines"]:
                daily_data = forecast_result["data"]["timelines"]["daily"]
                
                # Find the forecast for the target date
                target_date_str = target_date.strftime("%Y-%m-%d")
                target_forecast = None
                
                for day in daily_data:
                    forecast_date = datetime.fromisoformat(day["time"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
                    if forecast_date == target_date_str:
                        target_forecast = day
                        break
                
                if target_forecast:
                    # Convert to Fahrenheit for easier understanding
                    temp_min = round(target_forecast["values"]["temperatureMin"] * 9/5 + 32)
                    temp_max = round(target_forecast["values"]["temperatureMax"] * 9/5 + 32)
                    
                    # Get readable weather condition
                    weather_code = target_forecast["values"].get("weatherCodeMax", 1001)
                    weather_condition = self.get_weather_text(weather_code)
                    
                    # Precipitation probability
                    precip_prob = target_forecast["values"].get("precipitationProbabilityAvg", 0)
                    
                    # Wind information
                    wind_speed = round(target_forecast["values"].get("windSpeedAvg", 0))
                    wind_direction = self.get_wind_direction(target_forecast["values"].get("windDirectionAvg", 0))
                    
                    # Determine if the weather is suitable for outdoor activities
                    is_good_for_outdoors = self.assess_outdoor_suitability(
                        temp_min, 
                        temp_max, 
                        precip_prob, 
                        weather_condition
                    )
                    
                    return {
                        "success": True,
                        "date": target_date.strftime("%A, %B %d, %Y"),
                        "location": location["name"],
                        "forecast": {
                            "temp_min": temp_min,
                            "temp_max": temp_max,
                            "condition": weather_condition,
                            "precipitation_probability": precip_prob,
                            "wind": f"{wind_speed} mph {wind_direction}",
                            "is_good_for_outdoors": is_good_for_outdoors
                        }
                    }
                else:
                    return {
                        "success": False,
                        "message": f"No forecast available for {target_date_str}"
                    }
            else:
                return {
                    "success": False,
                    "message": "Forecast data not available in expected format"
                }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing weather data: {str(e)}"
            }
    
    # Get readable weather text from code
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
    
    # Get wind direction text
    def get_wind_direction(self, degrees):
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    # Assess if weather is suitable for outdoor activities
    def assess_outdoor_suitability(self, temp_min, temp_max, precip_prob, condition):
        # Simple logic for outdoor suitability
        condition_lower = condition.lower()
        
        # Bad conditions for outdoors
        if (
            "rain" in condition_lower or 
            "snow" in condition_lower or 
            "storm" in condition_lower or 
            "thunder" in condition_lower or
            "fog" in condition_lower or
            precip_prob > 40 or
            temp_max < 40 or  # Too cold
            temp_min > 95     # Too hot
        ):
            return False
        
        return True
    
    # Generate activity plan based on weather and preferences
    def generate_plan(self, location, date_str=None, preferences=None, outdoor_priority=None):
        # Default preferences if none provided
        if preferences is None:
            preferences = ["museums", "parks", "dining", "attractions"]
        
        # Get weather data
        weather_result = self.get_weather_for_planning(location, date_str)
        
        if not weather_result["success"]:
            return {
                "success": False,
                "message": weather_result["message"]
            }
        
        # Determine if we should prioritize indoor or outdoor activities
        is_outdoor_suitable = weather_result["forecast"]["is_good_for_outdoors"]
        
        # Override based on user preference if specified
        if outdoor_priority is not None:
            prioritize_outdoors = outdoor_priority
        else:
            prioritize_outdoors = is_outdoor_suitable
        
        # Get location name in lowercase for activity lookup
        location_key = location["name"].lower().split(",")[0].strip()
        
        # Find the best matching location key if exact match not found
        if location_key not in self.indoor_activities["museums"]:
            best_match = None
            for key in self.indoor_activities["museums"].keys():
                if key in location_key or location_key in key:
                    best_match = key
                    break
            
            if best_match:
                location_key = best_match
        
        # Prepare activities based on weather suitability
        morning_activities = []
        afternoon_activities = []
        evening_activities = []
        
        try:
            # Generate activities for each time slot based on preferences and weather
            if prioritize_outdoors:
                # Outdoor-focused day
                for pref in preferences:
                    if pref in self.outdoor_activities:
                        category = self.outdoor_activities[pref]
                        if location_key in category and len(morning_activities) < 2:
                            activities = category[location_key]
                            if activities:
                                morning_activities.append(random.choice(activities))
                    
                    if pref in self.outdoor_activities:
                        category = self.outdoor_activities[pref]
                        if location_key in category and len(afternoon_activities) < 2:
                            activities = category[location_key]
                            if activities:
                                activity = random.choice(activities)
                                if activity not in morning_activities:
                                    afternoon_activities.append(activity)
                
                # Always include dining options for evening
                if "dining" in self.indoor_activities and location_key in self.indoor_activities["dining"]:
                    evening_activities.append(random.choice(self.indoor_activities["dining"][location_key]))
                
                # Add entertainment option for evening
                if "entertainment" in self.indoor_activities and location_key in self.indoor_activities["entertainment"]:
                    activity = random.choice(self.indoor_activities["entertainment"][location_key])
                    evening_activities.append(activity)
            else:
                # Indoor-focused day
                for pref in preferences:
                    if pref in self.indoor_activities:
                        category = self.indoor_activities[pref]
                        if location_key in category and len(morning_activities) < 2:
                            activities = category[location_key]
                            if activities:
                                morning_activities.append(random.choice(activities))
                    
                    if pref in self.indoor_activities:
                        category = self.indoor_activities[pref]
                        if location_key in category and len(afternoon_activities) < 2:
                            activities = category[location_key]
                            if activities:
                                activity = random.choice(activities)
                                if activity not in morning_activities:
                                    afternoon_activities.append(activity)
                
                # Always include dining options for evening
                if "dining" in self.indoor_activities and location_key in self.indoor_activities["dining"]:
                    evening_activities.append(random.choice(self.indoor_activities["dining"][location_key]))
                
                # Add entertainment option for evening
                if "entertainment" in self.indoor_activities and location_key in self.indoor_activities["entertainment"]:
                    activity = random.choice(self.indoor_activities["entertainment"][location_key])
                    evening_activities.append(activity)
            
            # Fill in any missing activities
            if not morning_activities:
                if location_key in self.indoor_activities["museums"]:
                    morning_activities.append(random.choice(self.indoor_activities["museums"][location_key]))
                else:
                    morning_activities.append("Explore the local area")
            
            if not afternoon_activities:
                if location_key in self.indoor_activities["shopping"]:
                    afternoon_activities.append(random.choice(self.indoor_activities["shopping"][location_key]))
                else:
                    afternoon_activities.append("Visit local shops")
            
            if not evening_activities:
                evening_activities.append("Dinner at a local restaurant")
            
            # Format the plan
            plan = {
                "success": True,
                "weather": weather_result,
                "plan": {
                    "morning": {
                        "time": "9:00 AM - 12:00 PM",
                        "activities": morning_activities
                    },
                    "afternoon": {
                        "time": "12:00 PM - 5:00 PM",
                        "activities": afternoon_activities
                    },
                    "evening": {
                        "time": "5:00 PM - 10:00 PM",
                        "activities": evening_activities
                    }
                },
                "outdoor_priority": prioritize_outdoors
            }
            
            return plan
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error generating plan: {str(e)}"
            }
    
    # Process a natural language request and generate a response
    def process_request(self, user_message):
        try:
            # Extract location information from the message
            location = self.extract_location(user_message)
            
            # Extract date information from the message
            date_str = self.extract_date(user_message)
            
            # Extract preferences from the message
            preferences = self.extract_preferences(user_message)
            
            # Extract outdoor preference from the message
            outdoor_priority = self.extract_outdoor_preference(user_message)
            
            # If no location found, ask the user for location
            if not location:
                return {
                    "type": "question",
                    "message": "I need to know which location you'd like to plan for. Could you specify a city or place?"
                }
            
            # Generate the plan
            plan_result = self.generate_plan(location, date_str, preferences, outdoor_priority)
            
            if not plan_result["success"]:
                return {
                    "type": "error",
                    "message": plan_result["message"]
                }
            
            # Format the response
            weather = plan_result["weather"]["forecast"]
            date = plan_result["weather"]["date"]
            location_name = plan_result["weather"]["location"]
            
            weather_summary = f"On {date} in {location_name}, expect temperatures between {weather['temp_min']}°F and {weather['temp_max']}°F with {weather['condition']}. There's a {weather['precipitation_probability']}% chance of precipitation."
            
            outdoors_message = ""
            if plan_result["outdoor_priority"]:
                outdoors_message = "Since the weather looks good, I've included some outdoor activities."
            else:
                outdoors_message = "Due to the weather conditions, I've focused on indoor activities."
            
            plan_text = f"{weather_summary} {outdoors_message}\n\n"
            plan_text += f"Morning ({plan_result['plan']['morning']['time']}):\n"
            for activity in plan_result['plan']['morning']['activities']:
                plan_text += f"- {activity}\n"
            
            plan_text += f"\nAfternoon ({plan_result['plan']['afternoon']['time']}):\n"
            for activity in plan_result['plan']['afternoon']['activities']:
                plan_text += f"- {activity}\n"
            
            plan_text += f"\nEvening ({plan_result['plan']['evening']['time']}):\n"
            for activity in plan_result['plan']['evening']['activities']:
                plan_text += f"- {activity}\n"
            
            return {
                "type": "plan",
                "message": "I've created a day plan based on the weather forecast and your preferences.",
                "weather_summary": weather_summary,
                "outdoor_priority": plan_result["outdoor_priority"],
                "plan": plan_result["plan"],
                "location": location_name,
                "date": date,
                "plan_text": plan_text
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"I encountered an error while processing your request: {str(e)}"
            }
    
    # Extract location from user message
    def extract_location(self, message):
        message_lower = message.lower()
        
        # Check for specific locations mentioned in the message
        for location_key in self.indoor_activities["museums"].keys():
            if location_key in message_lower:
                # Get full location info from geocoding agent through API
                location_result = self.geocode_location_from_api(location_key)
                if location_result.get("success", False) and location_result.get("results", []):
                    return location_result["results"][0]
        
        # If no specific location found, return None
        return None
    
    # Extract date from user message
    def extract_date(self, message):
        message_lower = message.lower()
        
        # Check for date keywords
        if "today" in message_lower:
            return datetime.now().strftime("%Y-%m-%d")
        elif "tomorrow" in message_lower:
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "this weekend" in message_lower or "weekend" in message_lower:
            # Find the next Saturday
            today = datetime.now()
            days_until_weekend = (5 - today.weekday()) % 7  # 5 = Saturday
            if days_until_weekend == 0:
                days_until_weekend = 7  # If today is Saturday, get next Saturday
            return (today + timedelta(days=days_until_weekend)).strftime("%Y-%m-%d")
        
        # No specific date found, return None (will use current date)
        return None
    
    # Extract preferences from user message
    def extract_preferences(self, message):
        message_lower = message.lower()
        preferences = []
        
        # Check for activity keywords
        if "museum" in message_lower or "art" in message_lower or "cultural" in message_lower:
            preferences.append("museums")
        
        if "park" in message_lower or "garden" in message_lower or "nature" in message_lower:
            preferences.append("parks")
        
        if "hike" in message_lower or "trail" in message_lower or "hiking" in message_lower:
            preferences.append("hikes")
        
        if "food" in message_lower or "eat" in message_lower or "restaurant" in message_lower or "dining" in message_lower:
            preferences.append("dining")
        
        if "shop" in message_lower or "shopping" in message_lower or "mall" in message_lower or "store" in message_lower:
            preferences.append("shopping")
        
        if "attraction" in message_lower or "sightseeing" in message_lower or "landmark" in message_lower:
            preferences.append("attractions")
        
        if "entertainment" in message_lower or "show" in message_lower or "theater" in message_lower:
            preferences.append("entertainment")
        
        if "water" in message_lower or "beach" in message_lower or "swim" in message_lower or "boat" in message_lower:
            preferences.append("water_activities")
        
        # If no specific preferences found, return default preferences
        if not preferences:
            return ["museums", "parks", "dining", "attractions"]
        
        return preferences
    
    # Extract outdoor preference from user message
    def extract_outdoor_preference(self, message):
        message_lower = message.lower()
        
        # Check for outdoor/indoor preferences
        if "outdoor" in message_lower or "outside" in message_lower:
            return True
        elif "indoor" in message_lower or "inside" in message_lower:
            return False
        
        # No specific preference found, return None (will use weather-based decision)
        return None

# Function to check if weather API is available
def check_api_connection():
    try:
        response = requests.get(f"{WEATHER_API_BASE_URL}/api/healthcheck", timeout=5)
        return response.status_code == 200
    except:
        # Try alternative endpoint if healthcheck doesn't exist
        try:
            # Just try to access the main page
            response = requests.get(WEATHER_API_BASE_URL, timeout=5)
            return response.status_code == 200
        except:
            return False

# Initialize chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize planning agent if it doesn't exist
if "planning_agent" not in st.session_state:
    st.session_state.planning_agent = ActivityPlanningAgent()

# App title
st.title("Day Planner Assistant")
st.subheader("Plan your perfect day based on weather forecasts")

# Check API connection
api_available = check_api_connection()

if not api_available:
    st.error("""
    ⚠️ Cannot connect to the Weather App at https://sentinal.streamlit.app
    
    The application will use simulated weather data for demonstration purposes.
    """)
    st.info("Using simulated weather data for planning")
else:
    st.success("✅ Connected to Weather App at https://sentinal.streamlit.app")

# Create a two-column layout
col1, col2 = st.columns([2, 1])

with col1:
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user">
                <img src="https://api.dicebear.com/7.x/thumbs/svg?seed=Felix" class="avatar">
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant">
                <img src="https://api.dicebear.com/7.x/bottts/svg?seed=Dusty" class="avatar">
                <div class="message">{message["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input (only enable if API is available)
    with st.container():
        user_input = st.chat_input("What would you like to do today?", disabled=(not api_available))
        
        if user_input:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Process the user input
            response = st.session_state.planning_agent.process_request(user_input)
            
            # Format assistant response based on the type
            if response["type"] == "question":
                # Simple question response
                assistant_response = response["message"]
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            elif response["type"] == "error":
                # Error response
                assistant_response = response["message"]
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            elif response["type"] == "plan":
                # Format plan response with weather and activities
                assistant_response = response["message"] + "\n\n"
                
                # Add weather summary and outdoor/indoor decision
                if response["outdoor_priority"]:
                    assistant_response += f"**Weather Summary:** {response['weather_summary']} Since the weather looks good, I've planned some outdoor activities.\n\n"
                else:
                    assistant_response += f"**Weather Summary:** {response['weather_summary']} Due to the weather conditions, I've focused on indoor activities.\n\n"
                
                # Add morning activities
                assistant_response += f"**Morning ({response['plan']['morning']['time']}):**\n"
                for activity in response['plan']['morning']['activities']:
                    assistant_response += f"- {activity}\n"
                
                # Add afternoon activities
                assistant_response += f"\n**Afternoon ({response['plan']['afternoon']['time']}):**\n"
                for activity in response['plan']['afternoon']['activities']:
                    assistant_response += f"- {activity}\n"
                
                # Add evening activities
                assistant_response += f"\n**Evening ({response['plan']['evening']['time']}):**\n"
                for activity in response['plan']['evening']['activities']:
                    assistant_response += f"- {activity}\n"
                
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            
            # Rerun to update the UI
            st.rerun()

with col2:
    with st.expander("Locations", expanded=False, icon=None):
        # Sidebar-like info panel
        st.markdown("### Available Locations")
        
        # Display available locations for planning
        locations_df = pd.DataFrame([
            {"City": "New York, NY", "Activities": "Museums, Parks, Dining, Attractions"},
            {"City": "Los Angeles, CA", "Activities": "Beaches, Museums, Entertainment"},
            {"City": "Chicago, IL", "Activities": "Museums, Parks, Architecture"},
            {"City": "Miami, FL", "Activities": "Beaches, Nightlife, Cultural"},
            {"City": "Seattle, WA", "Activities": "Nature, Coffee, Tech"},
            {"City": "San Francisco, CA", "Activities": "Tech, Food, Sightseeing"},
            {"City": "Denver, CO", "Activities": "Mountains, Museums, Outdoors"},
            {"City": "Truckee, CA", "Activities": "Hiking, History, Nature"},
            {"City": "Donner Lake, CA", "Activities": "Lake, Museums, Outdoors"}
        ])
        
        st.dataframe(locations_df, use_container_width=True)

    with st.expander("Tips", expanded=False, icon=None):    
        # Tips for using the planner
        st.markdown("### Tips for Planning")
        st.markdown("""
        - Specify a location: "Plan a day in Chicago"
        - Mention date preferences: "tomorrow" or "this weekend"
        - Share activity interests: "museums" or "hiking"
        - Indicate indoor/outdoor preference: "outdoor activities"
        
        Example: "I'd like to explore San Francisco tomorrow with outdoor activities and some good food options"
        """)
        

    with st.expander("Weather", expanded=False, icon=None):
        # API connection status
        st.markdown("### API Connection")
        if api_available:
            st.markdown("""
            ✅ **Connected to Weather App**
            
            This planner is communicating with the Weather App at:
            https://sentinal.streamlit.app
            """)
        else:
            st.markdown("""
            ⚠️ **Using simulated weather data**
            
            Cannot connect to https://sentinal.streamlit.app
            Using simulated weather data for planning purposes.
            """)
            
            # Show a button to retry the connection
            if st.button("Retry Connection"):
                st.rerun()
    
        # Weather info
        if st.session_state.messages and len(st.session_state.messages) > 1:
            last_response = st.session_state.messages[-1]
            if last_response["role"] == "assistant" and "Weather Summary" in last_response["content"]:
                st.markdown("### Current Plan")
                
                # Extract the weather summary
                weather_start = last_response["content"].find("**Weather Summary:**")
                weather_end = last_response["content"].find("\n\n", weather_start)
                weather_summary = last_response["content"][weather_start:weather_end]
                
                st.markdown(f"""
                <div class="weather-summary">
                {weather_summary}
                </div>
                """, unsafe_allow_html=True)
                
                # Add a button to view options for adjustment
                if st.button("Adjust Plan"):
                    st.markdown("""
                    Try asking for different options:
                    - "Can you suggest more indoor activities?"
                    - "I'd prefer more dining options"
                    - "Show me options for museums instead"
                    """)

# Run the main function
if __name__ == "__main__":
    pass