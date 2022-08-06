import sys
import pymongo
import re

from bson import ObjectId

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]


def changeStatus(change_type, status=None, config_id=None):
    if change_type == "active":
        if status is None:
            status = True
        if config_id is None:
            config_id = str(mycol.find({}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+-\d+-\d+T\d+:\d+:\d+.\d+\+\d+:\d+", config_id):
            update_condition = {"time": config_id}
        elif re.search("^[0-9a-f]{24}$", config_id):
            update_condition = {'_id': ObjectId(f"{config_id}")}
        else:
            print("Entered wrong format of third parameter!")
    elif change_type == "status":
        if status is None:
            status = "verified"
        if config_id is None:
            config_id = str(mycol.find({}, {"_id": 1}).sort("date", -1)[0].get("_id"))
        if re.search("\d+-\d+-\d+T\d+:\d+:\d+.\d+\+\d+:\d+", config_id):
            update_condition = {"time": config_id}
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


if len(sys.argv) > 1:
    change_type = sys.argv[1]
else:
    print("Enter first parameter!")
    exit()
if len(sys.argv) > 2:
    status = sys.argv[2]
else:
    status = None
if len(sys.argv) > 3:
    config_id = sys.argv[3]
else:
    config_id = None
changeStatus(change_type, status, config_id)
