import argparse
from Update_database.updateConfigurations import update

parser = argparse.ArgumentParser()

parser.add_argument("-st", "--site", dest="site", help="Name of site")
parser.add_argument("-d", "--device", dest="device", default=None,
                    help="Name of devices, separate with ',' (default parameter will update all devices in selected site)")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-nd", "--new_documents", dest="new_documents", default=False, action='store_true',
                    help="Force creating new documents in DB")

args = parser.parse_args()

update(args.site, args.device, args.status_text, args.new_documents)
