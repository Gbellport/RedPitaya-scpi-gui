# General library imports
from scipy.interpolate import interp1d
import PySimpleGUI as sg
import numpy as np
import pickle
import json
import time
import sys
import os

# Custom module imports
sys.path.append(r'resources')
# import redpitaya_scpi as scpi
from palette import *
from paths import *

PITAYA_TIMEBASE            = 1/125e6
PITAYA_TIMEBASE_MULTIPLIER = 1
PITAYA_BUFFER_LENGTH       = 16384

INTERPOLATION_PATH = os.path.abspath('modules/resources/interpolation/probe_ao_interpolation_30dBm.pck')


def param_formatter(param, factor=1e-6, encode_or_decode='encode'):
    if encode_or_decode == 'encode':
        try:
            val, order = str(param).split('e')
        except:
            return str(param)
        order = order[1:]
        if order in ['04', '05', '06', '07', '08']:
            return str(float(val)*10**(6-float(order)))
    elif encode_or_decode == 'decode':
        return float(param) * factor


def param_field(param, key_n, unit='μs', default='', gui_scale='normal'):
    fs = {'normal':18, 'small':11, 'xsmall':10}[gui_scale]
    if default != '':
        default = param_formatter(default)
    return [
        sg.Text('   \u2022 {}:'.format(param), size=(20, 1), font=(GLOBAL_FONT, fs)),
        sg.InputText(default, size=(8, 1), justification='right', key='-AWG_PARAM_{}-'.format(key_n), font=(GLOBAL_FONT, fs)),
        sg.Text(unit, font=(GLOBAL_FONT, fs))
    ]


class AWGManager:
    """Manages AWG parameters for AWG tab depending on selected devices.
    
    Arguments:
        window : PySimpleGUI window object
        n_params : Number of parameters in use

    Attributes:
        params_dict : dictionary of parameters (real values and visual values)
    """

    def __init__(self, window, n_params=10):
        self.window = window
        self.n_params = n_params
        self.params_dict = self.load_parameters()


    def fetch_parameters_from_window(self, mac, values):
        """Fetches visual parameters from window."""
        visual_params = []
        for i in range(self.n_params):
            key = '-AWG_PARAM_{}-'.format(i)
            vis = float(values[key])
            visual_params.append(vis)

        self.param_dict['visual'] = visual_params
        # self.save_parameter(mac=mac)
        self.dict_visual_to_value(mac=mac)


    def update_params_in_window(self):
        """Updates visual parameters in window."""
        for i in range(self.n_params):
            key = '-AWG_PARAM_{}-'.format(i)
            self.window[key].update(self.param_dict['visual'][i])
    

    def dict_value_to_visual(self, mac):
        """Encodes values to visual parameters, updates and saves dictionary.

        Arguments:
            mac : mac address of device in use (for saving)
        """

        visual_params = []
        for val in self.param_dict['value']:
            vis = param_formatter(val)
            visual_params.append(vis)

        self.param_dict['visual'] = visual_params
        self._save_parameters(mac=mac)


    def dict_visual_to_value(self, mac, skip_i=[2, 5, 8, 9]):
        """Decodes visual parameters to values, updates and saves dictionary.

        Arguments:
            mac : mac address of device in use (for saving)
            skip_encoding : indices of parameters to not decode 
        """

        value_params = []
        for i, vis in enumerate(self.param_dict['visual']):
            if i not in skip_i:
                val = param_formatter(vis, encode_or_decode='decode')
            else: val = vis
            val = float('%.1e' % val)
            value_params.append(val)
        
        self.param_dict['value'] = value_params
        self._save_parameters(mac=mac)


    def _save_parameters(self, mac='default'):
        """Saves parameters to json file."""
        json_dict = json.dumps(self.param_dict)
        with open('{}/awg_dict.json'.format(SEL_DEVICE_PATH(mac)), 'w+') as f:
            f.write(json_dict)


    def load_parameters(self, mac='default'):
        """Loads AWG parameters from .json file."""
        with open('{}/awg_dict.json'.format(SEL_DEVICE_PATH(mac))) as f:
            self.param_dict = json.load(f)


    def load_parameters_from_file(self, path, mac):
        with open(path) as f:
            self.param_dict = json.load(f)
        self._save_parameters(mac=mac)


    def save_parameters_to_file(self, path):
        json_dict = json.dumps(self.param_dict)
        with open(path, 'w+') as f:
            f.write(json_dict)

class WaveGen:
    """Class to handle AWG when ready to send waveforms to pitaya.

    Arguments:
        pitaya_timebase : Timebase for selected decimation factor
        pitaya_timebase_mutl : Decimation factor
        pitaya_buffer_length : Buffer length

    Attributes:
        t_vec : Time vector to be used by redpitaya
        probe_waveform : Probe waveform (gaussian-like)
        control_waveform : Control waveform (square-like)
    """

    def __init__(self, pitaya_timebase=PITAYA_TIMEBASE, 
        pitaya_timebase_mult=PITAYA_TIMEBASE_MULTIPLIER, 
        pitaya_buffer_length=PITAYA_BUFFER_LENGTH):

        self.pitaya_timebase = pitaya_timebase
        self.pitaya_timebase_mult = pitaya_timebase_mult
        self.pitaya_buffer_length = pitaya_buffer_length

        self.t_vec = None 
        self.probe_waveform = None
        self.control_waveform = None


    def form_waveforms(self, parameters):
        """Creates waveforms necessary for AWG.
        
        Arguments:
            parameters : AWG parameters (from manager)
        """
        
        # Unpack parameters
        t_length        = parameters[0]
        storage_width   = parameters[1]
        storage_power   = parameters[2]
        storage_time    = parameters[3]
        retrieval_width = parameters[4]
        retrieval_power = parameters[5]
        probe_fwhm      = parameters[6]
        probe_position  = parameters[7]
        probe_height    = parameters[8]
        repetition      = int(parameters[9])

        self.t_vec = np.array([i * PITAYA_TIMEBASE for i in range(int(np.ceil(t_length / PITAYA_TIMEBASE)))])
    
        # Probe is a simple Gaussian defined by mean=probe_position and a FWHM of probe_fwhm
        self.probe_waveform = probe_height \
            * np.exp(-(self.t_vec - probe_position)**2/2 / (probe_fwhm / 2.35)**2) \
            * (self.t_vec <= probe_position)
        
        # Control will always start 1e-6 after the trigger to make sure you don't get a wraparound in the control (i.e.)
        # the control actually goes off at some point
        self.control_waveform = np.zeros(len(self.t_vec))
        self.control_waveform += (self.t_vec < 1e-6)
        self.control_waveform += (storage_power) * (self.t_vec >= 1e-6) \
            * (self.t_vec <= 1e-6 + storage_width)
        self.control_waveform += (retrieval_power) \
            * (self.t_vec >= 1e-6 + storage_width + storage_time) \
            * (self.t_vec <= 1e-6 + 1e-6 + storage_width + storage_time + retrieval_width)

        return self.t_vec, self.probe_waveform, self.control_waveform, repetition
        

    def waveforms_optical_to_ao(self):
        """Convert the waveforms you want to see optically into what 
        is needed by the AO."""
        
        # Probe optical to AO
        op_to_ao = pickle.load(open(INTERPOLATION_PATH, 'rb'))
        probe_ao = op_to_ao(self.probe_waveform)
        probe_ao[probe_ao < -1] = -1

        # Control optical to AO
        control_ao = 2*self.control_waveform-1
        
        return probe_ao, control_ao
    

    def waveform_to_pitaya(self, ip, repetition=1):
        probe_waveform_ao, control_waveform_ao = self.waveforms_optical_to_ao()

        rp = scpi.scpi(ip)

        ## Upload to pitaya
        # Reset to default state
        rp.tx_txt('GEN:RST')

        # Set function of output signal
        rp.tx_txt('SOUR1:FUNC ARBITRARY')
        rp.tx_txt('SOUR2:FUNC ARBITRARY')

        # set output amplitude and offset
        rp.tx_txt('SOUR1:VOLT 1')
        rp.tx_txt('SOUR1:VOLT:OFFS 0')
        rp.tx_txt('SOUR2:VOLT 1')
        rp.tx_txt('SOUR2:VOLT:OFFS 0')

        frequency_waveform = 1/self.t_vec[-1]

        ## Upload waveforms
        rp.tx_txt('SOUR1:TRAC:DATA:DATA ' + ','.join(map(str, probe_waveform_ao)))
        rp.tx_txt('SOUR1:FREQ:FIX ' + str(frequency_waveform))
        rp.tx_txt('SOUR2:TRAC:DATA:DATA ' + ','.join(map(str, control_waveform_ao)))
        rp.tx_txt('SOUR2:FREQ:FIX ' + str(frequency_waveform))

        # enable output
        rp.tx_txt('OUTPUT1:STATE ON')
        rp.tx_txt('OUTPUT2:STATE ON')

        rp.tx_txt('GEN:SYNC')

        rp.tx_txt('SOUR1:BURS:STAT BURST')
        rp.tx_txt('SOUR2:BURS:STAT BURST')

        rp.tx_txt(f'SOUR1:BURS:NCYC 1')
        rp.tx_txt(f'SOUR2:BURS:NCYC 1')

        if repetition > 1:
            rp.tx_txt(f'SOUR1:BURS:NOR {repetition}')
            rp.tx_txt(f'SOUR2:BURS:NOR {repetition}')
            rp.tx_txt('SOUR1:BURS:INT:PER 1')
            rp.tx_txt('SOUR2:BURS:INT:PER 1')

        rp.tx_txt('SOUR1:TRIG:SOUR EXT_PE')
        rp.tx_txt('SOUR2:TRIG:SOUR EXT_PE')

        rp.close()

        print('[!] AWG deployed.')


# =========================================================================== #
#   ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED   #
# =========================================================================== #


        # parameters = []
        # with open('{}/awg_params.txt'.format(SEL_DEVICE_PATH(mac))) as fp: 
        #     lines = fp.readlines() 
        #     for val in lines:
        #         val = val.split('\\')[0]
        #         parameters.append(float(val))
        # parameters[-1] = int(parameters[-1])

        # return parameters


# def save_params(values, window, filepath=CONFIG_PATH, skip_encoding=[]):
#     with open(filepath, 'r+') as file:
#         file.truncate(0)
#         lines = [values['-AWG_PARAM_{}-'.format(i)]+'\n' for i in range(10)]

#         # Save to .txt file
#         for i, line in enumerate(lines):
#             if i not in skip_encoding:
#                 line = param_formatter(line, encode_or_decode='decode')
#             lines[i] = '%.1e' % float(line)

#         lines = [line + '\n' for line in lines]
#         file.writelines(lines)

# OTHER WAYS TO GENERATE PROBE WAVEFORM
# probe_waveform = probe_height*np.exp(-(t_vec-probe_position)**2/2/(probe_fwhm/2.35)**2)
# probe_waveform = probe_height*np.exp(-np.abs(t_vec-probe_position)/(probe_fwhm/2.35))*(t_vec<=probe_position)


# default_awg = {"value":[1.5e-05, 1.0e-06, 1.0e+00, 7.0e-06, 2.5e-06, 1.0e+00, 
#                         1.0e-06, 1.1e-05, 1.0e+00, 1.0e+00], 
#                "visual":[15.0, 1.0, 1.0, 7.0, 2.5, 1.0, 1.0, 11.0, 1.0, 1.0]}