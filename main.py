
import tinytuya
import openai
import time
import speech_recognition as sr
import threading

# OpenAI Configuration
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
openai.api_key = OPENAI_API_KEY

# Global dictionary to store devices
devices = {}

# Predefined scenes
scenes = {
    "evening": {
        "actions": [
            {"device": "living room light", "command": "on"},
            {"device": "kitchen outlet", "command": "off"}
        ]
    },
    "work": {
        "actions": [
            {"device": "office light", "command": "on"},
            {"device": "fan", "command": "on"}
        ]
    }
}

# Discover devices
def discover_devices():
    print("Discovering Tuya devices...")
    discovered = tinytuya.deviceScan()
    print("Devices found:")
    for dev_id, info in discovered.items():
        print(f"Name: {info['name']}, ID: {dev_id}, IP: {info['ip']}, Version: {info['ver']}")
        if "ip" in info and "key" in info:
            devices[info['name'].lower()] = {
                "id": dev_id,
                "ip": info["ip"],
                "key": info["key"],
                "version": info["ver"]
            }

# Initialize devices
def initialize_devices():
    for name, info in devices.items():
        device = tinytuya.OutletDevice(info["id"], info["ip"], info["key"])
        device.set_version(info["version"])
        devices[name]["device"] = device

# Control devices
def control_device(device_name, command):
    device_info = devices.get(device_name.lower())
    if not device_info:
        print(f"Device '{device_name}' not found.")
        return

    device = device_info.get("device")
    if not device:
        print(f"Device object for '{device_name}' is not initialized.")
        return

    try:
        if command == "on":
            device.turn_on()
            print(f"{device_name} turned on.")
        elif command == "off":
            device.turn_off()
            print(f"{device_name} turned off.")
        else:
            print(f"Command '{command}' not recognized.")
    except Exception as e:
        print(f"Error controlling device: {e}")

# Execute scenes
def execute_scene(scene_name):
    scene = scenes.get(scene_name.lower())
    if not scene:
        print(f"Scene '{scene_name}' not found.")
        return

    print(f"Executing scene '{scene_name}'...")
    for action in scene["actions"]:
        device_name = action["device"]
        command = action["command"]
        control_device(device_name, command)

# Interpret commands using AI
def interpret_command_with_ai(command_text):
    prompt = (
        "You are a smart home assistant. Interpret the following command:
"
        f"Command: {command_text}
"
        "Respond with the format:
"
        "Action: <Execute Scene / Control Device>
"
        "Details: <Scene name or device name and action>"
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# Voice recognition
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            command = recognizer.recognize_google(audio, language="en-US")
            print(f"Recognized command: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Could not understand the command.")
            return None
        except sr.RequestError as e:
            print(f"Service error: {e}")
            return None

# Process voice commands
def process_command(command):
    if not command:
        return
    try:
        print(f"Analyzing command with AI: {command}")
        ai_response = interpret_command_with_ai(command)
        print(f"AI Response: {ai_response}")

        # Parse AI response
        lines = ai_response.split("\n")
        action = ""
        details = ""
        for line in lines:
            if line.startswith("Action:"):
                action = line.split(":")[1].strip()
            if line.startswith("Details:"):
                details = line.split(":")[1].strip()

        # Execute the action
        if action == "Execute Scene":
            execute_scene(details)
        elif action == "Control Device":
            device_name, device_command = details.split(" and ")
            control_device(device_name.strip(), device_command.strip())
        else:
            print("Action not recognized.")
    except Exception as e:
        print(f"Error processing command: {e}")

# Background thread for periodic device discovery
def periodic_device_discovery(interval=60):
    while True:
        print("Running periodic device discovery...")
        discover_devices()
        initialize_devices()
        print("Device list updated.")
        time.sleep(interval)

# Main program
def main():
    print("Welcome to TuyaVoiceControl!")
    discover_devices()
    initialize_devices()

    # Start periodic device discovery in the background
    discovery_thread = threading.Thread(target=periodic_device_discovery, args=(300,), daemon=True)
    discovery_thread.start()

    print("System ready. Say a command to control your devices or execute scenes.")
    while True:
        command = recognize_speech()
        if command == "exit":
            print("Exiting program.")
            break
        process_command(command)

if __name__ == "__main__":
    main()
