# General library imports
from datetime import datetime as dt
from threading import Thread
import numpy as np
import paramiko
import serial
import time
import sys
import os
import re

# Custom module imports
sys.path.append(r'resources')
from palette import *
from paths import *
# import redpitaya_scpi as scpi

class PitayaSSH:
    def __init__(self, ip):
        self.ip = ip
        self.ssh = None


    def connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.ip, username='root', password='root')


    def send_command(self, cmd, with_input=None):
        assert self.ssh is not None, 'SSH object is not connected.'
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        if with_input is not None:
            stdin.write(f'{with_input}\n')
        return stdin, stdout, stderr


    def download_file(self, local_filepath, filename, remote_filepath=REMOTE_SSH_PATH):
        assert self.ssh is not None, 'SSH object is not connected.'
        ftp_client = self.ssh.open_sftp()
        ftp_client.chdir(remote_filepath)
        ftp_client.get(filename, local_filepath)
        ftp_client.close()


    def upload_file(self, local_filepath, filename, remote_filepath=REMOTE_SSH_PATH):
        assert self.ssh is not None, 'SSH object is not connected.'
        ftp_client = self.ssh.open_sftp()
        ftp_client.chdir(remote_filepath)
        ftp_client.put(local_filepath, filename)
        ftp_client.close()


    def disconnect(self):
        self.ssh.close()
        self.ssh = None

    
    def get_mac_address(self):
        """Gets MAC address of connected device

        Used to address device after connecting to it

        Returns: 
            mac : MAC address of device
        """

        stdin, stdout, stderr = self.send_command(f'ip a | grep link/ether')
        mac = stdout.read()
        # Parse
        mac = '.'.join(mac.decode().split(' brd ')[0].split(':')[3:])

        return mac


# =========================================================================== #
#   ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED ARCHIVED   #
# =========================================================================== #
