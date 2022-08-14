import sys
import pymongo
import re
import argparse

from bson import ObjectId

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


def changeStatus(change_type, status=None, config_id=None):
    if change_type == "active":
        if status is None:
            status = True
        if config_id is None:
            config_id = str(mycol.find({"active": True}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+-\d+-\d+T\d+:\d+:\d+.\d+\+\d+:\d+", config_id):
            update_condition = {"date": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            update_condition = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of third parameter!")
    elif change_type == "status":
        if status is None:
            status = "verified"
        if config_id is None:
            config_id = str(mycol.find({"active": True}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+-\d+-\d+T\d+:\d+:\d+.\d+\+\d+:\d+", config_id):
            update_condition = {"date": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            update_condition = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of third parameter!")
    else:
        print("Entered wrong first parameter!")
        exit()
    newValues = {"$set": {"status": status}}
    dbUpdate = mycol.update_one(update_condition, newValues)
    print(dbUpdate.raw_result)


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
                    help="ID or date of configuration in DB")

args = parser.parse_args()

if isinstance(args.status, str):
    status = stringToBool(args.status)
else:
    status = args.status
if isinstance(args.config_id, str):
    config_id = stringToBool(args.config_id)
else:
    config_id = args.config_id

changeStatus(args.change_type, status, config_id)
