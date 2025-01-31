import os, time, subprocess, logging, random, webbrowser, datetime, threading
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3
import winsound
import dateparser
import requests
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from PIL import Image, ImageDraw
import pystray
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API using the API key from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY in the .env file.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize recognizer and pyttsx3 engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Set up pyttsx3 properties for a more natural voice
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Change voice (0 for male, 1 for female)

# List of natural activation responses
ACTIVATION_RESPONSES = [
    "Hey, how can I help you?",
    "Hello, what can I do for you?",
    "Hi there, how can I assist you today?",
    "Hey, what do you need help with?",
]

# List of follow-up responses
FOLLOW_UP_RESPONSES = [
    "Is there anything else I can help you with?",
    "Do you need anything else?",
    "Let me know if there's something more I can do.",
    "Anything else on your mind?",
]

# Global list to store alarms and timers
alarms = []
timers = []

# Function to create a system tray icon
def create_system_tray_icon():
    # Create an image for the system tray icon
    image = Image.new('RGB', (64, 64), color='black')
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "Bob", fill='white')

    # Define the menu for the system tray icon
    menu = pystray.Menu(
        pystray.MenuItem("Exit", on_exit)
    )

    # Create the system tray icon
    icon = pystray.Icon("Bob", image, "Bob Assistant", menu)

    # Run the icon in the background
    icon.run()

# Function to handle exit from the system tray
def on_exit(icon, item):
    icon.stop()
    os._exit(0)

# Function to get the current location
def get_location():
    try:
        geolocator = Nominatim(user_agent="weatherApp")
        location = geolocator.geocode("Phnom Penh, Cambodia")
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except Exception as e:
        logging.error(f"Error fetching location: {e}")
        return None

def listen_for_activation():
    with sr.Microphone() as source:
        print("Listening for activation phrase...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized: {text}")
            # Check for either "hey bob" or "bob" in the recognized text
            return "hey bob" in text.lower() or "bob" in text.lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
    return False


def listen_for_query():
    with sr.Microphone() as source:
        print("Listening for query...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        try:
            query = recognizer.recognize_google(audio)
            print(f"Query: {query}")
            return query
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
    return None


def generate_response(query):
    response = model.generate_content(query)
    return response.text


def speak_response(text):
    try:
        engine.endLoop()  # Stop any ongoing speech synthesis
    except:
        pass  # Ignore errors if the loop isn't running

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error during speech generation: {e}")


def play_alarm():
    frequency = 2500  # Frequency of the alarm sound (in Hz)
    duration = 2000  # Duration of the alarm sound (in milliseconds)
    winsound.Beep(frequency, duration)  # Play the alarm sound


def set_alarm(alarm_time):
    alarms.append(alarm_time)
    return f"Alarm set for {alarm_time.strftime('%I:%M %p')}."


def set_timer(duration):
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
    timers.append(end_time)
    return f"Timer set for {duration} seconds."


def check_alarms_and_timers():
    while True:
        now = datetime.datetime.now()
        # print(f"Current time: {now.strftime('%I:%M %p')}")  # Print current time for debugging

        # Check alarms
        for alarm in alarms[:]:  # Iterate over a copy of the list to safely remove elements
            print(f"Checking alarm for: {alarm.strftime('%I:%M %p')}")  # Print alarm time for debugging
            if now >= alarm:
                print("Wake up!")
                play_alarm()
                alarms.remove(alarm)

        # Check timers
        for timer in timers[:]:  # Iterate over a copy of the list to safely remove elements
            if now >= timer:
                print("Timer is up!")
                speak_response("Your timer is up!")  # Add voice response
                play_alarm()
                timers.remove(timer)  # Remove expired timer

        time.sleep(1)  # Check every second


# Function to fetch weather based on location
def get_weather():
    # Get the current latitude and longitude
    location = get_location()
    if location:
        lat, lon = location
    else:
        return "Sorry, couldn't retrieve your location."

    # OpenWeatherMap API key from environment
    API_KEY = os.getenv("OPENWEATHER_API_KEY")
    if not API_KEY:
        raise ValueError("Please set the OPENWEATHER_API_KEY in the .env file.")

    # OpenWeatherMap API endpoint for current weather data using coordinates
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            # Extract weather data
            main = data["main"]
            weather = data["weather"][0]
            temperature = main["temp"]
            description = weather["description"]
            city_name = data["name"]  # Using the name returned from OpenWeatherMap
            return f"The current weather in {city_name} is {temperature}°C with {description}."
        else:
            return "Sorry, I couldn't fetch the weather data."
    except Exception as e:
        logging.error(f"Error fetching weather data: {e}")
        return "Sorry, there was an error fetching the weather."
def open_application(app_name):
    try:
        # Map common application names to their respective commands
        app_commands = {
            "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": "notepad",
            "calculator": "calc",
            "vs code": r'C:\Users\oenge\AppData\Local\Programs\Microsoft VS Code\Code.exe',
            # Add more applications as needed
        }

        app_name_lower = app_name.lower()
        if app_name_lower in app_commands:
            command = app_commands[app_name_lower]
            subprocess.Popen([command], shell=True)
            logging.info(f"Opening {app_name}...")
            return f"Opening {app_name}..."
        else:
            logging.warning(f"Application '{app_name}' not found in the command map.")
            return f"Sorry, I don't know how to open {app_name}."

    except Exception as e:
        logging.error(f"An error occurred while trying to open {app_name}: {e}")
        return f"An error occurred while trying to open {app_name}: {e}"


# Global WebDriver instance
driver = None

def play_music(song_name):
    global driver

    try:
        # Check if the WebDriver instance already exists
        if driver is None:
            # Setup Edge WebDriver
            options = webdriver.EdgeOptions()
            options.add_argument("--start-maximized")  # Open browser in full screen
            driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)

        # Open YouTube
        driver.get("https://www.youtube.com")

        # Find the search bar and enter the song name
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.send_keys(song_name)
        search_box.send_keys(Keys.RETURN)

        # Wait for search results to load
        time.sleep(3)

        # Click the first video result
        first_video = driver.find_elements(By.ID, "video-title")[0]
        first_video.click()

        logging.info(f"Playing {song_name} on YouTube...")
        return f"Playing {song_name} on YouTube..."

    except Exception as e:
        logging.error(f"An error occurred while trying to play music: {e}")
        return f"An error occurred while trying to play music: {e}"


def parse_time(query):
    try:
        # Use dateparser to parse natural language time expressions
        parsed_time = dateparser.parse(query, settings={'PREFER_DATES_FROM': 'future'})
        if parsed_time:
            return parsed_time
        else:
            return None
    except Exception as e:
        logging.error(f"Error parsing time: {e}")
        return None


def main():
    # Start the alarm/timer checker in a separate thread
    threading.Thread(target=check_alarms_and_timers, daemon=True).start()

    while True:
        if listen_for_activation():
            # Respond with a natural activation phrase
            activation_response = random.choice(ACTIVATION_RESPONSES)
            print(f"Bob: {activation_response}")
            speak_response(activation_response)

            # Wait for 1 second before listening for the query
            time.sleep(1)

            # Listen for the user's query
            query = listen_for_query()
            if query:
                if "open" in query.lower():
                    # Extract the application name from the query
                    app_name = query.lower().replace("open", "").strip()
                    response_text = open_application(app_name)
                elif "play" in query.lower():
                    # Extract the song name from the query
                    song_name = query.lower().replace("play", "").strip()
                    response_text = play_music(song_name)
                elif "set alarm" in query.lower():
                    # Extract the time from the query
                    time_str = query.lower().replace("set alarm", "").strip()
                    alarm_time = parse_time(time_str)
                    if alarm_time:
                        response_text = set_alarm(alarm_time)
                    else:
                        response_text = "Sorry, I didn't understand the time. Please try again."
                elif "set timer" in query.lower():
                    # Extract the duration and unit from the query
                    query_lower = query.lower().replace("set timer for", "").strip()
                    words = query_lower.split()
                    try:
                        # Get the number from the words
                        duration = int(words[0])  # First word should be the number
                        unit = words[1] if len(words) > 1 else "seconds"  # Default to seconds if no unit is provided

                        # Convert to seconds
                        if "minute" in unit:
                            duration *= 60
                        elif "hour" in unit:
                            duration *= 3600

                        response_text = set_timer(duration)
                    except (ValueError, IndexError):
                        response_text = "Sorry, I didn't understand the duration. Please try again."
                elif "weather" in query.lower():
                    response_text = get_weather()
                else:
                    response_text = generate_response(query)

                print(f"Bob: {response_text}")
                speak_response(response_text)

                # Ask a follow-up question
                follow_up_response = random.choice(FOLLOW_UP_RESPONSES)
                print(f"Bob: {follow_up_response}")
                speak_response(follow_up_response)


# Run the main loop
if __name__ == "__main__":
    main()