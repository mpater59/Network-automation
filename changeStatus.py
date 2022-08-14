import pymongo
import re
import argparse

from datetime import datetime
from bson import ObjectId

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


def changeStatus(change_type, status=None, config_id=None):
    if change_type == "active":
        if status is None:
            status = True
        elif status in ["true", "yes"]:
            status = True
        elif status in ["false", "no"]:
            status = False
        else:
            print("Change type parameter is not boolean!")
            exit()
        if config_id is None:
            config_id = str(mycol.find({"active": True}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
            date = datetime.strptime(config_id, "%d/%m/%Y %H:%M:%S")
            config_id = date
            update_condition = {"date": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            update_condition = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of configuration ID!")
            exit()
    elif change_type == "status":
        if status is None:
            status = "verified"
        if config_id is None:
            config_id = str(mycol.find({"active": True}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
            date = datetime.strptime(config_id, "%d/%m/%Y %H:%M:%S")
            config_id = date
            update_condition = {"date": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            update_condition = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of configuration ID!")
            exit()
    else:
        print("Entered wrong first parameter!")
        exit()
    new_values = {"$set": {"status": status}}
    db_update = mycol.update_one(update_condition, new_values)
    print(db_update.raw_result)


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

parser.add_argument("-ct", "--change_type", dest="change_type",
                    help='Define what parameter will be changed in DB ("active" or "status")')
parser.add_argument("-s", "--status", dest="status", default=None,
                    help="Define status that will be inserted to DB for selected configuration")
parser.add_argument("-id", "--config_id", dest="config_id", default=None,
                    help="ID or date (dd/mm/YYYY HH:MM:SS) of configuration in DB")

args = parser.parse_args()

changeStatus(args.change_type, args.status, args.config_id)
