import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from geopy.geocoders import Nominatim
import geocoder

# Configure Streamlit page
st.set_page_config(
    page_title="🌤️ Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class WeatherApp:
    def __init__(self):
        self.api_key = None
        self.base_url = "http://api.openweathermap.org/data/2.5"
        self.forecast_url = "http://api.openweathermap.org/data/2.5/forecast"
        self.geocoder = Nominatim(user_agent="weather_app")
        
    def setup_api_key(self):
        """Setup API key from user input or session state"""
        if 'api_key' not in st.session_state:
            st.session_state.api_key = ""
            
        # API Key input in sidebar
        with st.sidebar:
            st.header("🔑 API Configuration")
            api_key = st.text_input(
                "OpenWeatherMap API Key",
                value=st.session_state.api_key,
                type="password",
                help="Get your free API key from https://openweathermap.org/api"
            )
            
            if api_key:
                st.session_state.api_key = api_key
                self.api_key = api_key
                st.success("✅ API Key configured!")
                
                # API key info
                with st.expander("ℹ️ How to get API Key"):
                    st.write("""
                    1. Visit [OpenWeatherMap](https://openweathermap.org/api)
                    2. Sign up for a free account
                    3. Go to API Keys section
                    4. Copy your API key
                    5. Paste it above
                    
                    **Note:** It may take a few minutes for new API keys to activate.
                    """)
            else:
                st.warning("⚠️ Please enter your OpenWeatherMap API key to use the app")
                return False
                
        return True
    
    def get_current_location(self):
        """Get current location using IP geolocation"""
        try:
            # Use geocoder to get location by IP
            g = geocoder.ip('me')
            if g.ok:
                return {
                    'lat': g.latlng[0],
                    'lon': g.latlng[1],
                    'city': g.city,
                    'country': g.country
                }
            else:
                # Fallback location (New York)
                return {
                    'lat': 40.7128,
                    'lon': -74.0060,
                    'city': 'New York',
                    'country': 'US'
                }
        except Exception as e:
            st.error(f"Error getting location: {str(e)}")
            # Fallback location
            return {
                'lat': 40.7128,
                'lon': -74.0060,
                'city': 'New York',
                'country': 'US'
            }
    
    def get_coordinates_from_city(self, city_name):
        """Get coordinates from city name using geocoding"""
        try:
            location = self.geocoder.geocode(city_name)
            if location:
                return {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'city': city_name,
                    'formatted_address': location.address
                }
            else:
                return None
        except Exception as e:
            st.error(f"Error geocoding city: {str(e)}")
            return None
    
    def get_weather_data(self, lat, lon):
        """Fetch current weather data from OpenWeatherMap API"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching weather data: {str(e)}")
            return None
    
    def get_forecast_data(self, lat, lon, days=5):
        """Fetch weather forecast data"""
        try:
            url = self.forecast_url
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (every 3 hours)
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching forecast data: {str(e)}")
            return None
    
    def get_weather_icon_url(self, icon_code):
        """Get weather icon URL"""
        return f"http://openweathermap.org/img/wn/{icon_code}@2x.png"
    
    def format_weather_data(self, weather_data):
        """Format weather data for display"""
        if not weather_data:
            return None
            
        return {
            'city': weather_data['name'],
            'country': weather_data['sys']['country'],
            'temperature': round(weather_data['main']['temp']),
            'feels_like': round(weather_data['main']['feels_like']),
            'humidity': weather_data['main']['humidity'],
            'pressure': weather_data['main']['pressure'],
            'visibility': weather_data.get('visibility', 0) / 1000,  # Convert to km
            'wind_speed': weather_data['wind']['speed'],
            'wind_direction': weather_data['wind'].get('deg', 0),
            'description': weather_data['weather'][0]['description'].title(),
            'icon': weather_data['weather'][0]['icon'],
            'sunrise': datetime.fromtimestamp(weather_data['sys']['sunrise']),
            'sunset': datetime.fromtimestamp(weather_data['sys']['sunset']),
            'clouds': weather_data['clouds']['all']
        }
    
    def display_current_weather(self, weather_info, title="Current Weather"):
        """Display current weather information"""
        if not weather_info:
            st.error("No weather data available")
            return
            
        st.subheader(f"🌍 {title}")
        
        # Main weather display
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.metric(
                label=f"{weather_info['city']}, {weather_info['country']}",
                value=f"{weather_info['temperature']}°C",
                delta=f"Feels like {weather_info['feels_like']}°C"
            )
            
            # Weather icon and description
            icon_url = self.get_weather_icon_url(weather_info['icon'])
            st.image(icon_url, width=100)
            st.write(f"**{weather_info['description']}**")
        
        with col2:
            st.write("") # Spacer
            
        with col3:
            # Additional metrics
            col3a, col3b = st.columns(2)
            
            with col3a:
                st.metric("Humidity", f"{weather_info['humidity']}%")
                st.metric("Pressure", f"{weather_info['pressure']} hPa")
                st.metric("Visibility", f"{weather_info['visibility']:.1f} km")
                
            with col3b:
                st.metric("Wind Speed", f"{weather_info['wind_speed']} m/s")
                st.metric("Clouds", f"{weather_info['clouds']}%")
                
        # Sun times
        st.write("---")
        col_sun1, col_sun2 = st.columns(2)
        with col_sun1:
            st.write(f"🌅 **Sunrise:** {weather_info['sunrise'].strftime('%H:%M')}")
        with col_sun2:
            st.write(f"🌇 **Sunset:** {weather_info['sunset'].strftime('%H:%M')}")
    
    def display_forecast(self, forecast_data):
        """Display weather forecast"""
        if not forecast_data:
            st.error("No forecast data available")
            return
            
        st.subheader("📅 5-Day Forecast")
        
        # Process forecast data
        forecast_list = []
        for item in forecast_data['list']:
            forecast_list.append({
                'datetime': datetime.fromtimestamp(item['dt']),
                'temperature': item['main']['temp'],
                'description': item['weather'][0]['description'],
                'icon': item['weather'][0]['icon'],
                'humidity': item['main']['humidity'],
                'wind_speed': item['wind']['speed']
            })
        
        # Group by day
        daily_forecasts = {}
        for forecast in forecast_list:
            date_key = forecast['datetime'].date()
            if date_key not in daily_forecasts:
                daily_forecasts[date_key] = []
            daily_forecasts[date_key].append(forecast)
        
        # Display daily forecasts
        forecast_cols = st.columns(5)
        for i, (date, day_forecasts) in enumerate(list(daily_forecasts.items())[:5]):
            if i < len(forecast_cols):
                with forecast_cols[i]:
                    # Get mid-day forecast (around noon)
                    midday_forecast = min(day_forecasts, 
                                        key=lambda x: abs(x['datetime'].hour - 12))
                    
                    st.write(f"**{date.strftime('%a, %b %d')}**")
                    
                    # Weather icon
                    icon_url = self.get_weather_icon_url(midday_forecast['icon'])
                    st.image(icon_url, width=60)
                    
                    # Temperature range
                    temps = [f['temperature'] for f in day_forecasts]
                    min_temp = min(temps)
                    max_temp = max(temps)
                    st.write(f"🌡️ {max_temp:.0f}°/{min_temp:.0f}°C")
                    
                    # Description
                    st.write(f"{midday_forecast['description'].title()}")
        
        # Temperature trend chart
        st.subheader("📈 Temperature Trend")
        
        df = pd.DataFrame(forecast_list)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df['temperature'],
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#ff6b6b', width=3),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Temperature Over Next 5 Days",
            xaxis_title="Date & Time",
            yaxis_title="Temperature (°C)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def display_weather_map(self, lat, lon, city_name):
        """Display weather map"""
        st.subheader(f"🗺️ Weather Map - {city_name}")
        
        # Create a simple map showing the location
        map_data = pd.DataFrame({
            'lat': [lat],
            'lon': [lon],
            'city': [city_name]
        })
        
        st.map(map_data, zoom=10)
    
    def run(self):
        """Main application runner"""
        # App header
        st.title("🌤️ Weather Dashboard")
        st.markdown("*Get real-time weather information for any location worldwide*")
        
        # Setup API key
        if not self.setup_api_key():
            return
            
        # Sidebar options
        with st.sidebar:
            st.header("📍 Location Options")
            location_option = st.radio(
                "Choose location method:",
                ["🎯 Current Location", "🔍 Search City"]
            )
            
            st.header("⚙️ Display Options")
            show_forecast = st.checkbox("Show 5-day forecast", value=True)
            show_map = st.checkbox("Show weather map", value=True)
            
        # Main content area
        if location_option == "🎯 Current Location":
            st.header("📍 Your Current Location Weather")
            
            if st.button("🔄 Get Current Location Weather", type="primary"):
                with st.spinner("Getting your location and weather data..."):
                    # Get current location
                    location = self.get_current_location()
                    
                    if location:
                        # Get weather data
                        weather_data = self.get_weather_data(location['lat'], location['lon'])
                        
                        if weather_data:
                            weather_info = self.format_weather_data(weather_data)
                            self.display_current_weather(weather_info, "Your Current Location")
                            
                            # Store in session state for other displays
                            st.session_state.current_weather = weather_info
                            st.session_state.current_location = location
                            
                            # Show forecast if enabled
                            if show_forecast:
                                forecast_data = self.get_forecast_data(location['lat'], location['lon'])
                                if forecast_data:
                                    self.display_forecast(forecast_data)
                            
                            # Show map if enabled
                            if show_map:
                                self.display_weather_map(
                                    location['lat'], 
                                    location['lon'], 
                                    f"{location['city']}, {location['country']}"
                                )
        
        else:  # Search City
            st.header("🔍 Search Weather by City")
            
            # City search input
            col1, col2 = st.columns([3, 1])
            
            with col1:
                city_name = st.text_input(
                    "Enter city name:",
                    placeholder="e.g., London, Paris, Tokyo, New York"
                )
            
            with col2:
                search_button = st.button("🔍 Search", type="primary")
            
            if search_button and city_name:
                with st.spinner(f"Searching weather for {city_name}..."):
                    # Get coordinates from city name
                    location = self.get_coordinates_from_city(city_name)
                    
                    if location:
                        # Get weather data
                        weather_data = self.get_weather_data(location['lat'], location['lon'])
                        
                        if weather_data:
                            weather_info = self.format_weather_data(weather_data)
                            self.display_current_weather(weather_info, f"Weather in {city_name}")
                            
                            # Show forecast if enabled
                            if show_forecast:
                                forecast_data = self.get_forecast_data(location['lat'], location['lon'])
                                if forecast_data:
                                    self.display_forecast(forecast_data)
                            
                            # Show map if enabled
                            if show_map:
                                self.display_weather_map(
                                    location['lat'], 
                                    location['lon'], 
                                    weather_info['city']
                                )
                        else:
                            st.error("Failed to fetch weather data. Please check your API key and try again.")
                    else:
                        st.error(f"City '{city_name}' not found. Please check the spelling and try again.")
            
            elif search_button and not city_name:
                st.warning("Please enter a city name to search.")
        
        # Quick city buttons
        st.markdown("---")
        st.subheader("🌍 Quick Weather Check")
        st.markdown("*Click on any city for instant weather:*")
        
        # Popular cities
        cities = [
            "London", "Paris", "Tokyo", "New York", "Sydney",
            "Dubai", "Singapore", "Mumbai", "São Paulo", "Cairo"
        ]
        
        city_cols = st.columns(5)
        for i, city in enumerate(cities):
            with city_cols[i % 5]:
                if st.button(city, key=f"quick_{city}"):
                    with st.spinner(f"Loading weather for {city}..."):
                        location = self.get_coordinates_from_city(city)
                        if location:
                            weather_data = self.get_weather_data(location['lat'], location['lon'])
                            if weather_data:
                                weather_info = self.format_weather_data(weather_data)
                                self.display_current_weather(weather_info, f"Weather in {city}")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Powered by OpenWeatherMap API | Built with Streamlit</p>
            <p>Weather data updates every 10 minutes</p>
        </div>
        """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    app = WeatherApp()
    app.run()