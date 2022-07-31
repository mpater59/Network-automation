import sys
import pymongo
import re

myclient = pymongo.MongoClient("mongodb://192.168.1.21:9000/")
mydb = myclient["configsdb"]
mycol = mydb["configurations"]

for arg in sys.argv:
    print(arg)

if len(sys.argv) != 3:
    print("Enter two parameters!")
    exit()

config_id = sys.argv[1]
status = sys.argv[2]

if re.search("^[\d]/[\d]/[\d] [\d]:[\d]:[\d]$", config_id):
    updateCondition = {"time": config_id}
elif re.search("[0-9a-f]", config_id):
    updateCondition = {"_id": config_id}
else:
    print("First parameter has to be date with time with YYYY/MM/DD HH:MM:SS format or ID configuration in MongoDB!")
    exit()
newValues = {"$set": {"status": status}}
dbUpdate = mycol.update_many(updateCondition, newValues)
