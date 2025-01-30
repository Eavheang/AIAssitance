import speech_recognition as sr
from openai import OpenAI  # Replace google.generativeai with openai
from dotenv import load_dotenv
import os
import time
import subprocess
import logging
import pyttsx3
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Configure DeepSeek API using the API key from .env
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("Please set the DEEPSEEK_API_KEY in the .env file.")

# Initialize DeepSeek client
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

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


# Function to listen for a query
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


# Function to generate response using DeepSeek
def generate_response(query):
    response = client.chat.completions.create(
        model="deepseek-chat",  # Use the appropriate DeepSeek model
        messages=[
            {"role": "system", "content": "You are a personal assistant designed to help with daily tasks and answer any questions. Your responses should be short, cheerful, and playful, like you're the closest friend of the person you're talking to. Keep your replies simple, clear, and easy to understand—no need for long explanations. Do not use emojis in your responses. Your goal is to assist in a friendly, natural way, just like a best friend would!"},
            {"role": "user", "content": query},
        ],
        stream=False
    )
    return response.choices[0].message.content


# Function to speak the response using pyttsx3
def speak_response(text):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error during speech generation: {e}")


def open_application(app_name):
    try:
        # Map common application names to their respective commands
        app_commands = {
            "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "firefox": "firefox",
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


# Main loop
def main():
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