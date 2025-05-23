#!/usr/bin/env python3
'''
Generic electronic Visual Analogue Scale (eVAS) to record subjective pain in (pain) studies.

This script has been tested in Windows using Python 3.12.0.

Please install pip packages according to the requirements.txt file.
'''

from meta_info import app_version

import os
import sys
import logging
from datetime import datetime

def get_current_path():
    """Retrieve the current path of script/application correctly, dependent on the OS and whether its frozen or not.

    Returns:
        str: Path string to executed script/application.
    """
    if getattr(sys, 'frozen', False):
        # if on Mac and frozen
        if (sys.platform == "darwin") and (".app" in sys.executable):
            app_path = os.path.dirname(sys.executable)
            return os.path.abspath(os.path.join(app_path, os.pardir, os.pardir, os.pardir))
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

current_path = get_current_path()
log_filename = current_path + os.sep + "log.txt"
logging.basicConfig(filename= log_filename, level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

try:
    import time
    import glob
    import psutil
    import requests
    import pyautogui
    import threading
    import webbrowser
    import configparser
    import tkinter as tk
    from functools import wraps
    from packaging import version
    from tkinter.messagebox import showinfo, askquestion
    from tkinter.constants import *
    from contextlib import contextmanager
    from urllib.request import urlretrieve
    import PIL.Image, PIL.ImageTk
    from screeninfo import get_monitors
    from pynput.keyboard import Key, Listener
    from send_trigger import get_com, send_start_trigger

except Exception as e:
    logging.exception(f"Import error: '{e}'.")


def clip(value, min_value, max_value):
    return max(min_value, min(value, max_value))

def linspace(start, stop, num):
    step = (stop - start) / (num - 1) if num > 1 else 0
    return [start + i * step for i in range(num)]

def get_key_string(x):
    # get string and remove "Key."
    x = [str(i).replace("Key.", "") for i in x]
    if len(x) == 1:
        return x[0]
    if len(x) == 2:
        return x[0] + " or " + x[1]
    if len(x) > 2:
        x = [el if ((i+1)==len(x)) else el+"," for i, el in enumerate(x)]
        x.insert(len(x)-1, 'or')
        return " ".join(x)

def try_delete_log_file():
    """If empty, tries to delete the logging file. Upon error, only prints the error to the console. 
    """
    try:
        if os.stat(log_filename).st_size == 0:
            os.remove(log_filename)
    except Exception as e:
        print("Could not remove log file.")
        print(f"Error: '{e}'")

#################################################################################################################
def throw_config_error(text):
    """Function to throw an error when the config file could not be read.
    Creates a message in the logging file, ends the VAS and prompts a message to the user.

    Args:
        text (str): Error message that will be logged.
    """
    logging.exception(f"Config error, Version: {app_version}")
    logging.exception(text)
    if "vas" in globals():
        vas.end()
    message(showinfo, 
            title="eVAS: Warning", 
            message=f"An error ocurred while reading the config file. " +
                     "Probably a setting not permitted was chosen. " +
                     "Simplest solution is to delete the '{config_file_name}' file.")
    sys.exit()

# Catch errors
def catch(func):
    '''Decorator that catches errors, logs them and creates a user warning.'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logging.exception(e)
            logging.exception(f"Version: {app_version}")
            if "vas" in globals():
                vas.end()
            message(showinfo, 
                title="eVAS: Warning", 
                message=f"An unknown error ocurred. " +
                         "Please contact Philip Gouverneur <philipgouverneur@gmx.de> " +
                         "and provide the created 'log.txt' file.")
            sys.exit()
    return wrapper

def is_already_running():
    """Function to check whether the application is already running.

    Returns:
        bool: Whether another instance of the eVAS is already running.
    """
    processes = [p for p in psutil.process_iter() if 'eVAS.exe' in p.name()]
    return len(processes) > 2

#################################################################################################################
# Config file
config_file_name = "config.ini"

def create_config():
    """Creates the default configuration file with it default elements.

    Returns:
        ConfigParser: Default configuration.
    """
    config = configparser.ConfigParser(allow_no_value=True)

    # preserve capital letters in config
    config.optionxform = str

    config.add_section("general")
    config.set("general", "# Sampling rate: How often should values be saved to file (in seconds).")
    config.set("general", "sampling_rate", "0.1")
    config.set("general", "# Whether to save values only upon change. Should be: True/False")
    config.set("general", "only_on_change", "True")
    config.set("general", "# Whether to use the second screen to show the eVAS. Should be: True/False")
    config.set("general", "use_second_screen", "True")

    config.add_section("scale")
    config.set("scale", "# Define the anchor labels of the scale. You can wrap text by placing a '\\n' in the label.")
    config.set("scale", "anchors", "['No pain', 'Highest\\nimaginable pain']")
    config.set("scale", "# Font size of the defined anchor labels above.")
    config.set("scale", "label_size", "32")
    config.set("scale", "# Define the value range")
    config.set("scale", "range", "[0, 1]")
    config.set("scale", "# Define the start value")
    config.set("scale", "start", "0")
    config.set("scale", "# Step size to move the slider whenever a key is released.")
    config.set("scale", "step_size", "0.02")
    config.set("scale", "# Height of vertical lines for each anchor. Can be 0 to not draw any vertical lines.")
    config.set("scale", "vertical_line_height", "0")
    config.set("scale", "# Whether to plot numbers below the lines. Should be: True/False")
    config.set("scale", "numbers", "False")
    config.set("scale", "# Font size of the defined numbers below the scale.")
    config.set("scale", "number_size", "32")

    config.add_section("devices")
    config.set("devices", "# Whether to send a signal to trigger a 'QST.LAB TCS2' thermode when the eVAS is recording. Only works on Windows. Should be: True/False")
    config.set("devices", "trigger_thermode", "False")
    config.set("devices", "# Moving the slider not only when the button is released, but also while the button is held down. Should be: True/False")
    config.set("devices", "move_while_down", "False")
    config.set("devices", "# Whether to use the mouse (slider does not move with keys anymore). Should be: True/False")
    config.set("devices", "use_mouse", "False")
    config.set("devices", "# Whether to update only on mouse click (only has an effect if 'use_mouse' is 'True'). Should be: True/False")
    config.set("devices", "on_click", "False")

    config.add_section("keys")
    config.set("keys", "# The following section is used to defined the keys.")
    config.set("keys", "# Keys code names can be found under: 'https://pynput.readthedocs.io/en/latest/keyboard.html'")
    config.set("keys", "")
    config.set("keys", "# Keys to start the recording.")
    config.set("keys", "keys_start", "[Key.space]")
    config.set("keys", "# Keys to end the application.")
    config.set("keys", "keys_end", "[Key.esc, Key.end]")
    config.set("keys", "# Keys to move the slider left.")
    config.set("keys", "keys_left", "[Key.left, Key.page_up]")
    config.set("keys", "# Keys to move the slider right.")
    config.set("keys", "keys_right", "[Key.right, Key.page_down]")

    config.add_section("appearance")
    config.set("appearance", "# Whether to load an image as slider background. Image must be placed in the same directory and called 'image'. Should be: True/False")
    config.set("appearance", "use_image", "False")
    config.set("appearance", "# Whether to load an image and place it above the slider. Image must be placed in the same directory and called 'upper_image'. Should be: True/False")
    config.set("appearance", "use_upper_image", "False")
    config.set("appearance", "# Width of the slider")
    config.set("appearance", "slider_width", "31")
    config.set("appearance", "# Height of the slider")
    config.set("appearance", "slider_height", "138")
    config.set("appearance", "# Color of the slider. Should be in form (R,G,B). Colors can be found under: 'https://redketchup.io/color-picker'")
    config.set("appearance", "slider_color", "(0,0,0)")
    config.set("appearance", "# Background color left")
    config.set("appearance", "left_color", "(192,192,192)")
    config.set("appearance", "# Background color right")
    config.set("appearance", "right_color", "(64,64,64)")
    config.set("appearance", "# Background color mid. Can also be disabled with 'None'.")
    config.set("appearance", "mid_color", "None")
    config.set("appearance", "# Height of the line the slider moves on.")
    config.set("appearance", "line_height", "128")
    config.set("appearance", "# Use a triangle instead of a square for the background. Should be: True/False.")
    config.set("appearance", "use_triangle", "False")
    config.set("appearance", "# Use a decreasing and an increasing triangle instead of a square for the background. Should be: True/False.")
    config.set("appearance", "use_two_triangle", "False")
    config.set("appearance", "# Welcome message that is displayed at the beginning. Should be list of Strings. Each element of the list is separated by a line break.")
    config.set("appearance", "welcome_message", '[f"Press {get_key_string(self.keys_start)} to start.", f"You can configure {config_file_name} to change the eVAS.", f"The application can be exited at any time by pressing {get_key_string(self.keys_end)}."]')
    config.set("appearance", "# Whether to hide the slider until first user interaction. Should only be used with 'use_mouse' set to 'True'. Should be: True/False.")
    config.set("appearance", "hide_slider", "False")

    config.add_section("csv")
    config.set("csv", "# Delimiter used in the CSV output file, for example ';'.")
    config.set("csv", "delimiter", ";")
    config.set("csv", "# Decimal point used in the CSV output file, for example ','.")
    config.set("csv", "decimal_point", ",")
    config.set("csv", "# Number of digits after the decimal point for the slider values saved.")
    config.set("csv", "decimal_places", "4")
    config.set("csv", "# Whether to save the used config at the beginning of the CSV file.")
    config.set("csv", "save_config_in_csv", "False")

    return config

def write_config(config, config_file_name=config_file_name):
    """Writes a given config to a file at the current path of the script/application.

    Args:
        config (ConfigParser): The config that should be written to a file.
        config_file_name (str, optional): Name of the output file. Defaults to config_file_name.
    """
    with open(os.path.join(current_path, config_file_name), 'w', encoding='utf-8') as fp:
        config.write(fp)

def read_config(config_file_name=config_file_name):
    """Reads a config from a file at the current path of the script/application.

    Args:
        config_file_name (str, optional): name of the config file. Defaults to config_file_name.

    Returns:
        ConfigParser: The loaded configuration.
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(os.path.join(current_path, config_file_name), encoding='utf-8')

    return config

def eval_config(config):
    """Evaluates a given configuration. 
    First entries that are in the "default" configuration but missing in the given one are filled.
    Next simplistic checks are performed to ensure the correctness of the config.

    Args:
        config (ConfigParser): The config to check.

    Returns:
        ConfigParser: Updated config.
    """

    try:
        generic_config = create_config()

        # check if all elements are present
        new_config = configparser.ConfigParser(allow_no_value=True)
        new_config.optionxform = str
        
        for section in generic_config:
            if section == "DEFAULT":
                continue
            new_config.add_section(section)
            for entry in generic_config[section]:
                if (len(entry) == 0):
                    continue
                if (entry.startswith("#")):
                    new_config.set(section, entry)
                    continue
                if not config.has_option(section, entry):
                    new_config.set(section, entry, generic_config[section][entry])
                    continue
                new_config.set(section, entry, config[section][entry])

        config = new_config
        write_config(config= config)

        range =  eval(config["scale"]["range"])
        start_value =  eval(config["scale"]["start"])

        if type(range)!=list or len(range) != 2:
            message(showinfo, 
                title="eVAS: Warning", 
                message=f"Range should be a list with two entries but is '{range}'. " +
                         "Fix or delete the '{config_file_name}' file.")
            sys.exit()
        if range[0] >= range[1]:
            message(showinfo, 
                title="eVAS: Warning", 
                message=f"First element of range should be smaller than second value, " +
                         "but are '{range[0]}' and '{range[1]}'. " +
                         "Fix or delete the '{config_file_name}' file.")
            sys.exit()
        if start_value < range[0] or start_value > range[1]:
            message(showinfo, 
                title="eVAS: Warning", 
                message=f"Start value should be in-between range, " +
                         "but is '{start_value}' with range '{range[0]}' and '{range[1]}'. " +
                         "Fix or delete the '{config_file_name}' file.")
            sys.exit()
        return config
    except Exception as e:
        throw_config_error(e)

#################################################################################################################
# CoVAS
class Covas(tk.Frame):
    def __init__(self, callback, master=None, *args, **kwargs):

        on_click = eval(config["devices"]["on_click"])
        # set a visible cursor if interact by mouse click, otherwise set cursor invisible
        cursor = "target" if on_click else "none"
        super().__init__(master, cursor= cursor, background="white")
        self.pack(fill=BOTH, expand=True)
        self.focus_set()
        self.callback = callback

        self.slider = Slider(self, callback= callback, *args, **kwargs)
        self.slider.pack(side='top', expand=True, fill=X, padx=10, pady=10)
        self.slider.grab_set()

    def update(self):
        self.slider.update_slider()
        return super().update()

# constants for placement
xpad, ypad, gradh, gradfac, linefac, textfac, sliderfac = .1, .1, .2, .75, 1.2, .5, 1.15

class Slider(tk.Canvas):
    def __init__(self, master=None, *, callback=None):
        '''callback is called with the slider's value as sole parameter. value is kept in [0,1] to accommodate for possibly changing scales.'''

        super().__init__(master, highlightthickness=0, background='#FFFFFF', height=800)

        # config
        try:
            self.sampling_rate = eval(config["general"]["sampling_rate"])
            self.only_on_change = eval(config["general"]["only_on_change"])

            self.range = eval(config["scale"]["range"])
            self.start_value = eval(config["scale"]["start"])
            self.labels = eval(config["scale"]["anchors"])
            self.label_size = eval(config["scale"]["label_size"])
            self.numbers = eval(config["scale"]["numbers"])
            self.number_size = eval(config["scale"]["number_size"])
            self.vertical_line_height = eval(config["scale"]["vertical_line_height"])
            self.step_size = eval(config["scale"]["step_size"])

            self.use_mouse = eval(config["devices"]["use_mouse"])
            self.move_while_down = eval(config["devices"]["move_while_down"])
            self.trigger_thermode = eval(config["devices"]["trigger_thermode"])
            self.on_click = eval(config["devices"]["on_click"])

            self.keys_start = eval(config["keys"]["keys_start"])
            self.keys_end = eval(config["keys"]["keys_end"])
            if Key.esc not in self.keys_end:
                self.keys_end.append(Key.esc)
            self.keys_left = eval(config["keys"]["keys_left"])
            self.keys_right = eval(config["keys"]["keys_right"])

            self.use_image = eval(config["appearance"]["use_image"])
            self.use_upper_image = eval(config["appearance"]["use_upper_image"])
            self.left_color = eval(config["appearance"]["left_color"])
            self.right_color = eval(config["appearance"]["right_color"])
            self.mid_color = eval(config["appearance"]["mid_color"])
            self.line_height = int(eval(config["appearance"]["line_height"]))
            self.use_triangle = eval(config["appearance"]["use_triangle"])
            self.use_two_triangle = eval(config["appearance"]["use_two_triangle"])
            self.slider_width = eval(config["appearance"]["slider_width"])
            self.slider_height = eval(config["appearance"]["slider_height"])
            self.slider_color = eval(config["appearance"]["slider_color"])
            self.welcome_message = "\n".join(eval(config["appearance"]["welcome_message"]))
            self.hide_slider = eval(config["appearance"]["hide_slider"])
        except Exception as e:
            throw_config_error(e)

        # generic init
        self.master = master
        self.w, self.h = None, None
        self.callback = callback
        self.started = False
        self.slider_value = self.start_value

        self.bind('<Configure>', self.update_size)

        if self.use_mouse:
            if self.on_click:
                self.bind('<ButtonRelease-1>', self.update_mouse)
            else:
                self.bind('<Motion>', self.update_mouse)

        if (self.trigger_thermode) and (sys.platform == 'win32'):
            self.com = get_com(self.master.master)

        #-------------------------------------------------------------------------------------------------------
        # KeyMonitor class
        #-------------------------------------------------------------------------------------------------------
        class KeyMonitor():
            def __init__(self, key_press_function, key_release_function):
                super().__init__()
                self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
                self.key_release_fun = key_release_function
                self.key_press_fun = key_press_function

            def on_press(self, key):
                self.key_press_fun(key)

            def on_release(self, key):
                self.key_release_fun(key)

            def stop_monitoring(self):
                self.listener.stop()

            def start_monitoring(self):
                self.listener.start()

        monitor = KeyMonitor(key_press_function=self.key_press, key_release_function=self.key_release)
        monitor.start_monitoring()

    def get_image_path(self, pattern= "image.*"):
        """Finds paths for files with the given pattern and returns the first one.
        If no paths are found, ends the eVAS and creates a user warning.

        Args:
            pattern (str, optional): Pattern to find files. Defaults to "image.*".

        Returns:
            str: Path to the first found element.
        """
        images = glob.glob(pattern)
        if len(images) == 0:
            if "vas" in globals():
                vas.end()
            message(showinfo, 
                title="eVAS: Warning", 
                message=f"You configured to load an image as background in the '{config_file_name}' file but none was found. " +
                         "Either update the config file or place an image called '{pattern}' in the same directory of the application.")
            sys.exit()
        return images[0]

    def update_size(self, event):
        w,h = event.width, event.height
        if (w,h) == (self.w,self.h):
            return
        self.w, self.h = w,h

        # visualize the slider background
        self.delete('all')
        self.gradient_w, gradient_h = int(w*(1-2*xpad)+.5), self.line_height
        gradient_y = h*(ypad+(1-2*ypad))*gradfac
        if self.use_image:
            image_path = self.get_image_path()
            im = PIL.Image.open(image_path)
            gradient_img = im.resize((self.gradient_w, gradient_h), PIL.Image.Resampling.BILINEAR)
        else:
            if self.mid_color is None:
                gradient_img = PIL.Image.new('RGB', (2,1))
                pixel = gradient_img.load()
                pixel[0,0] = self.left_color
                pixel[1,0] = self.right_color
            else:
                gradient_img = PIL.Image.new('RGB', (3,1))
                pixel = gradient_img.load()
                pixel[0,0] = self.left_color
                pixel[1,0] = self.mid_color
                pixel[2,0] = self.right_color
            gradient_img = gradient_img.resize((self.gradient_w, gradient_h), PIL.Image.Resampling.BILINEAR)
        self.gradient_img_tk = PIL.ImageTk.PhotoImage(gradient_img, master=self)
        self.gradient_tk = self.create_image(w/2, gradient_y, anchor=CENTER, image=self.gradient_img_tk)

        # optionally, place an image above
        if self.use_upper_image:
            image_path = self.get_image_path(pattern="upper_image.*")
            im = PIL.Image.open(image_path)
            gradient_img = im.resize((w, 3*gradient_h), PIL.Image.Resampling.BILINEAR)
            self.upper_img_tk = PIL.ImageTk.PhotoImage(gradient_img, master=self)
            self.upper_tk = self.create_image(w/2, h/4, anchor=CENTER, image=self.upper_img_tk)

        semi_line_height = gradient_h*linefac/2
        xs = linspace(w*xpad, w*(1-xpad), 11)

        if self.use_two_triangle or self.use_triangle:
            mid_x = xs[len(xs)//2] # x value in the middle
            quart_w = (mid_x -xs[0]) // 2 # width of one quartile of the VAS
            y_0 = gradient_y - gradient_h//2 # y-coordinate where VAS gradient starts
            y_1 = gradient_y + gradient_h//2 # y-coordinate where VAS gradient ends

            if self.use_two_triangle:
                # --- Morin et al. 1998 „Pain Threshold“
                points = [mid_x, y_0, mid_x, y_1, mid_x+quart_w+quart_w, y_0]
                self.cut_out = self.create_polygon(points, fill='white')
                points = [mid_x, y_0, mid_x, y_1, mid_x-quart_w-quart_w, y_0]
                self.cut_out2 = self.create_polygon(points, fill='white')
            else:
                points = [mid_x-quart_w-quart_w, y_0, mid_x-quart_w-quart_w, y_1, mid_x+quart_w+quart_w, y_0]
                self.cut_out2 = self.create_polygon(points, fill='white')

        # visualize the labels with optional bars and numbers
        y2 = (1-textfac)*gradient_y+semi_line_height + textfac*h*(1-ypad)
        offset = 20
        for i, x, text in zip(linspace(start= self.range[0], stop= self.range[1], num=len(self.labels)), range(int(xs[0]), int(xs[-1]), int((xs[-1] -  xs[0]) // max((len(self.labels) - 1), 1)) - 1), self.labels):
            x += i 
            self.create_text(x, y2 + self.vertical_line_height + offset, text=text, font=('DejaVu',self.label_size), anchor=CENTER, justify='center', fill='black')
            # vertical lines
            y0,y1 = gradient_y-self.vertical_line_height, gradient_y+self.vertical_line_height
            self.create_line(*[x,y0, x,y1], fill='#000000', width=3)
            if self.numbers:
                value = str(round(i, 2)).rstrip('0').rstrip('.')
                self.create_text(x, y1 + offset, text= value, font=('DejaVu', self.number_size, 'bold'), anchor=N, fill='black')

        # create slider already if it should not be invisible at the start
        if not self.hide_slider:
            self.create_slider()

        # create welcome message text
        self.start_text_id = self.create_text(w//2, h//4, text=self.welcome_message, font=('DejaVu',32), anchor=CENTER, justify='center', fill='black')

    def create_slider(self):
        val = self.slider_value
        self.slider_img = PIL.Image.new('RGBA', (1,1), self.slider_color)
        self.slider_img = self.slider_img.resize((self.slider_width, self.slider_height), PIL.Image.Resampling.NEAREST)
        self.slider_img_tk = PIL.ImageTk.PhotoImage(self.slider_img, master=self)
        slider_x, slider_y = self.w*((1-val)*xpad+val*(1-xpad)), self.h*(ypad+(1-2*ypad))*gradfac
        self.slider_tk = self.create_image(slider_x, slider_y, anchor=CENTER, image=self.slider_img_tk)

    def key_release(self, key):
        """Function triggered on a key release.

        Args:
            key (Key): The released key.
        """
        # reduce crashes on mac os when caps lock is pressed
        if (sys.platform == "darwin") and (key == Key.caps_lock):
            time.sleep(0.05)
            return

        self.check_start(key)
        self.check_move(key)

    def key_press(self, key):
        """Function triggered on a key press.

        Args:
            key (Key): The pressed key.
        """
        # reduce crashes on mac os when caps lock is pressed
        if (sys.platform == "darwin") and (key == Key.caps_lock):
            time.sleep(0.05)
            return

        self.check_start(key)
        if self.move_while_down:
            self.check_move(key)

    def check_start(self, key):
        """Function to check whether the eVAS should be started.
        Evaluates whether the pressed key is in the ones to start the eVAS.
        If yes, optionally triggers the thermode and creates the callback thread.

        Args:
            key (Key): The pressed/released key.
        """
        if (key in self.keys_start):
            if not self.started:
                self.started = True
                self.start_time = time.time()

                def callback_thread(each_sec= self.sampling_rate):
                    start_time = time.time()
                    while (not self.only_on_change) and (self.master.master.running):
                        self.callback(self.slider_value, self.start_time)
                        time.sleep(each_sec - ((time.time() - start_time) % each_sec))

                if (self.trigger_thermode) and (sys.platform == 'win32'):
                    try:
                        send_start_trigger(self.com)
                        logging.info("trigger sent") 
                    except Exception as e:
                        print(f"Error while sending trigger: '{e}'")
                        logging.exception(e)

                x = threading.Thread(target= callback_thread)
                x.start()

    def check_move(self, key):
        """Function to check whether the slider should be moved upon key press.
        Ends the eVAS upon escape, does nothing when eVAS was not started and moves slider right/left upon key stroke.

        Args:
            key (Key): The pressed/released key.
        """
        if (key in self.keys_end):
            self.master.master.running = False

        if  not self.started:
            return

        if (key in self.keys_right or key in self.keys_left) and (not self.use_mouse):

            # get old value
            old_value = self.slider_value

            # +/- step_length + old_value -> new value
            step_length = self.step_size
            step = step_length if (key in self.keys_right) else -step_length
            new_value = old_value + step

            # clip to [0, 1]
            new_value = clip(value=new_value, min_value=self.range[0], max_value=self.range[1])

            # set value
            self.slider_value = new_value

            if self.only_on_change:
                self.callback(self.slider_value, self.start_time)

    def update_mouse(self, event):
        """Updates the slider on mouse move.

        Args:
            event (event): The mouse move event.
        """
        if  not self.started:
            return

        if not hasattr(self, 'slider_tk'):
            self.create_slider()

        # calculate new value depending on the mouse position in relation to the slide
        new_value = ((event.x - (self.w * xpad)) / self.gradient_w) * (self.range[1] - self.range[0]) + self.range[0]
        # clip the value to the allowed range
        new_value = clip(value=new_value, min_value=self.range[0], max_value=self.range[1])
        # limit the value to the allowed ranges - round to nearest multiple of 'step_size'
        self.slider_value = round(new_value / self.step_size) * self.step_size

        if self.only_on_change:
            self.callback(self.slider_value, self.start_time)

    def update_slider(self):
        """Visualize the slider movement.
        """

        normalized_val = (self.slider_value - self.range[0]) / (self.range[1] - self.range[0])

        # when the experiment just started
        if self.started and (self.start_text_id in self.find_all()):
            self.delete(self.start_text_id)

            # move cursor to location of slider
            x= int((self.w * xpad) + (self.gradient_w * normalized_val))
            y= int(self.master.master.winfo_height()//2)
            pyautogui.moveTo(x + self.master.master.monitor.x, y)

        # if the background and slider are not initialized
        if not hasattr(self, 'slider_tk') or not self.master.master.running:
            return

        # place the slider accordingly
        w,h,f = self.winfo_width(), self.winfo_height(), normalized_val
        slider_x, slider_y = w*((1-f)*xpad+f*(1-xpad)), h*(ypad+(1-2*ypad))*gradfac
        self.coords(self.slider_tk, slider_x, slider_y)

class vas_thread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.filename = current_path + os.sep + '{}_vas.csv'.format(datetime.now().strftime("%Y%m%d_%H%M%S"))

        try:
            # csv options
            self.delimiter = config["csv"]["delimiter"]
            self.decimal_point = config["csv"]["decimal_point"]
            self.decimal_places = int(config["csv"]["decimal_places"])
            self.save_config_in_csv = eval(config["csv"]["save_config_in_csv"])
        except Exception as e:
            throw_config_error(e)

    def run(self):

        @contextmanager
        def callback_context():

            with open(self.filename, 'w+') as f_output:
                assert f_output is not None

                if f_output.tell() == 0:
                    if self.save_config_in_csv:
                        with open(config_file_name) as f:
                            lines = f.readlines()
                            for line in lines:
                                f_output.write(line)

                    f_output.write(f'secs{self.delimiter}values\n')
                else:
                    f_output.write('\n')

                def callback(slider_value, start_time):

                    if slider_value is None or f_output.closed:
                        return

                    secs = str(round(time.time() - start_time, 2))
                    value = str(round(slider_value, self.decimal_places))
                    if self.decimal_point != ".":
                        secs = secs.replace(".", self.decimal_point)
                        value = value.replace(".", self.decimal_point)
                    f_output.write(f'{secs}{self.delimiter}{value}\n')

                yield callback

        # get information about screens
        monitors = get_monitors()
        monitor_index = -1 if eval(config["general"]["use_second_screen"]) else 0
        monitor = monitors[monitor_index]

        self.root = tk.Tk()
        self.root.title('eVAS')
        self.root.wm_attributes("-topmost", 1)
        self.root.running = True
        self.root.monitor = monitor

        # set an icon
        icon_path = f"{os.path.dirname(__file__)}/images/icon.png"
        icon_path = icon_path.replace("\\", "/")
        self.root.iconphoto(True, PIL.ImageTk.PhotoImage(file= icon_path))

        # bind window close to end function
        self.root.protocol("WM_DELETE_WINDOW", self.end)

        # set to fullscreen on the correct monitor 
        self.root.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+0")

        if sys.platform == 'win32':
            # remove 'upper bar with close, maximize and minimize options' and taskbar icon in windows
            self.root.overrideredirect(1)
        elif sys.platform == 'linux':
            # enter full screen mode
            self.root.attributes("-fullscreen", True)

        with callback_context() as callback:
            covas_frame = Covas(master= self.root, callback=callback)
            self.root.deiconify()
            self.root.update()

            while self.root.running:
                covas_frame.update_idletasks()
                covas_frame.update()
                # reduce (cpu) load in while loop
                time.sleep(1/50)

            self.end()

        # remove file if no data was saved
        remove = True
        for i, _ in enumerate(open(self.filename, 'r').readlines()):
            if i > 0:
                remove = False
                break
        if remove:
            os.remove(self.filename)

    def end(self):
        self.root.running = False
        try:
            self.root.update()
            self.root.destroy()
        except:
            pass

#################################################################################################################
# Update

def is_update_available():
    """Checks whether there is a new release on GitHub available.

    Returns:
        bool: Whether a new release is available.
    """
    try:
        # get info from the latest release from github
        response = requests.get("https://api.github.com/repos/gouverneurp/eVAS/releases/latest")
        # retrieve the version of the release
        server_version = response.json()["tag_name"]
        # compare to current version
        return version.parse(app_version) < version.parse(server_version)

    except Exception as e:
        print(f"Error while checking for update: '{e}'")
        logging.exception(e)
        return False

def perform_windows_update():
    """Function to automatically perform an update of the application on Windows.
    First, the newest version of the application is downloaded. 
    Next a batch script to, remove and replace the old application and start the new one is written.
    Eventually, the current instance is stopped and the batch script started.

    Application should stop and restart with the updated version.
    """
    # get latest application from github
    url = 'https://github.com/gouverneurp/eVAS/releases/latest/download/eVAS.exe'
    filename = 'eVAS_new.exe'
    urlretrieve(url, filename)

    # compiled file.exe can find itself by
    own_name = os.path.basename(sys.executable)

    # create script to to replace file
    update_script = "update.bat"
    f = open(update_script, "w")
    f.write(f'@echo off\n')
    f.write(f'echo "Performing eVAS update..." \n')
    f.write(f'timeout /t 3 /nobreak > NUL\n')
    f.write(f'del "{own_name}"\n')
    f.write(f'ren "{filename}" "{own_name}"\n')
    f.write(f'start "" "{own_name}"\n')
    f.write(f'del "{update_script}"\n')
    f.close()

    message(showinfo, 
            title="eVAS: Update", 
            message="Update downloaded. Application will perform update and restart now.")

    os.startfile(update_script)
    sys.exit()

def check_for_update():
    """Function to check if an update is available.
    Depending on the OS, an automated update or redirect to the download page is performed.
    """
    try:

        if is_update_available():

            if not sys.platform == 'win32':
                answer = message(askquestion, 
                    title="eVAS: update", 
                    message="An update is available! " +
                            "Automatic update is currently not supported for your Operating System. " +
                            "Do you want to open the download page?")
                if answer == 'yes':
                    webbrowser.open_new(url= "https://gouverneurp.github.io/evas.html")
                    sys.exit()
                return

            answer = message(askquestion, 
                    title="eVAS: update", 
                    message="An update is available!" +
                            " Do you want to update the application now?")
            if answer == 'yes':
                perform_windows_update()
                return
    except Exception as e:
        print("Error while updating")
        print(e)

#################################################################################################################    
# TK message boxes

def message(fun, **kwargs):
    """Function to create a TK messagebox for the user, return its value and delete the window afterwards.
    The TK window is set to the front and only the messagebox is displayed.
    
    In detail, the given function should be a 'tkinter.messagebox'.
    Kwargs are given to the call of the messagebox function.

    Args:
        fun (function): The TK messagebox to open.

    Returns:
        Return value of the TK messagebox call.

    Example:
        from tkinter.messagebox import showinfo
        message(showinfo, title="Test", message="Test")
    """
    # create tk window
    message_window = tk.Tk()
    # make the window topmost so the message is visible
    message_window.attributes('-topmost', True)
    # make the created TK window not visible
    message_window.withdraw()
    # set the logo
    icon_path = f"{os.path.dirname(__file__)}/images/icon.png"
    icon_path = icon_path.replace("\\", "/")
    message_window.iconphoto(True, PIL.ImageTk.PhotoImage(file= icon_path))
    # create window
    return_value = fun(**kwargs)
    # delete the window
    message_window.destroy()

    return return_value

#################################################################################################################    
@catch
def main():
    """Main function of the eVAS.

    Checks whether the appropriate rights are given under MacOS, if the app is already running,
    creates a default config file if none exists, reads and evaluates the config file, checks for updates,
    and eventually starts the eVAS.
    """

    # under MAC OS
    if sys.platform == "darwin":
        from mac_os import is_keyboard_verified, request_access, is_allowed_mac_version

        if not is_allowed_mac_version():
            message(showinfo, 
                    title="eVAS: Warning", 
                    message="Your MacOS version is too low. Should be above 10.15. Exiting...")
            return

        # check if the application is trusted and keyboard can be monitored
        if not is_keyboard_verified():

            answer = message(askquestion, 
                             title="eVAS: Warning", 
                             message="You need to add eVAS to the Accessibility and Input Monitoring apps and restart it. " +
                                     "Open the system preferences?")

            if answer == 'yes':
                request_access()

            answer = message(askquestion, 
                             title="eVAS: Warning", 
                             message="The application is exited as rights are missing. " +
                                     "Do you want to open a detailed tutorial page?")

            if answer == 'yes':
                webbrowser.open_new(url= "https://github.com/gouverneurp/eVAS/blob/main/tutorials/mac_not_trusted.md")
            return

    if is_already_running():
        message(showinfo, title="eVAS: Warning", message="An instance of the eVAS is already running. Please close it.")
        return

    global config
    # create a config file if none is existing
    if not os.path.isfile(os.path.join(current_path, config_file_name)):
        config = create_config()
        write_config(config= config)

    # read and check config
    config = read_config()
    config = eval_config(config)

    # check for updates: new releases on GitHub
    check_for_update()

    # start the vas
    global vas
    vas = vas_thread()
    vas.run()

if __name__ == '__main__':
    main()

    logging.shutdown()
    # clean up afterwards
    try_delete_log_file()