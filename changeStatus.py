import sys
import pymongo
import re

from bson import ObjectId

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

if re.search("\d+/\d+/\d+ \d+:\d+:\d+", config_id):
    updateCondition = {"time": config_id}
elif re.search("^[0-9a-f]{24}$", config_id):
    updateCondition = {'_id': ObjectId(f"{config_id}")}
else:
    print("First parameter has to be date with time with YYYY/MM/DD HH:MM:SS format or ID configuration in MongoDB!")
    exit()

"""
print("Select status to update:")
while True:
    print("1. Verified")
    print("2. Unverified")
    print("3. Other")
    print("4. Exit")
    choice = input("Enter choice: ")
    choice = choice.strip()

    if choice == 1:
        status = "verified"
        break
    elif choice == 2:
        status = "unverified"
        break
    elif choice == 3:
        status = input("Enter status: ")
        break
    elif choice == 4:
        exit()
    else:
        print("Entered wrong number!")
"""

newValues = {"$set": {"status": status}}
dbUpdate = mycol.update_one(updateCondition, newValues)
print(dbUpdate.raw_result)
