import sys
import pymongo
import re
import yaml
import argparse

from bson import ObjectId
from Devices_configuration.devicesConfiguration import devicesConfiguration

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]

def configRollback(config_id=None, soft_rollback=True, del_configs=False):
    config_list = []
    device_list = []

    stream = open("knownDevices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    devices = []
    for counter, device in enumerate(devices_temp):
        devices.append(device)

    if config_id is not None:
        if re.search("\d+-\d+-\d+T\d+:\d+:\d+.\d+\+\d+:\d+", config_id):
            config = mycol.find({"date": config_id})[0].get("devices")
        elif re.search("^[0-9a-f]{24}$", config_id):
            config = mycol.find({'_id': ObjectId(f"{config_id}")})[0].get("devices")
        else:
            print("Entered wrong format of first parameter!")
    else:
        config = mycol.find({"status": "verified"}).sort("date", -1)[0].get("devices")
    for key, value in config.items():
        device_exist = False
        for counter, device in enumerate(devices):
            if device.get("hostname") == value.get("hostname"):
                device_list.append(device)
                config_list.append(value)
                device_exist = True
                if soft_rollback is False:
                    config_list[-1]["hard clear config"] = True
                break
        if device_exist is False:
            if del_configs is True:
                device_list.append(device)
                config_list.append({"hard clear config": True})

    devicesConfiguration(device_list, config_list)


parser = argparse.ArgumentParser()

parser.add_argument("-id", "--config_id", dest="config_id", default=None, help="ID or date of configuration in DB")
parser.add_argument("-sr", "--soft_rollback", dest="soft_rollback", default=True,
                    help="Delete current configs on devices and then apply from DB")
parser.add_argument("-dc", "--del_configs", dest="del_configs", default=False,
                    help="Delete current config on devices that aren't in saved configuration from DB")

args = parser.parse_args()

configRollback(args.config_id, args.soft_rollback, args.del_configs)
