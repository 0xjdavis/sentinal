# Add this to both apps to enable autonomous conversation

import streamlit as st
import time
import json
import requests
from datetime import datetime, timedelta
import random
import threading

# Configuration
WEATHER_APP_URL = "https://sentinal.streamlit.app"
DAY_PLANNER_APP_URL = "https://day-planner.streamlit.app"  # Example URL
CONVERSATION_INTERVAL = 60  # seconds between conversation cycles

# Conversation history storage
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Message class to represent messages in the conversation
class Message:
    def __init__(self, sender, receiver, content, timestamp=None):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        msg = Message(
            data["sender"],
            data["receiver"],
            data["content"]
        )
        msg.timestamp = datetime.fromisoformat(data["timestamp"])
        return msg

# Weather App Agent Communication Functions
class WeatherAppCommunicator:
    def __init__(self):
        self.name = "WeatherApp"
    
    def receive_message(self, message):
        """Process incoming messages from the Day Planner"""
        # Log the received message
        st.session_state.conversation_history.append(message)
        
        # Process the message based on its content
        if isinstance(message.content, dict) and "request_type" in message.content:
            request_type = message.content["request_type"]
            
            if request_type == "weather_request":
                # Process weather request from Day Planner
                location = message.content.get("location", {})
                lat = location.get("lat", 0)
                lon = location.get("lon", 0)
                source = message.content.get("source", "tomorrow")
                
                # Get weather data using existing weather data agent
                weather_response = st.session_state.ui_agent.get_weather_for_location(
                    lat, lon, source
                )
                
                # Create response message
                response_content = {
                    "response_type": "weather_data",
                    "success": weather_response.get("success", False),
                    "data": weather_response.get("data", {})
                }
                
                response = Message(
                    self.name,
                    message.sender,
                    response_content
                )
                
                # Log and return the response
                st.session_state.conversation_history.append(response)
                return response
                
            elif request_type == "forecast_request":
                # Process forecast request
                location = message.content.get("location", {})
                lat = location.get("lat", 0)
                lon = location.get("lon", 0)
                source = message.content.get("source", "tomorrow")
                
                # Get forecast data
                forecast_response = st.session_state.ui_agent.get_forecast_for_location(
                    lat, lon, source
                )
                
                # Create response message
                response_content = {
                    "response_type": "forecast_data",
                    "success": forecast_response.get("success", False),
                    "data": forecast_response.get("data", {})
                }
                
                response = Message(
                    self.name,
                    message.sender,
                    response_content
                )
                
                # Log and return the response
                st.session_state.conversation_history.append(response)
                return response
                
        # Default response for unrecognized messages
        response = Message(
            self.name,
            message.sender,
            {"response_type": "error", "message": "Unrecognized request"}
        )
        
        st.session_state.conversation_history.append(response)
        return response
    
    def send_message(self, receiver, content):
        """Send a message to another app (not used by Weather App in this example)"""
        message = Message(self.name, receiver, content)
        st.session_state.conversation_history.append(message)
        
        # In a real implementation, this would make an API call to the other app
        # For demonstration, we'll just log the message
        print(f"Message sent from {self.name} to {receiver}: {content}")
        return message

# Day Planner Agent Communication Functions
class DayPlannerCommunicator:
    def __init__(self):
        self.name = "DayPlanner"
        self.locations = [
            {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060},
            {"name": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437},
            {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
            {"name": "Miami, FL", "lat": 25.7617, "lon": -80.1918},
            {"name": "Seattle, WA", "lat": 47.6062, "lon": -122.3321},
            {"name": "Donner Lake, CA", "lat": 39.1395453, "lon": -120.1664349},
        ]
    
    def receive_message(self, message):
        """Process incoming messages from the Weather App"""
        # Log the received message
        st.session_state.conversation_history.append(message)
        
        # Process the message based on its content
        if isinstance(message.content, dict) and "response_type" in message.content:
            response_type = message.content["response_type"]
            
            if response_type == "weather_data" or response_type == "forecast_data":
                # Process weather/forecast data and generate a plan
                if message.content.get("success", False):
                    # Create a response that acknowledges receipt of data
                    response_content = {
                        "response_type": "acknowledgment",
                        "message": f"Received {response_type}. Generating plan based on weather data.",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # In a real implementation, we would generate a plan here
                    # based on the weather data
                    
                    response = Message(
                        self.name,
                        message.sender,
                        response_content
                    )
                    
                    # Log and return the response
                    st.session_state.conversation_history.append(response)
                    return response
                else:
                    # Error handling
                    response_content = {
                        "response_type": "error_acknowledgment",
                        "message": f"Error in {response_type}. Cannot generate plan.",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    response = Message(
                        self.name,
                        message.sender,
                        response_content
                    )
                    
                    # Log and return the response
                    st.session_state.conversation_history.append(response)
                    return response
        
        # Default response for unrecognized messages
        response = Message(
            self.name,
            message.sender,
            {"response_type": "error", "message": "Unrecognized response"}
        )
        
        st.session_state.conversation_history.append(response)
        return response
    
    def send_message(self, receiver, content):
        """Send a message to the Weather App"""
        message = Message(self.name, receiver, content)
        st.session_state.conversation_history.append(message)
        
        # In a real implementation, this would make an API call to the Weather App
        # For demonstration, we'll just log the message and simulate a response
        print(f"Message sent from {self.name} to {receiver}: {content}")
        
        # Simulate sending to Weather App by making an API call
        try:
            # Construct query parameters from the message content
            if "request_type" in content:
                params = {
                    "request_type": content["request_type"].replace("_request", ""),
                }
                
                if "location" in content:
                    params["lat"] = content["location"]["lat"]
                    params["lon"] = content["location"]["lon"]
                
                if "source" in content:
                    params["source"] = content["source"]
                
                # Make request to Weather App
                response = requests.get(
                    WEATHER_APP_URL,
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    # Process the response
                    try:
                        # Try to parse as JSON
                        data = response.json()
                        response_message = Message(
                            receiver,
                            self.name,
                            {
                                "response_type": params["request_type"] + "_data",
                                "success": True,
                                "data": data
                            }
                        )
                        
                        # Log the response
                        st.session_state.conversation_history.append(response_message)
                        return response_message
                    except:
                        # If not JSON, treat as error
                        response_message = Message(
                            receiver,
                            self.name,
                            {
                                "response_type": "error",
                                "message": "Could not parse response from Weather App"
                            }
                        )
                        
                        # Log the response
                        st.session_state.conversation_history.append(response_message)
                        return response_message
                else:
                    # Handle unsuccessful response
                    response_message = Message(
                        receiver,
                        self.name,
                        {
                            "response_type": "error",
                            "message": f"Error response from Weather App: {response.status_code}"
                        }
                    )
                    
                    # Log the response
                    st.session_state.conversation_history.append(response_message)
                    return response_message
                    
        except Exception as e:
            # Handle connection errors
            response_message = Message(
                receiver,
                self.name,
                {
                    "response_type": "error",
                    "message": f"Error connecting to Weather App: {str(e)}"
                }
            )
            
            # Log the response
            st.session_state.conversation_history.append(response_message)
            return response_message
    
    def initiate_conversation(self):
        """Initiates a conversation with the Weather App by requesting weather data"""
        # Select a random location
        location = random.choice(self.locations)
        
        # Create a weather request message
        content = {
            "request_type": "weather_request",
            "location": {
                "name": location["name"],
                "lat": location["lat"],
                "lon": location["lon"]
            },
            "source": "tomorrow",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send the message to the Weather App
        return self.send_message("WeatherApp", content)

# Function to run the autonomous conversation
def run_autonomous_conversation():
    """Run the conversation between the Weather App and Day Planner"""
    # Check which app we're running in
    app_type = st.session_state.get("app_type", None)
    
    if app_type == "weather":
        # Weather App logic - just wait for requests
        pass
    elif app_type == "planner":
        # Day Planner logic - initiate the conversation
        if "planner_communicator" not in st.session_state:
            st.session_state.planner_communicator = DayPlannerCommunicator()
        
        # Initiate a conversation every CONVERSATION_INTERVAL seconds
        if "last_conversation" not in st.session_state:
            st.session_state.last_conversation = datetime.now() - timedelta(seconds=CONVERSATION_INTERVAL + 1)
        
        # Check if it's time for a new conversation
        if (datetime.now() - st.session_state.last_conversation).total_seconds() > CONVERSATION_INTERVAL:
            st.session_state.planner_communicator.initiate_conversation()
            st.session_state.last_conversation = datetime.now()
            st.rerun()  # Refresh the UI to show the new conversation

# Display conversation history
def display_conversation_history():
    """Display the conversation history in the UI"""
    st.subheader("Agent Conversation")
    
    conversation_container = st.container(height=400)
    with conversation_container:
        for message in st.session_state.conversation_history:
            if message.sender == "WeatherApp":
                st.markdown(f"""
                <div style="background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Weather App → Day Planner</strong><br>
                    <small>{message.timestamp.strftime("%I:%M:%S %p")}</small><br>
                    {format_message_content(message.content)}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #f0f7ea; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <strong>Day Planner → Weather App</strong><br>
                    <small>{message.timestamp.strftime("%I:%M:%S %p")}</small><br>
                    {format_message_content(message.content)}
                </div>
                """, unsafe_allow_html=True)

# Helper function to format message content
def format_message_content(content):
    """Format the message content for display"""
    if isinstance(content, dict):
        # Format different message types differently
        if "request_type" in content:
            if content["request_type"] == "weather_request":
                location = content.get("location", {})
                return f"""
                <strong>Weather Request:</strong><br>
                Location: {location.get("name", "Unknown")}<br>
                Coordinates: {location.get("lat", 0)}, {location.get("lon", 0)}<br>
                Source: {content.get("source", "unknown")}
                """
            elif content["request_type"] == "forecast_request":
                location = content.get("location", {})
                return f"""
                <strong>Forecast Request:</strong><br>
                Location: {location.get("name", "Unknown")}<br>
                Coordinates: {location.get("lat", 0)}, {location.get("lon", 0)}<br>
                Source: {content.get("source", "unknown")}
                """
        elif "response_type" in content:
            if content["response_type"] == "weather_data":
                if content.get("success", False):
                    weather_data = content.get("data", {})
                    current = weather_data.get("current", {})
                    return f"""
                    <strong>Weather Data Response:</strong><br>
                    Temperature: {current.get("temperature", "N/A")}°<br>
                    Conditions: {current.get("shortForecast", current.get("weatherText", "N/A"))}<br>
                    Wind: {current.get("windSpeed", "N/A")}
                    """
                else:
                    return "<strong>Weather Data Response:</strong><br>Error fetching weather data"
            elif content["response_type"] == "forecast_data":
                if content.get("success", False):
                    return "<strong>Forecast Data Response:</strong><br>Forecast data received successfully"
                else:
                    return "<strong>Forecast Data Response:</strong><br>Error fetching forecast data"
            elif content["response_type"] == "acknowledgment":
                return f"<strong>Acknowledgment:</strong><br>{content.get('message', 'Message received')}"
            elif content["response_type"] == "error":
                return f"<strong>Error:</strong><br>{content.get('message', 'Unknown error')}"
    
    # Default formatting for string content or unrecognized formats
    return str(content)

# Add to the main function in the Weather App
def add_to_weather_app_main():
    # Set app type
    st.session_state.app_type = "weather"
    
    # Initialize communicator if needed
    if "weather_communicator" not in st.session_state:
        st.session_state.weather_communicator = WeatherAppCommunicator()
    
    # Run the autonomous conversation
    run_autonomous_conversation()
    
    # Add a section to display conversation history
    st.markdown("---")
    display_conversation_history()

# Add to the main function in the Day Planner App
def add_to_day_planner_main():
    # Set app type
    st.session_state.app_type = "planner"
    
    # Initialize communicator if needed
    if "planner_communicator" not in st.session_state:
        st.session_state.planner_communicator = DayPlannerCommunicator()
    
    # Run the autonomous conversation
    run_autonomous_conversation()
    
    # Add a section to display conversation history
    st.markdown("---")
    display_conversation_history()
    
    # Add controls to manually trigger conversations
    st.button("Request Weather Update", on_click=lambda: st.session_state.planner_communicator.initiate_conversation())