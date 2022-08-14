import pymongo
import re
import yaml
import argparse

from datetime import datetime
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
        old_id = str(mycol.find({"active": True}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        update_condition_old = {'_id': ObjectId(f"{old_id}")}
        if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
            date = datetime.strptime(config_id, "%d/%m/%Y %H:%M:%S")
            config_id = date
            config = mycol.find({"date": config_id})[0].get("devices")
            update_condition_new = {"date": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            config = mycol.find({'_id': ObjectId(f"{config_id}")})[0].get("devices")
            update_condition_new = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of first parameter!")
    else:
        config = mycol.find({"status": "verified"}).sort("date", -1)[0].get("devices")
        document_id = str(mycol.find({"status": "verified"}).sort("date", -1)[0].get("_id"))
        update_condition_new = {'_id': ObjectId(f"{document_id}")}
    for key, value in config.items():
        device_exist = False
        for counter, device in enumerate(devices):
            if device.get("hostname") == value.get("hostname"):
                device_list.append(device)
                config_list.append(value)
                device_exist = True
                if soft_rollback is False:
                    config_list[counter]["hard clear config"] = True
                break
        if device_exist is False:
            if del_configs is True:
                device_list.append(device)
                config_list.append({"hard clear config": True})

    devicesConfiguration(device_list, config_list)

    values_old = {"$set": {"active": False}}
    db_update_old = mycol.update_one(update_condition_old, values_old)
    print(db_update_old.raw_result)
    values_new = {"$set": {"active": True}}
    db_update_new = mycol.update_one(update_condition_new, values_new)
    print(db_update_new.raw_result)


def stringToBool(string):
    string = string.lower()
    if string in ["true", "yes"]:
        string = True
        return string
    elif string in ["false", "no"]:
        string = False
        return string
    else:
        print("Entered parameter is not boolean!")
        exit()


parser = argparse.ArgumentParser()

parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID or date (dd/mm/YYYY HH:MM:SS) of configuration in DB")
parser.add_argument("-sr", "--soft_rollback", dest="soft_rollback", default=True,
                    help="Delete current configs on devices and then apply from DB")
parser.add_argument("-dc", "--del_configs", dest="del_configs", default=False,
                    help="Delete current config on devices that aren't in saved configuration from DB")

args = parser.parse_args()

if isinstance(args.soft_rollback, str):
    soft_rollback = stringToBool(args.soft_rollback)
else:
    soft_rollback = args.soft_rollback
if isinstance(args.del_configs, str):
    del_configs = stringToBool(args.del_configs)
else:
    del_configs = args.del_configs

configRollback(args.config_id, soft_rollback, del_configs)
