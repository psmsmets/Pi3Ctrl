# Absolute imports
from gpiozero import Button, LED
from threading import Thread
from time import sleep
import os
import signal
import subprocess
import sys

# Relative imports
from .config import Config
from .util import parse_config


# Load config
config = os.path.expandvars('$PI3CTRL_CONFIG')
config = parse_config(config if os.path.isfile(config) else None, defaults=Config().to_dict())

# Define the system commands to execute for each button
COMMANDS = [
    "echo Button 1 pressed",  # Change these to the commands you want to run
    f"/usr/bin/aplay {config['SAMPLE_FILE_2']}",
    "/usr/bin/aplay /opt/pi3ctrl/sampleFile3.wav"
]

# Create button and LED objects
buttons = [Button(pin) for pin in config['BUTTON_PINS']]
leds = [LED(pin) for pin in config['LED_PINS']]


# Function to set LEDs to standby mode
def set_leds_standby():
    for led in leds:
        led.on()


# Function to blink LED
def blink_led(led):
    while True:
        led.toggle()
        sleep(0.5)  # @CONFIG


# Function to execute the command and control LEDs
def execute_command(button_index):
    def wrapper():
        print(f"Button {button_index + 1} pressed, executing command: {COMMANDS[button_index]}")

        # Turn off all LEDs and blink the pressed button's LED
        for i, led in enumerate(leds):
            if i == button_index:
                led.off()
                blink_thread = Thread(target=blink_led, args=(leds[button_index],))
                blink_thread.start()
            else:
                led.off()

        # Run the command
        result = subprocess.run(COMMANDS[button_index], shell=True, capture_output=True, text=True)
        print(f"Command output:\n{result.stdout}")

        # Disable all buttons
        for i, button in enumerate(buttons):
            if i != button_index:
                button.when_pressed = None

        # Re-enable all buttons and set LEDs to standby mode after a delay
        sleep(5)  # Adjust the delay as needed @CONFIG
        for i, button in enumerate(buttons):
            if i != button_index:
                button.when_pressed = execute_command(i)

        # Stop blinking and set LEDs to standby mode
        blink_thread.join()
        set_leds_standby()

    return wrapper


# Function to handle clean exit
def exit_handler(signal, frame):
    print("Exiting script...")
    sys.exit(0)


def main():
    """
    """
    # Attach the execute_command function to each button
    for i, button in enumerate(buttons):
        button.when_pressed = execute_command(i)

    # Attach the exit handler to SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, exit_handler)

    # Set LEDs to standby mode initially
    set_leds_standby()

    # Keep the script running to monitor the GPIO pins
    print(f"Monitoring GPIO pins {config['BUTTON_PINS']} for rising edge events. Press Ctrl+C to exit.")
    signal.pause()


if __name__ == '__main__':
    main()
