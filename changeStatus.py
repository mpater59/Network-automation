import re
import pymongo
import argparse
import yaml
from bson import ObjectId
from datetime import datetime

myclient = pymongo.MongoClient("mongodb://192.168.1.11:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


stream = open("devices.yaml", 'r')
devicesTemp = yaml.load_all(stream, Loader=yaml.SafeLoader)
known_devices = []
for device in devicesTemp:
    known_devices.append(device)


def changeStatus(change_type="status", status=None, config_id=None, config_update_date=None, site=None, devices=None):
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
                if known_device["site"] == site and known_device["hostname"] == split_device:
                    selected_devices = known_device
                    break
    else:
        selected_devices = []
        for known_device in known_devices:
            if known_device["site"] == site:
                selected_devices.append(known_device["hostname"])

    if selected_devices == []:
        print("Can't find devices in this site!")
        exit()

    for selected_device in selected_devices:
        update_condition = None
        new_values = None
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
                conf_id = str(mycol.find(query, {"_id": 1}).sort("config update time", -1)[0].get("_id"))
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            elif config_id is not None:
                if re.search("^[0-9a-f]{24}$", config_id):
                    update_condition = {'_id': ObjectId(f"{config_id}")}
                else:
                    print("Entered wrong format of configuration set ID!")
                    exit()
            elif config_update_date is not None:
                if re.search("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", config_update_date):
                    date = datetime.strptime(config_update_date, "%d/%m/%Y %H:%M:%S")
                    update_condition = {"config update time": date}
                else:
                    print("Entered wrong format of configuration update date, enter dd/mm/YYYY HH:MM:SS!")
                    exit()
            new_values = {"$set": {"active": status}}
        elif change_type == "status":
            if status is None:
                status = "stable"
            if config_id is None:
                query = {"active": True, "site": site, "configuration.hostname": selected_device}
                conf_id = str(mycol.find(query, {"_id": 1}).sort("config update date", -1)[0].get("_id"))
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            elif config_id is not None:
                if re.search("^[0-9a-f]{24}$", config_id):
                    update_condition = {'_id': ObjectId(f"{config_id}")}
                else:
                    print("Entered wrong format of configuration set ID!")
                    exit()
            elif config_update_date is not None:
                if re.search("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", config_update_date):
                    date = datetime.strptime(config_update_date, "%d/%m/%Y %H:%M:%S")
                    update_condition = {"config update time": date}
                else:
                    print("Entered wrong format of configuration update date, enter dd/mm/YYYY HH:MM:SS!")
                    exit()
            new_values = {"$set": {"status": ObjectId(f"{config_id}")}}
        else:
            print('Select parameter to change ("active" or "status")!')
            exit()
        db_update = mycol.update_one(update_condition, new_values)
        print(db_update.raw_result)


parser = argparse.ArgumentParser()

parser.add_argument("-ct", "--change_type", dest="change_type", default="status",
                    help='Define what parameter will be changed in DB ("active" or "status"); Default "status"')
parser.add_argument("-s", "--status", dest="status", default=None,
                    help="Define status that will be inserted to DB for selected configuration")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID of configuration set in DB (optional)")
parser.add_argument("-dt", "--datetime", dest="config_update_date", default=None,
                    help="Datetime of configuration set in DB (optional)")
parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")

args = parser.parse_args()

changeStatus(args.change_type, args.status, args.config_id, args.config_update_date, args.site, args.device)
