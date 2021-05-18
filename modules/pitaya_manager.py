# General library imports
from datetime import datetime as dt
import matplotlib.pyplot as plt
from distutils.dir_util import copy_tree
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
from gui_module import *
# import redpitaya_scpi as scpi


class RPManager:
    """Manages RedPitaya devices, both connected and not

    Arguments:
        window : pysimplegui window object

    Attributes:
        device_dict : dictionary of added devices + info
        connected_devices : list of connected devices
    """

    def __init__(self, window=None):
        self.window = window

        self.device_dict = self.get_device_dict()
        self.connected_devices = {}


    def get_device_dict(self, disconnect_all=True):
        """Gets dictionary of RedPitaya from .json file

        Arguments:
            disconnect_all : flag to change status all devices (used at startup)

        Returns:
            device_dict : dictionary of device
        """

        with open(DEVICE_DICT_PATH, 'r') as f:
            device_dict = json.loads(f.read())
        if disconnect_all:
            for k in list(device_dict.keys()):
                device_dict[k]['status'] = 'disconnected'
        return device_dict


    def add_device(self, name, ip):
        """Add device to dictionary and GUI

        Arguments:
            name : nickname for device
            ip : ip of device
        """

        # Handle no entry
        if name in ['', ' '] or ip in ['', ' ']:
            generate_popup('Please enter a Name and IP for the RedPitaya.')
            return None
        
        # Add entry to dictionary and save
        self.device_dict[name] = {'ip':ip, 'status':'disconnected', 'mac':''}
        self._save_device_dict()

        # Clear text in iput fields
        self.window['-RP_NAME-'].update(value='')
        self.window['-RP_IP-'].update(value='')

        # Update device table
        self.window['-RP_TABLE-'].update(self.get_device_list())


    def remove_device(self, index):
        """Remove device from dictionary 

        Arguments: 
            index : Index of device to be removed
        """

        key = list(self.device_dict.keys())[index]

        # First remove from connected list
        if self.device_dict[key]['status'] == 'connected':
            del self.connected_devices[self.connected_devices.index(key)]
            self.window['-RP_LIST-'].update(self.connected_devices)

        # Remove from dictionary
        del self.device_dict[key]
        self._save_device_dict()

        # Update device table
        self.window['-RP_TABLE-'].update(self.get_device_list())


    def change_device_status(self, index, status, ip=None):
        """Change status of selected device

        Arguments:
            index : Index of device to change status 
            status : New status
            ip : IP of device
        """

        key = list(self.device_dict.keys())[index]
        self._save_device_dict()

        if status == 'connected':
            self.device_dict[key]['status'] = status
            self._connect(name=key, ip=ip)
        
        elif status == 'disconnected':
            # Change status and delete from connected list
            self.device_dict[key]['status'] = status
            self._disconnect(name=key)
        
        # Update window to display changes
        self.window['-RP_LIST-'].update(self.connected_devices.keys())

        # Update table
        self.window['-RP_TABLE-'].update(self.get_device_list(with_mac=True))


    def _save_device_dict(self):
        """Save device_dict to json file
        """

        json_dict = json.dumps(self.device_dict)
        with open(DEVICE_DICT_PATH, 'w+') as f:
            f.write(json_dict)


    def get_device_list(self, just_keys=False, with_mac=False):
        """Gets list of RedPitayas (for table)

        Arguments:
            just_keys : 
        """
        # Get keys, return them if requested or empty array if none yet
        keys = list(self.device_dict.keys())
        if len(keys) == 0: return [['']*3]
        if just_keys: return list(self.device_dict.keys())

        # Create list of rps
        rp_list = []
        for k in keys: 
            if with_mac and k in self.connected_devices:
                mac = self.connected_devices[k]['mac']
            else:
                mac = ''
            entry = [k, self.device_dict[k]['ip'], self.device_dict[k]['status'], mac]
            rp_list.append(entry)
        return rp_list


    def get_device_by_index(self, index):
        return self.device_dict[list(self.device_dict.keys())[index]]


    def _connect(self, name, ip):
        """Connects selected device

        Arguments: 
            name : Nickname of device
            ip : IP of device
        """
        
        # Connect device and fetch MAC address
        ssh = PitayaSSH(ip=ip)
        ssh.connect()
        # Start SCPI server upon connection
        ssh.send_command('systemctl start redpitaya_scpi')
        mac = ssh.get_mac_address()
        print('Connected device with MAC extension {}'.format(mac))

        # Check if directory for device exists and if not, create
        if '{}'.format(mac) not in os.listdir(DEVICES_PATH):
            copy_tree('{}/default'.format(DEVICES_PATH), 
                      '{}/{}'.format(DEVICES_PATH, mac))
            print('[+] New device detected. Creating new set of files.')
        else:
            print('[!] Device in memory.')

        # Add device to connected devices
        self.connected_devices[name] = {'ssh':ssh, 'mac':mac}


    def _disconnect(self, name):
        """Disconnects selected device

        Arguments:
            name : Nickname of device to disconnect
        """
        # Disconnect ssh instance and remove from dictionary
        self.connected_devices[name]['ssh'].disconnect()
        del self.connected_devices[name]
