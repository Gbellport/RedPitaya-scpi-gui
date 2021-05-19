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

# ========================================================================= #
#   PINOUT PINOUT PINOUT PINOUT PINOUT PINOUT PINOUT PINOUT PINOUT PINOUT   #
# ========================================================================= #

def generate_pinout_tab(gui_scale='normal'):

    pinout_tab = [
        [sg.Column([[sg.Image('{}/rp_extensions.png'.format(IMAGES_PATH))]], 
            element_justification='c')]
    ]

    return sg.Tab('Pinout Reference', pinout_tab, element_justification='c', key='-PINOUT_TAB-')

# =========================================================================== #
#   DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO DIO   #
# =========================================================================== #

def generate_dio_tab(gui_scale='normal'):
    dio_p_layout = []
    dio_n_layout = []
    n_dio = 8

    dio_format = lambda n, p: [
        sg.Combo(['', 'IN', 'OUT'], default_value='', readonly=True, enable_events=True, k=f'-DIO{n}_{p}_IN_OUT-'),
        sg.Text(f'DIO{n}_{p}'), 
        sg.Button('Set HIGH', visible=False, button_color='#59d47a', k=f'-DIO{n}_{p}_TOGGLE-'),
        sg.Column([
            [sg.Input('', disabled=True, size=(10, 1), disabled_readonly_background_color=COLOR_DARK, k=f'-DIO{n}_{p}_INPUT-'),
             sg.Text(f'V')]
            ], element_justification='l', visible=False, k=f'-DIO{n}_{p}_READING-')
    ]

    for n in range(0, n_dio):
        dio_p_entry = dio_format(n=n, p='P')
        dio_n_entry = dio_format(n=n, p='N')
        dio_p_layout.append(dio_p_entry)
        dio_n_layout.append(dio_n_entry)

    dio_tab = [
        [sg.Column(dio_p_layout, element_justification='l'),
         create_spacing(w=2),
         sg.VerticalSeparator(),
         create_spacing(w=2),
         sg.Column(dio_n_layout, element_justification='l')]
    ]

    return sg.Tab('DIO', dio_tab, element_justification='c', key='-DIO_TAB-')

# ========================================================================== #
#   SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW SLOW    #
# ========================================================================== #

def generate_slow_tab(gui_scale='normal'):
    slow_layout = []
    n_dio = 4

    slow_format = lambda n: [
        sg.Checkbox('', default=False, enable_events=True, k=f'-AO{n}_CHECKBOX-'),
        sg.Text(f'AO{n}'), 
        sg.Input('', size=(10, 1), disabled=True, disabled_readonly_background_color=COLOR_DARK, k=f'-AO{n}_OUTPUT-'),
        sg.Text(f'V'), 
        create_spacing(w=5),
        sg.Checkbox('', default=False, enable_events=True, k=f'-AI{n}_CHECKBOX-'),
        sg.Text(f'AI{n}'), 
        sg.Input('', disabled=True, size=(10, 1), disabled_readonly_background_color=COLOR_DARK, k=f'-AI{n}_INPUT-'),
        sg.Text(f'V'), 
    ]

    for n in range(0, n_dio):
        slow_entry = slow_format(n=n)
        slow_layout.append(slow_entry)

    slow_tab = [
        [sg.Column(slow_layout, 
            element_justification='c')]
    ]

    return sg.Tab('Slow Analogs', slow_tab, element_justification='c', key='-SLOW_TAB-')

#==============================================================================#

def create_tabgroup(rp_obj, gui_scale='normal'):
    tabs = []
    
    # First create main tab and all TODs tab
    tabs.append(generate_main_tab(rp_obj, gui_scale))
    tabs.append(generate_dio_tab(gui_scale))
    tabs.append(generate_slow_tab(gui_scale))
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
        sg.Text('[ Ver. 0.1 - 05.18.2021 ]', font=(GLOBAL_FONT, 12), text_color='gray'),
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
# =========================================================================== #  