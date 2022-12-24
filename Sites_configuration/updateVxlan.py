# import re
import yaml
import pymongo

from Other.other import key_exists
# from Other.other import check_if_exists
from bson import ObjectId
from Sites_configuration.updateLeaf import get_neighbor_ports as leaf_ports

stream = open("database_env.yaml", 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]
stream.close()


def get_vxlan(site, device, config_db=None):
    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    selected_device = None
    for device_temp in devices_temp:
        if device_temp['hostname'] == device and device_temp['site'] == site \
                and device_temp['device information']['type'] == 'leaf':
            selected_device = device_temp
            break
    stream.close()
    if selected_device is None:
        print(f"Device {device} is not Leaf!")
        return

    if config_db is None:
        query = {"site": site, "device hostname": device, "active": True}
        if col_configs.count_documents(query) > 0:
            conf_id = str(col_configs.find(query).sort("last update datetime", -1)[0].get("_id"))
            get_condition = {'_id': ObjectId(f"{conf_id}")}
        else:
            print(f"Couldn't find device {device} in DB!")
            return
        config_db = col_configs.find_one(get_condition)

    ports = leaf_ports(selected_device, site, config_db['configuration'])

    vxlan = {}
    for port in ports:
        port_name = list(port.keys())[0]
        if 'vni' not in port[port_name]:
            continue

        vnis = port[port_name]['vni']
        vid = int(port[port_name]['vid'])

        for vni in vnis:
            if key_exists(vxlan, vni) is False:
                vxlan[int(vni)] = {}
                vxlan[int(vni)]['vid'] = vid
                vxlan[int(vni)]['ports'] = []
            if port_name not in vxlan[int(vni)]['ports']:
                vxlan[int(vni)]['ports'].append(port_name)

    return vxlan


def update_vxlan(site, device, vxlan_config, expand=False):
    result = {}

    stream = open("database_env.yaml", 'r')
    db_env = yaml.load(stream, Loader=yaml.SafeLoader)

    myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
    mydb = myclient[f"{db_env['DB name']}"]
    col_configs = mydb[f"{db_env['DB collection configuration']}"]
    stream.close()

    if site is None:
        print("Enter name of site!")
        exit()
    else:
        query = {"site": site}
        if col_configs.count_documents(query) == 0:
            print("Can't find this site in DB!")
            exit()

    stream = open("sites.yaml", 'r')
    sites_file = list(yaml.load_all(stream, Loader=yaml.SafeLoader))
    selected_site = None
    for site_file in sites_file:
        if site_file["name"] == site:
            selected_site = site_file
            break
    stream.close()

    query = {"device hostname": device, "site": site, "active": True}
    if col_configs.count_documents(query) > 0:
        db_config = col_configs.find(query).sort("last update datetime", -1)[0].get("configuration")
    else:
        print(f"Couldn't find active device {device} at site {site}!")
        return

    stream = open("devices.yaml", 'r')
    devices_temp = yaml.load_all(stream, Loader=yaml.SafeLoader)
    selected_device = None
    for device_temp in devices_temp:
        if device_temp["hostname"] == device and device_temp["site"] == site:
            selected_device = device_temp
            break
    stream.close()

    if selected_device is None:
        print(f"Couldn't fine device {device} at site {site}!")
        return

    # configure vxlan

    ports_taken = {}
    vids_taken = []
    vxlan_result = {}

    ports = leaf_ports(selected_device, site)

    for port in ports:
        port_name = list(port.keys())[0]
        if port_name not in ports_taken and 'vni' not in port[port_name]:
            ports_taken[port_name] = {}
        if 'vni' not in port[port_name]:
            continue

        if expand is True:
            vxlan_result = get_vxlan(site, selected_device['hostname'])
            for vxlan in vxlan_result:
                vni = int(vxlan)
                vids_taken.append(int(vxlan_result[vni]['vid']))
                for port_result in vxlan_result[vni]['ports']:
                    if port_result not in ports_taken:
                        ports_taken.update({port_result: {'vid': int(vxlan_result[vni]['vid'])}})

    for vxlan in vxlan_config:
        vni = int(vxlan)
        if 'vid' in vxlan_config[vni]:
            vids_taken.append(int(vxlan_config[vni]['vid']))

    for vxlan in vxlan_config:
        vni = int(vxlan)
        if vni not in vxlan_result:
            vxlan_result[vni] = {}

        # config vid
        if 'vid' not in vxlan_config[vni] and 'vid' not in vxlan_result[vni]:
            new_vid = 10
            while True:
                if new_vid > 4096:
                    print("Couldn't find free VID")
                    break
                if new_vid not in vids_taken:
                    vids_taken.append(new_vid)
                    vxlan_result[vni]['vid'] = new_vid
                    break
                new_vid += 10
        elif 'vid' in vxlan_config[vni]:
            new_vid = int(vxlan_config[vni]['vid'])
            if 'vid' in vxlan_result[vni]:
                for port in ports_taken:
                    if 'vid' in ports_taken[port] and int(ports_taken[port]['vid']) == int(vxlan_result[vni]['vid']):
                        ports_taken[port]['vid'] = new_vid
            vxlan_result[vni]['vid'] = new_vid
            if vxlan_config[vni]['vid'] in vids_taken:
                vids_taken.remove(vxlan_config[vni]['vid'])
        else:
            new_vid = int(vxlan_result[vni]['vid'])

        # config ports
        if 'ports' in vxlan_config[vni]:
            if 'ports' not in vxlan_result[vni]:
                vxlan_result[vni]['ports'] = []
            for port in vxlan_config[vni]['ports']:
                if port in ports_taken and 'vid' in ports_taken[port] and ports_taken[port]['vid'] != new_vid:
                    print(f"Port {port} has assigned different VID!")
                    continue
                elif port in ports_taken and 'vid' in ports_taken[port]:
                    if port not in vxlan_result[vni]['ports']:
                        vxlan_result[vni]['ports'].append(port)
                else:
                    vxlan_result[vni]['ports'].append(port)
                    ports_taken.update({port: {'vid': new_vid}})

    # config add ports
    for vxlan in vxlan_config:
        vni = int(vxlan)
        new_vid = vxlan_result[vni]['vid']
        if 'add ports' in vxlan_config[vni] or ('ports' not in vxlan_config[vni] and 'ports' not in vxlan_result[vni]):
            if 'ports' not in vxlan_result[vni]:
                vxlan_result[vni]['ports'] = []
            if 'add ports' in vxlan_config[vni]:
                add_ports = int(vxlan_config[vni]['add ports'])
                number_of_ports = len(vxlan_result[vni]['ports']) + add_ports
            else:
                add_ports = 1
                number_of_ports = len(vxlan_result[vni]['ports']) + add_ports
            for _ in range(add_ports):
                for x in range(selected_device['number of ports']):
                    if f'swp{x + 1}' in ports_taken and 'vid' in ports_taken[f'swp{x + 1}'] \
                            and ports_taken[f'swp{x + 1}']['vid'] == new_vid \
                            and f'swp{x + 1}' not in vxlan_result[vni]['ports']:
                        vxlan_result[vni]['ports'].append(f'swp{x + 1}')
                    if len(vxlan_result[vni]['ports']) == number_of_ports:
                        break
                if len(vxlan_result[vni]['ports']) < number_of_ports:
                    for x in range(selected_device['number of ports']):
                        if f'swp{x + 1}' not in ports_taken:
                            vxlan_result[vni]['ports'].append(f'swp{x + 1}')
                            ports_taken.update({f'swp{x + 1}': {'vid': new_vid}})
                        if len(vxlan_result[vni]['ports']) == number_of_ports:
                            break
                    if len(vxlan_result[vni]['ports']) < number_of_ports:
                        print(f"Couldn't find free ports for device {selected_device['hostname']}")

    for port in ports_taken:
        if 'vid' in ports_taken[port]:
            vid = int(ports_taken[port]['vid'])
            for vxlan in vxlan_result:
                vni = int(vxlan)
                if vxlan_result[vni]['vid'] == vid and port not in vxlan_result[vni]['ports']:
                    vxlan_result[vni]['ports'].append(port)

    for vxlan in vxlan_result:
        vni = int(vxlan)
        vxlan_result[vni]['ports'].sort()

    # prepare yaml config
    db_config['vxlan'] = {}
    db_config['vxlan']['vnis'] = {}
    db_config['bridge'] = {}
    if len(vxlan_result) == 0:
        result['config'] = db_config
        result['vxlan'] = vxlan_result
        return result
    db_config['bridge']['ports'] = []
    db_config['bridge']['vids'] = {}
    db_config['bridge']['bridge-vlan-aware'] = True

    vid_list = []
    for vid in db_config['bridge']['vids']:
        vid_list.append(vid)

    if selected_device['device information']['type'] == 'leaf':
        device_lo = f"1.1.{selected_site['site id']}.{100 + selected_device['device information']['id']}"
    else:
        print(f"Selected device {device} is not a Leaf!")
        return

    for vni in vxlan_result:
        vni_name = f'vni{vni}'
        vid = vxlan_result[vni]['vid']
        ports = vxlan_result[vni]['ports']

        db_config['vxlan']['vnis'][vni_name] = {}
        db_config['vxlan']['vnis'][vni_name]['bridge access'] = vid
        db_config['vxlan']['vnis'][vni_name]['id'] = vni
        db_config['vxlan']['vnis'][vni_name]['local-tunnelip'] = device_lo

        if vni_name not in db_config['bridge']['ports']:
            db_config['bridge']['ports'].append(vni_name)
        if vid not in vid_list:
            db_config['bridge']['vids'][vid] = {}
            db_config['bridge']['vids'][vid]['bridge access'] = []
            vid_list.append(vid)
        if vni_name not in db_config['bridge']['vids'][vid]['bridge access']:
            db_config['bridge']['vids'][vid]['bridge access'].append(vni_name)

        for port in ports:
            if port not in db_config['bridge']['ports']:
                db_config['bridge']['ports'].append(port)
            if port not in db_config['bridge']['vids'][vid]['bridge access']:
                db_config['bridge']['vids'][vid]['bridge access'].append(port)

    result['config'] = db_config
    result['vxlan'] = vxlan_result
    return result
