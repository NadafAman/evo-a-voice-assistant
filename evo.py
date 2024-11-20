import json
import speech_recognition as sr
import datetime
import random
import wikipedia
import webbrowser
import time
from gtts import gTTS
import pygame
import os
import uuid
from transformers import pipeline

# Set the Wikipedia language
wikipedia.set_lang('en')

# Initialize pygame mixer
pygame.mixer.init()

# Initialize the text generation model
generator = pipeline('text-generation', model='gpt2')

stop_flag = False
is_sleeping = False

# Load intents from the intents.json file
with open('intents.json', 'r') as file:
    intents = json.load(file)["intents"]
    
def speak(audio):
    audio_folder = "audio"  # Specify your audio folder
    if not os.path.exists(audio_folder):
        os.makedirs(audio_folder)  # Create the folder if it doesn't exist

    # Generate a unique filename for the audio file
    filename = os.path.join(audio_folder, f"temp_{uuid.uuid4()}.mp3")
    
    # Save the audio to the specified folder
    tts = gTTS(text=audio, lang='en')
    tts.save(filename)
    
    # Load and play the audio file
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    
    # Wait until the music is done playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Cleanup the temporary audio file
    try:
        os.remove(filename)
    except PermissionError:
        print("File is currently in use. Please close any applications using it.")
        
def get_user_input():
    r = sr.Recognizer()
    r.pause_threshold = 1
    r.energy_threshold = 290
    while True:
        with sr.Microphone() as mic:
            print("Listening....")
            audio = r.listen(mic)

        try:
            query = r.recognize_google(audio, language='en-in')
            return query
        except Exception:
            speak("Sorry!! I did not understand that. Could you please repeat?")

def intent_recognition(user_input):
    best_intent = None
    max_match_count = 0

    for intent in intents:
        match_count = 0
        for example in intent["examples"]:
            if example.lower() in user_input.lower():
                match_count += 1

        if match_count > max_match_count:
            max_match_count = match_count
            best_intent = intent

    return best_intent

def stop_Evio():
    speak('Shutting down Evio!')
    global stop_flag
    stop_flag = True

def sleep_Evio():
    global is_sleeping
    is_sleeping = True
    speak("Going to sleep! Wake me up by calling my name!")

def wake_Evio():
    global is_sleeping
    r = sr.Recognizer()
    r.pause_threshold = 1
    r.energy_threshold = 290

    while is_sleeping:
        with sr.Microphone() as mic:
            print("Listening for wake word....")
            audio = r.listen(mic)

        try:
            query = r.recognize_google(audio, language='en-in')
            if "evo" in query.lower():
                is_sleeping = False
                speak("Hey! I am up. What can I do for you?")
        except Exception:
            pass

def search_wikipedia():
    speak("What do you want me to search?")
    query = get_user_input()
    speak("Searching Wikipedia...")
    query = query.replace("on wikipedia", "")
    try:
        result = wikipedia.summary(query, sentences=3)
        speak("According to Wikipedia")
        speak(result)
    except wikipedia.exceptions.PageError:
        speak("I couldn't find any information on Wikipedia for that query.")

def search_youtube():
    speak("What do you want me to search?")
    query = get_user_input()
    youtube_url = f"https://www.youtube.com/results?search_query={query}"
    try:
        webbrowser.open(youtube_url)
    except webbrowser.Error:
        speak("I couldn't search it on YouTube.")

def search_google():
    speak("What do you want me to search?")
    query = get_user_input()
    google_url = f"https://www.google.com/search?q={query}"
    try:
        webbrowser.open(google_url)
    except webbrowser.Error:
        speak("I couldn't connect to Google.")

def get_time():
    strTime = datetime.datetime.now().strftime("%H:%M")
    speak(f"The time is {strTime}")

def set_timer():
    speak("Sure! Please specify the duration for the timer in seconds, minutes, or hours.")

    try:
        user_input = get_user_input().lower()
        print(user_input)

        duration = 0
        words = user_input.split()

        for i in range(0, len(words), 2):
            value = int(words[i])
            unit = words[i + 1]
            if "minute" in unit or "mins" in unit:
                duration += value * 60
            elif "hour" in unit:
                duration += value * 3600
            elif "second" in unit or "secs" in unit:
                duration += value

        if duration > 0:
            speak(f"Timer set for {user_input}. I will notify you when it's time.")
            time.sleep(duration)
            speak("Timer has ended. Time's up!")
        else:
            speak("Could not set a timer. Please specify a valid duration.")

    except ValueError:
        speak("Could not set a timer! Please provide a numeric duration.")
    except Exception:
        speak("Could not set a timer due to an unexpected error.")

def respond_to_query(query):
    response = generator(query, max_length=50, num_return_sequences=1)
    return response[0]['generated_text'].strip()

# Mapping of actions
mapping = {
    "search_wikipedia": search_wikipedia,
    "get_time": get_time,
    "stop_Evio": stop_Evio,
    "search_google": search_google,
    "search_youtube": search_youtube,
    "sleep_Evio": sleep_Evio,
    "set_timer": set_timer,
}

if __name__ == "__main__":
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        speak("Good Morning!")
    elif hour >= 12 and hour < 17:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak("I am Evio, your voice assistant! How can I help you today?")

    while not stop_flag:
        if not is_sleeping:
            user_input = get_user_input()
            print(user_input)
            recognized_intent = intent_recognition(user_input)
            print(recognized_intent)
            if recognized_intent:
                if "responses" in recognized_intent:
                    responses = recognized_intent['responses']
                    respond = random.choice(responses)
                    speak(respond)
                if "action" in recognized_intent:
                    action = recognized_intent["action"]

                    if action in mapping:
                        mapping[action]()
                        if action != "stop_Evio" and action != "sleep_Evio":
                            sleep_Evio()
                    else:
                        speak("I don't know how to do this!")
                        sleep_Evio()
            else:
                # If no intent is recognized, respond to the user's query using the transformer
                response = respond_to_query(user_input)
                speak(response)
        else:
            wake_Evio()
