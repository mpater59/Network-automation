import pymongo
import re
import argparse

from datetime import datetime

import yaml
from bson import ObjectId

myclient = pymongo.MongoClient("mongodb://192.168.1.11:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


stream = open("devices.yaml", 'r')
devicesTemp = yaml.load_all(stream, Loader=yaml.SafeLoader)
known_devices = []
for device in devicesTemp:
    known_devices.append(device)


def changeStatus(change_type, status=None, config_id=None, site=None, devices=None):
    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if mycol.count_documents(query) > 0:
            if devices is None:
                site_devices = []
                for known_device in known_devices:
                    if known_device.get("site") == site:
                        site_devices.append(known_device)
        else:
            print("Can't find devices in this site!")
            exit()

    if devices is not None:
        split_devices = devices.split(',')
        selected_devices = []
        for split_device in split_devices:
            for known_device in known_devices:
                if known_device["site"] == site and known_device["configuration"]["hostname"] == split_device:
                    selected_devices = known_device
                    break
    else:
        selected_devices = []
        for known_device in known_devices:
            if known_device["site"] == site:
                selected_devices.append(known_device["configuration"]["hostname"])

    if selected_devices == []:
        print("Can't find devices in this site!")
        exit()

    for selected_device in selected_devices:
        if change_type == "active":
            if status is None:
                status = True
            elif status in ["true", "yes"]:
                status = True
            elif status in ["false", "no"]:
                status = False
            else:
                print("Change type parameter is not boolean (true/yes or false/no)!")
                exit()
            if config_id is None:
                query = {"active": True, "site": site, "configuration.hostname": selected_device}
                config_id = str(mycol.find(query, {"_id": 1}).sort([("config update time", -1),
                                                                    ("creation date", -1)])[0].get("_id"))
            if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
                date = datetime.strptime(config_id, "%d/%m/%Y %H:%M:%S")
                config_id = date
                update_condition = {"creation date": config_id}
            elif re.search("^[0-9a-f]{24}$", config_id):
                update_condition = {'_id': ObjectId(f"{config_id}")}
            else:
                print("Entered wrong format of configuration ID!")
                exit()
            new_values = {"$set": {"active": status}}
        elif change_type == "status":
            if status is None:
                status = "verified"
            if config_id is None:
                query = {"active": True, "site": site, "configuration.hostname": selected_device}
                config_id = str(mycol.find(query, {"_id": 1}).sort([("config update time", -1),
                                                                    ("creation date", -1)])[0].get("_id"))
            if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
                date = datetime.strptime(config_id, "%d/%m/%Y %H:%M:%S")
                config_id = date
                update_condition = {"creation date": config_id}
            elif re.search("^[0-9a-f]{24}$", config_id):
                update_condition = {'_id': ObjectId(f"{config_id}")}
            else:
                print("Entered wrong format of configuration ID!")
                exit()
            new_values = {"$set": {"status": status}}
        else:
            print("Entered wrong first parameter!")
            exit()
        db_update = mycol.update_one(update_condition, new_values)
        print(db_update.raw_result)


parser = argparse.ArgumentParser()

parser.add_argument("-ct", "--change_type", dest="change_type",
                    help='Define what parameter will be changed in DB ("active" or "status")')
parser.add_argument("-s", "--status", dest="status", default=None,
                    help="Define status that will be inserted to DB for selected configuration")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID or creation date (dd/mm/YYYY HH:MM:SS) of configuration in DB")
parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")

args = parser.parse_args()

changeStatus(args.change_type, args.status, args.config_id, args.site, args.device)
