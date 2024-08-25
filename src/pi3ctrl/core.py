# Absolute imports
from gpiozero import Button, LED
from gpiozero.exc import CallbackSetToNone
from threading import Thread, Event, Lock
from time import sleep
import os
import signal
import subprocess
import sys
import warnings

# Relative imports
from .app import create_app
from .database import db, Trigger
from .config import get_config
from .utils import get_logger


__all__ = []


# Suppress the specific CallbackSetToNone warning
warnings.filterwarnings("ignore", category=CallbackSetToNone)


# Create a subclass of Button
class IndexedButton(Button):
    def __init__(self, pin, index, *args, **kwargs):
        # Initialize the Button class with its original parameters
        super().__init__(pin, *args, **kwargs)
        # Add the index attribute
        self.index = index


# Create a subclass of LED
class IndexedLED(LED):
    def __init__(self, pin, index, *args, **kwargs):
        # Initialize the Button class with its original parameters
        super().__init__(pin, *args, **kwargs)
        # Add the index attribute
        self.index = index


# Load config as a dictionary
_config = get_config()


# Construct the logger object
_logger = get_logger('pi3ctrl-core', debug=_config['DEBUG'])


# Create button and LED objects
_buttons = [IndexedButton(pin, index=i) for i, pin in enumerate(_config['BUTTON_PINS'])]
_leds = [IndexedLED(pin, index=i) for i, pin in enumerate(_config['LED_PINS'])]


# Init command lock
_execute_command_lock = Lock()


# Function to set LEDs to standby mode
def set_leds_standby():
    leds = _leds
    for led in leds:
        led.on()


# Function to blink LED with an event to stop blinking
def blink_led(led, stop_event):
    config = _config
    while not stop_event.is_set():
        led.on()
        sleep(config['LED_ON_SECONDS'])
        led.off()
        sleep(config['LED_OFF_SECONDS'])


def debounce_button(button, interval):
    button.when_pressed = None  # Temporarily disable the button
    sleep(interval)  # Wait for debounce interval
    button.when_pressed = execute_command  # Re-enable the button


# Function to execute the command and control LEDs
def execute_command(button: Button):
    """Function handled when the GPIO pin is triggered."""

    if _execute_command_lock.locked():
        print("Command already running, ignoring this press.")
        return

    with _execute_command_lock:

        # Disable all buttons immediately to prevent multiple triggers
        for btn in _buttons:
            btn.when_pressed = None

        try:
            # From global
            config = _config
            leds = _leds
            logger = _logger

            # Construct button command
            command = "{player} {sf} -v".format(
                player=config['SOUNDFILE_PLAYER'],
                sf=os.path.expandvars(os.path.join(
                    config['SOUNDFILE_FOLDER'],
                    f"soundFile.{button.index}.{button.pin}"
                ))
            )
            logger.info(f"Button {button.index} for {button.pin} pressed, executing command: {command}")

            # Turn off all LEDs and blink the pressed button's LED
            print("Blink activated LED and disable other LEDs")
            stop_event = Event()
            blink_thread = None
            for i, led in enumerate(leds):
                if i == button.index:
                    led.off()
                    blink_thread = Thread(target=blink_led, args=(leds[button.index], stop_event))
                    blink_thread.start()
                else:
                    led.off()

            # Add trigger to database
            logger.debug("Add trigger to database")
            with create_app().app_context() as ctx:
                ctx.push()
                new_trigger = Trigger(button=button.index, pin=button.pin.number)
                db.session.add(new_trigger)
                db.session.commit()

            # Run the command
            logger.debug("Execute command")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            logger.debug(f"Command output: {result.stdout}")

        finally:
            # Stop blinking, reset LEDs, re-enable buttons with debounce
            logger.debug("Reset LEDs")
            if blink_thread is not None:
                stop_event.set()
                blink_thread.join()
            set_leds_standby()

            # Re-enable buttons with a debounce period
            logger.debug("Re-enable buttons")
            debounce_interval = 0.3  # 300ms debounce interval
            for btn in _buttons:
                Thread(target=debounce_button, args=(btn, debounce_interval)).start()

        logger.info(f"Button {button.index} when pressed function done.")


# Function to handle clean exit
def exit_handler(signal, frame):
    _logger.info("Exiting script...")
    sys.exit(0)


def main():
    """
    """
    # From global
    config = _config
    buttons = _buttons
    logger = _logger

    # Attach the execute_command function to each button
    for button in buttons:
        button.when_pressed = execute_command

    # Attach the exit handler to SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, exit_handler)

    # Set LEDs to standby mode initially
    set_leds_standby()

    # Keep the script running to monitor the GPIO pins
    logger.info(f"Monitoring GPIO pins {config['BUTTON_PINS']} for rising edge events. Press Ctrl+C to exit.")
    signal.pause()


if __name__ == '__main__':
    main()
