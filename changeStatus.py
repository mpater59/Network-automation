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


def changeStatus(status=None, config_id=None, config_update_date=None, site=None, devices=None, active=False):
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

    config_datetime = None
    if active is False:
        config_datetime = mycol.find({"site": site}).sort("config update date", -1)[0].get("config update time")

    selected_devices = []
    if devices is not None:
        split_devices = devices.split(',')
        for split_device in split_devices:
            for known_device in known_devices:
                if known_device["site"] == site and known_device["hostname"] == split_device:
                    if active is False:
                        query = {"site": site, "configuration.hostname": split_device,
                                 "config update time": config_datetime}
                        if mycol.count_documents(query) > 0:
                            selected_devices.append(known_device["hostname"])
                    else:
                        query = {"site": site, "configuration.hostname": split_device, "active": True}
                        if mycol.count_documents(query) > 0:
                            selected_devices.append(known_device["hostname"])
                    break
    else:
        for known_device in known_devices:
            if known_device["site"] == site:
                if active is False:
                    query = {"site": site, "configuration.hostname": known_device["hostname"],
                             "config update time": config_datetime}
                    if mycol.count_documents(query) > 0:
                        selected_devices.append(known_device["hostname"])
                else:
                    query = {"site": site, "configuration.hostname": known_device["hostname"], "active": True}
                    if mycol.count_documents(query) > 0:
                        selected_devices.append(known_device["hostname"])
                break

    if selected_devices == []:
        print("Can't find devices in this site!")
        exit()

    for selected_device in selected_devices:
        update_condition = None

        if status is None:
            status = "stable"
        if config_id is None:
            query = {"active": True, "site": site, "configuration.hostname": selected_device}
            conf_id = str(mycol.find(query, {"_id": 1}).sort("config update date", -1)[0].get("_id"))
            update_condition = {'_id': ObjectId(f"{conf_id}")}
        elif config_id is not None:
            if re.search("^[0-9a-f]{24}$", config_id):
                query = {'config id': ObjectId(f"{config_id}"), "site": site, "configuration.hostname": selected_device}
                if mycol.count_documents(query) > 0:
                    conf_id = str(mycol.find_one(query, {"_id": 1}).get("_id"))
                else:
                    conf_id = None
                    print("Couldn't find configuration with entered ID!")
                    exit()
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration set ID!")
                exit()
        elif config_update_date is not None:
            if re.search("\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}", config_update_date):
                date = datetime.strptime(config_update_date, "%d/%m/%Y %H:%M:%S")
                query = {"site": site, "configuration.hostname": selected_device, "config update date": date}
                if mycol.count_documents(query) > 0:
                    conf_id = str(mycol.find_one(query, {"_id": 1}).get("_id"))
                else:
                    conf_id = None
                    print("Couldn't find configuration with entered datetime!")
                    exit()
                update_condition = {'_id': ObjectId(f"{conf_id}")}
            else:
                print("Entered wrong format of configuration update date, enter dd/mm/YYYY HH:MM:SS!")
                exit()
        new_values = {"$set": {"status": status}}
        db_update = mycol.update_one(update_condition, new_values)
        print(db_update.raw_result)


parser = argparse.ArgumentParser()

parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Define status that will be inserted to DB for selected configuration")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID of configuration set in DB (optional)")
parser.add_argument("-dt", "--datetime", dest="config_update_date", default=None,
                    help="Datetime of configuration set in DB (optional)")
parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will set status for all devices in selected site)")
parser.add_argument("-oa", "--only_active", dest="active", default=False, action='store_true',
                    help="Change status only on active configuration (cannot be used with -id and -st flags)")

args = parser.parse_args()

changeStatus(args.status_text, args.config_id, args.config_update_date, args.site, args.device, args.active)
