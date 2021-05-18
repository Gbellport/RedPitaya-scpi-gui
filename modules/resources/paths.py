import os

RESOURCES_PATH = os.path.abspath('modules/resources')
IMAGES_PATH    = '{}/images'.format(RESOURCES_PATH)

DEVICES_PATH     = os.path.abspath('modules/resources/devices')
DEVICE_DICT_PATH = os.path.abspath('modules/resources/rp_dict.json')

SEL_DEVICE_PATH   = lambda x: os.path.abspath('modules/resources/devices/{}'.format(x))

REMOTE_SSH_PATH       = '../home/jupyter/RedPitaya/qusync'
