import argparse
import pymongo
import yaml

from Sites_configuration.updateDevice import update_device
from Update_database.updateConfigurations import update
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports
from Other.other import key_exists
from Other.other import check_if_exists


stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def migrate_vni(source_site, source_device, destination_site, destination_device, ports=None, vnis=None, extend=False,
            status=None, soft_update=False):

    if ports is not None and vnis is not None:
        print("Can't use flags --ports and --vnis simultaneously!")
        exit()

    if source_site is None:
        print("Enter name of source site!")
        exit()
    else:
        query = {"site": source_site}
        if col_configs.count_documents(query) == 0:
            print(f"Can't find source site {source_site} in DB!")
            exit()

    if destination_site is None:
        print("Enter name of destination site!")
        exit()
    else:
        query = {"site": destination_site}
        if col_configs.count_documents(query) == 0:
            print(f"Can't find destination site {destination_site} in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    s_device = None
    d_device = None
    known_devices = []
    for device in devices_temp:
        if device["hostname"] == source_device and device["site"] == source_site:
            s_device = device
        elif device["hostname"] == destination_device and device["site"] == destination_site:
            d_device = device
        known_devices.append(device)
    stream.close()

    vxlan_migrate = []

    if key_exists(s_device, "vxlan") is False:
        print(f"Source device {source_device} doesn't have VxLAN configuration!")
        exit()

    if ports is not None:
        ports_vxlan = ports.split(',')
        ports_vxlan_temp = ports.split(',')
        for vxlan in s_device['vxlan']:
            if key_exists(vxlan, 'port'):
                if check_if_exists(vxlan['port'], ports_vxlan):
                    vxlan_migrate.append(vxlan)
                    ports_vxlan_temp.remove(vxlan['port'])
        if ports_vxlan_temp != []:
            print(f"Couldn't find these ports for source device {source_device}:")
            for port in ports_vxlan_temp:
                print(port)
    elif vnis is not None:
        vnis_vxlan = vnis.split(',')
        vnis_vxlan_temp = vnis.split(',')
        for vxlan in s_device['vxlan']:
            if key_exists(vxlan, 'vni'):
                if check_if_exists(str(vxlan['vni']), vnis_vxlan):
                    vxlan_migrate.append(vxlan)
                    if check_if_exists(str(vxlan['vni']), vnis_vxlan_temp) is True:
                        vnis_vxlan_temp.remove(str(vxlan['vni']))
        if vnis_vxlan_temp != []:
            print(f"Couldn't find these VNIs for source device {source_device}:")
            for vni in vnis_vxlan_temp:
                print(vni)
    else:
        for vxlan in s_device['vxlan']:
            vxlan_migrate.append(vxlan)

    if extend is False:
        d_device['vxlan'] = []
    elif key_exists(d_device, 'vxlan') is False:
        d_device['vxlan'] = []

    d_taken_vids = []
    for vxlan in d_device['vxlan']:
        if key_exists(vxlan, 'vid'):
            if check_if_exists(vxlan['vid'], d_taken_vids) is False:
                d_taken_vids.append(vxlan['vid'])

    s_taken_vids = []
    temp_s_taken_vids = []
    for vxlan in vxlan_migrate:
        if key_exists(vxlan, 'vid'):
                s_taken_vids.append(vxlan['vid'])
                temp_s_taken_vids.append(vxlan['vid'])

    multiple_vids = []
    for vid in s_taken_vids:
        if check_if_exists(vid, temp_s_taken_vids) is True:
            temp_s_taken_vids.remove(vid)
        if check_if_exists(vid, temp_s_taken_vids) is True:
            if check_if_exists(vid, multiple_vids) is False:
                multiple_vids.append(vid)

    for vxlan in vxlan_migrate:
        if key_exists(vxlan, 'vid') and check_if_exists(vxlan['vid'], multiple_vids) is False:
            vxlan.pop('vid', None)
            if key_exists(vxlan, 'port'):
                vxlan.pop('port', None)

    for vid in multiple_vids:
        new_vid = 10
        for vxlan in vxlan_migrate:
            if key_exists(vxlan, 'vid') and vxlan['vid'] == vid:
                while True:
                    if new_vid > 4096:
                        print("Couldn't find free VID")
                        break
                    if check_if_exists(new_vid, d_taken_vids) is False:
                        vxlan['vid'] = new_vid
                        if key_exists(vxlan, 'port'):
                            vxlan.pop('port', None)
                        break
                    new_vid += 10
        d_taken_vids.append(new_vid)

    for vxlan in vxlan_migrate:
        d_device['vxlan'].append(vxlan)

    selected_device = None
    for device in known_devices:
        if device['hostname'] == destination_device and device['site'] == destination_site:
            device['vxlan'] = d_device['vxlan']
            selected_device = device
            break

    with open("devices.yaml", "w") as stream:
        yaml.safe_dump_all(known_devices, stream, default_flow_style=False, sort_keys=False)

    update_device(destination_site, destination_device, soft_update)

    update(destination_site, destination_device, status)

    ports = leaf_ports(selected_device, destination_site)
    print(f"Configured ports for device {destination_device}; site {destination_site}")
    for port in ports:
        print(port)


parser = argparse.ArgumentParser()

parser.add_argument("-sst", "--source_site", dest="source_site", help="Name of source site")
parser.add_argument("-sd", "--source_device", dest="source_device", help="Name of source device")
parser.add_argument("-dst", "--destination_site", dest="destination_site", help="Name of destination site")
parser.add_argument("-dd", "--destination_device", dest="destination_device", help="Name of destination device")
parser.add_argument("-p", "--ports", dest="ports", default=None,
                    help="Name of switchports with VNI, separate with ',' (default parameter will migrate all known switchports with VNI from source device)")
parser.add_argument("-vx", "--vnis", dest="vnis", default=None,
                    help="Index of VNI, separate with ',' (default parameter will migrate all known VNIs from source device)")
parser.add_argument("-ex", "--extend", dest="extend", default=False, action='store_true',
                    help="Migrate new VNIs without deleting old VNIs from destination device")
parser.add_argument("-t", "--status_text", dest="status_text", default=None,
                    help="Text status that will be set for this update in DB")
parser.add_argument("-su", "--soft_update", dest="soft_update", default=False, action='store_true',
                    help="Apply change without deleting existing configuration on devices (default false)")

args = parser.parse_args()

migrate_vni(args.source_site, args.source_device, args.destination_site, args.destination_device, args.ports, args.vnis,
        args.extend, args.status_text, args.soft_update)
