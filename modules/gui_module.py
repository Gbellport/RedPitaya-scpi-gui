# General library imports
from datetime import datetime as dt
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import numpy as np
import pickle
import json
import time
import sys
import os

# Custom module imports
sys.path.append(r'resources')
from palette import *
from paths import *
from pitaya_ssh import *


def get_time():
    return dt.now().strftime('%H:%M:%S')

def unitary_separator():
    return [sg.Text()]

def create_spacing(h=1, w=1):
    h, w = int(h), int(w)
    return sg.Text('', size=(w, h))

def generate_popup(msg):
    msg = '\n{}\n'.format(msg)
    sg.popup_ok(msg, no_titlebar=True, background_color=COLOR_POPUP, line_width=30)


class TabManager:
    """Manages tabs when in the GUI loop

    Arguments:
        n_rp : limit of devices able to connect in the current session
        rp_obj : rp manager instance
        window : GUI window instance

    Attributes:
        tracker : current and previous tab tracker
    """

    def __init__(self, rp_obj, window, gui_scale):
        self.rp_obj      = rp_obj
        self.window      = window
        self.gui_scale   = gui_scale
        self.tracker     = {'curr':None, 'prev':None}


    def manage_tabs(self, device, values):
        """Main tab managing function

        Arguments: 
            device : current device selected in connected devices window
        """
        
        stat = ''
        if device != [] and device is not None:
            self.tracker['curr'] = device
            if self.tracker['curr'] != self.tracker['prev']:

                self.update_items(device=device, values=values)

                stat = 'switch'

            self.tracker['prev'] = device

        return stat


    def update_items(self, device, values):
        """Updates all items in window when switching devices."""
        mac = self.rp_obj.connected_devices[device]['mac']
        path = SEL_DEVICE_PATH(mac)

        # # Update TOD items (table + plot) ======================================
        # tod_pps_plot(path=path, gui_scale=self.gui_scale)
        # all_tod_plot(gui_scale=self.gui_scale)
        # self.window['-TOD_TRIG_PLOT-'].update('{}/plots/tod_bars.png'.format(path))

        # # Update WR items ======================================================
        # self.window['-LOG_LINK-'].update(False)

        # # Update AWG items (parameters + plot) =================================
        # self.awg_obj.load_parameters(mac=mac)
        # self.awg_obj.update_params_in_window()
