# Absolute imports
from gpiozero import Button, LED
from threading import Thread
from time import sleep
import os
import signal
import subprocess
import sys

# Relative imports
from .app import create_app
from .database import db, Trigger
from .config import get_config


__all__ = []


# Load config as a dictionary
config = get_config()


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
        led.on()
        sleep(config['LED_ON_SECONDS'])
        led.off()
        sleep(config['LED_OFF_SECONDS'])


# Function to execute the command and control LEDs
def execute_command(button_index):
    def wrapper():
        button_pin = config['BUTTON_PINS'][button_index]
        command = "{player} {sf}".format(
            player=config['SOUNDFILE_PLAYER'],
            sf=os.path.expandvars(os.path.join(
                config['SOUNDFILE_FOLDER'],
                f"soundFile.{button_index}.GPIO{button_pin}"
            ))
        )
        print(f"Button {button_index} for GPIO{button_pin} pressed, executing command: {command}")

        # Turn off all LEDs and blink the pressed button's LED
        for i, led in enumerate(leds):
            if i == button_index:
                led.off()
                blink_thread = Thread(target=blink_led, args=(leds[button_index],))
                blink_thread.start()
            else:
                led.off()

        # Add trigger to database
        with create_app().app_context() as ctx:
            ctx.push()
            new_trigger = Trigger(button=button_index, pin=button_pin)
            db.session.add(new_trigger)
            db.session.commit()

        # Run the command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Command output:\n{result.stdout}")

        # Disable all buttons
        for i, button in enumerate(buttons):
            if i != button_index:
                button.when_pressed = None

        # Re-enable all buttons and set LEDs to standby mode after a delay
        sleep(config['BUTTON_OFF_SECONDS'])
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
