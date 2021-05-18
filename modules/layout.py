# General library imports
from datetime import datetime as dt
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import numpy as np
import json
import time
import sys
import os

# Custom module imports
sys.path.append(r'resources')
from gui_module import *
from palette import *
from paths import *

# ========================================================================== #
#   MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN MAIN    #
# ========================================================================== #

def generate_main_tab(rp_obj, gui_scale='normal'):
    main_tab = [
        [create_spacing(h=1)],
        [sg.Column([
            [sg.Text('Pitya Name:'), sg.Input(size=(15, 1), key='-RP_NAME-')],
            [sg.Text('Pitaya IP:  '), sg.Input(size=(15, 1), key='-RP_IP-')],
            [create_spacing(h=1)],
            [sg.Button('Add', size=(12, 1), key='-RP_ADD-')]
         ], element_justification='c'),
         create_spacing(w={'normal':10, 'small':5, 'xsmall':5}[gui_scale]),
         sg.Column([
            [sg.Table(values               = rp_obj.get_device_list(), 
                      headings             = ['Name', 'IP', 'Status', 'short MAC'], 
                      col_widths           = [15, 15, 15, 15],
                      auto_size_columns    = False,
                      justification        = 'c',
                      hide_vertical_scroll = True,
                      selected_row_colors  = ('white', COLOR_ACCENT),
                      key                  = '-RP_TABLE-')],
         [create_spacing(h=1)],
         [sg.Button('Disconnect',  size=(12, 1), key='-RP_DISCONNECT-'),
          sg.Button('Connect',     size=(12, 1), key='-RP_CONNECT-'),
          sg.Button('Remove',      size=(12, 1), key='-RP_REMOVE-')]
        ], element_justification='c')]
    ]

    return sg.Tab('Main', main_tab, element_justification='c', key='-MAIN_TAB-')

# =========================================================================== #
#   ALL TOD ALL TOD ALL TOD ALL TOD ALL TOD ALL TOD ALL TOD ALL TOD ALL TOD   #
# =========================================================================== #

def generate_pinout_tab(gui_scale='normal'):

    pinout_tab = [
        [sg.Column([[sg.Image('{}/rp_extensions.png'.format(IMAGES_PATH))]], 
            element_justification='c')]
    ]

    return sg.Tab('PINOUT', pinout_tab, element_justification='c', key='-PINOUT_TAB-')


#==============================================================================#

def create_tabgroup(rp_obj, gui_scale='normal'):
    tabs = []
    
    # First create main tab and all TODs tab
    tabs.append(generate_main_tab(rp_obj, gui_scale))
    tabs.append(generate_pinout_tab(gui_scale))

    # Compile tabs to send to main file
    tabgroup = sg.TabGroup([tabs], 
                           tab_background_color      = COLOR_POPUP, 
                           selected_background_color = COLOR_LIGHT2,
                           title_color               = '#707070',
                           key                       = '-TABS-')
    return tabgroup

#==============================================================================#

def create_layout(rp_obj, gui_scale='normal'):
    logo_selec = [
        sg.Column([
            [sg.Text('RedPitaya\nSCPI GUI', font=(GLOBAL_FONT, 15, 'bold'))]
        ], element_justification='l'),
        create_spacing(w={'normal':35, 'small':17, 'xsmall':17}[gui_scale]),
        sg.Text('[ Ver. 0.1 - 06.01.2021 ]', font=(GLOBAL_FONT, 12), text_color='gray'),
        create_spacing(w={'normal':35, 'small':17, 'xsmall':17}[gui_scale]),
        sg.Column([
            [sg.Text('Connected\nRedPitaya\nSelector'),
             sg.Listbox(values           = rp_obj.connected_devices, 
                        select_mode      = 'SELECT_MODE_SINGLE',
                        background_color = COLOR_DARK,
                        text_color       = 'white',
                        size             = (15, 5),
                        no_scrollbar     = True,
                        key              = '-RP_LIST-')]
        ], element_justification='r')
    ]

    rp_tabs = [create_tabgroup(rp_obj=rp_obj, gui_scale=gui_scale)]
    
    time_row = [
        sg.Column([
            [sg.Text('Time (PC): '), 
             sg.Text('', size=(10, 1), key='-GUI_TIME-'),
            ]
        ], justification='r')
    ]

    # Define layout
    layout = [
        logo_selec,
        [create_spacing()],
        rp_tabs,
        time_row
    ]

    return layout

# =========================================================================== #
#   ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED   #
# =========================================================================== # create_spacing(w=8*gui_scale), 