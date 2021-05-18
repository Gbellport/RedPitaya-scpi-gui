# General library imports
import matplotlib.pyplot as plt
from threading import Thread
import PySimpleGUI as sg
import datetime as dt
import numpy as np
import subprocess
import webbrowser

import paramiko
import argparse
import time
import sys
import os

import warnings
if not sys.warnoptions:
    warnings.simplefilter('ignore')

# Custom module imports
sys.path.append(r'modules/resources')
sys.path.append(r'modules')
# from parameter_module import *
from pitaya_manager import *
from pitaya_ssh import *
from layout import *
from gui_module import *
from palette import *
from paths import *


# ============================================================================ #
#                              Argument Parser                                 #
# ============================================================================ #

# Parse command line arguments
parser = argparse.ArgumentParser(description='QuSync GUI')
parser.add_argument('--gui_scale', default='small', type=str, 
                    help='Control scale of GUI for various resolutions')
args = parser.parse_args()
gui_scale = args.gui_scale

# ============================================================================ #
#                  Initialize variables and objects                            #
# ============================================================================ #

RPMgr = RPManager()

# ============================================================================ #
#                         LAYOUT CONFIGURATION                                 #
# ============================================================================ #

GLOBAL_FONT_SIZE = {'normal':15, 'small':12, 'xsmall':10}[gui_scale]
sg.SetOptions(font=(GLOBAL_FONT, GLOBAL_FONT_SIZE))
sg.theme_add_new('GUI', GUI_theme)
sg.theme('GUI')

layout = create_layout(rp_obj=RPMgr, gui_scale=gui_scale)

# ============================================================================ #
#                     Start window, finalize objects                           #
# ============================================================================ #

# Create window and begin GUI loop
loc_h = {'normal':200, 'small':100, 'xsmall':100}[gui_scale]
loc_v = {'normal':40, 'small':20, 'xsmall':100}[gui_scale]
window = sg.Window('RP Control GUI', layout, grab_anywhere=False,
                   location=(loc_h, loc_v), finalize=True)

# Create/update objects
TabMgr = TabManager(
    rp_obj      = RPMgr, 
    window      = window, 
    gui_scale   = gui_scale)

RPMgr.window = window

# ============================================================================ #
#              Event handler (to use with multithreading)                      #
# ============================================================================ #

    # ============================================ #
    #              Main tab behaviour              #
    # ============================================ #

def main_tab_event_handler(event, values, ssh):
    global window
    global RPMgr
    global TabMgr

    if event == '-RP_ADD-':
        name = values['-RP_NAME-']
        ip = values['-RP_IP-']
        RPMgr.add_device(name=name, ip=ip)

    elif event == '-FORCE_SYNC-' and ssh is not None:
        stdin, stdout, stderr = ssh.send_command('python3 {}/wr_sync.py'.format(REMOTE_SSH_PATH))

    elif event in ['-RP_REMOVE-', '-RP_CONNECT-', '-RP_DISCONNECT-']:
        if values['-RP_TABLE-'] != []:
            # Index of selected entry on table (and entry)
            index = values['-RP_TABLE-'][0]
            entry = RPMgr.get_device_by_index(index)
            # Handle specific event
            if event == '-RP_REMOVE-':
                RPMgr.remove_device(index=index)
                TabMgr.close_all_tabs()
            elif event == '-RP_CONNECT-':
                RPMgr.change_device_status(index=index, status='connected', ip=entry['ip'])
            elif event == '-RP_DISCONNECT-':
                RPMgr.change_device_status(index=index, status='disconnected', ip=entry['ip'])
                TabMgr.close_all_tabs()
        else:
            pass
            generate_popup('First select a RedPitaya from the table.')


# ============================================================================ #
#                            Main GUI loop                                     #
# ============================================================================ #

device_ssh = None
print('[+] Initialized GUI.')
while True:
    event, values = window.read(timeout=10)
    # Update time on each iteration
    window['-GUI_TIME-'].Update(get_time())

    # Unpack necessary variables
    try:
        current_tab = values['-TABS-']
    except:
        break

    current_device = values['-RP_LIST-']
    if current_device != []:
        current_device = current_device[0]
        device_ssh = RPMgr.connected_devices[current_device]['ssh']
        device_mac = RPMgr.connected_devices[current_device]['mac']
        device_path = SEL_DEVICE_PATH(device_mac)

    # Open tabs based on selected device
    tab_status = TabMgr.manage_tabs(device=current_device, values=values)

    # ================== #
    #   General events   #
    # ================== #

    # Handle closing GUI  
    if event == sg.WIN_CLOSED:
        break


    # ============================================= #
    #              Main tabs behaviour              #
    # ============================================= #

    if current_tab == '-MAIN_TAB-':
        if event != [] and event != '__TIMEOUT__' and event is not None:
            #Thread(target=main_tab_event_handler, 
            #       args=(event, values)).start()
            main_tab_event_handler(event, values, device_ssh)


window.close()
print('[-] Closed GUI.')


# =========================================================================== #
#   ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED   #
# =========================================================================== #

# # WR TAB BEHAVIOR ============================================================
# if wr_err_c >= 4:
#     err = stderr.read()
#     if err.decode() not in ['', ' ', []]:
#         print('ERR: ', err)
#         print('restarting script...')
#         stdin, stdout, stderr = device_ssh.send_command('python3 {}/dt_wr_usb.py'.format(REMOTE_SSH_PATH))
#     else:
#         print('no errors...')
# wr_err_c += 1

# window[f'-WR_RT_HIST-'].update('{}/plots/histogram_rt.png'.format(device_path))
# window[f'-WR_SP_HIST-'].update('{}/plots/histogram_sp.png'.format(device_path))

# display_status_histograms(path=path, rt_data=rt_data, sp_data=sp_data)

# # TOD TAB BEHAVIOR ===========================================================