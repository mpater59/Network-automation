import socket
import netmiko.ssh_exception
import paramiko.buffered_pipe
import pymongo
import yaml
import os

from netmiko import ConnectHandler
import Devices_configuration.interfaces as interfaces
from Devices_configuration.ospf import ospf as ospf
from Devices_configuration.bgp import bgp as bgp
from Devices_configuration.vlanBridgeVxlan import vlan as vlan
from Devices_configuration.vlanBridgeVxlan import bridge as bridge
from Devices_configuration.vlanBridgeVxlan import vxlan as vxlan


cur_path = os.path.dirname(__file__) #
new_path = os.path.relpath('../database_env.yaml', cur_path)

stream = open(new_path, 'r')
db_env = yaml.load(stream, Loader=yaml.SafeLoader)

myclient = pymongo.MongoClient(f"mongodb://{db_env['DB address IP']}/")
mydb = myclient[f"{db_env['DB name']}"]
col_configs = mydb[f"{db_env['DB collection configuration']}"]


def devicesConfiguration(site, device, config, soft_config_change=False, expand=False):

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
        if device_temp["hostname"] == device and device_temp["site"] == site:
            selected_device = device_temp
            break

    commands = []
    active_config = False
    if soft_config_change is True:
        if col_configs.count_documents({"active": True, "hostname": device, "site": site}) > 0:
            active_config = True
        else:
            print(f"Active configuration not detected in the database for {device}!")

    device_connection = {
        "device_type": selected_device.get("machine type"),
        "ip": selected_device.get("ip address"),
        "username": selected_device.get("username"),
        "password": selected_device.get("password"),
        "secret": selected_device.get("secret"),
        "port": selected_device.get("port"),
        "verbose": True
    }

    db_config = None
    if active_config is True:
        query = {"active": True, "site": site, "hostname": device}
        if col_configs.count_documents(query) > 0:
            db_config = col_configs.find(query).sort("last update datetime", -1)[0].get("configuration")
        else:
            print(f"Couldn't find active configuration for {device} in DB!")

    # Commands for Cumulus VX virtual machines
    # hard configuration reset
    if active_config is False and expand is False:
        commands.append("net del all")
    # hostname configuration
    if config.get("hostname"):
        commands.append(f"net add hostname {config.get('hostname')}")
    # interfaces configuration
    for command_cli in interfaces.interfaces(config, db_config, expand):
        commands.append(command_cli)
    # loopback configuration
    for command_cli in interfaces.loopback(config, db_config, expand):
        commands.append(command_cli)
    # ospf configuration
    for command_cli in ospf(config, db_config, expand):
        commands.append(command_cli)
    # bgp configuration
    for command_cli in bgp(config, db_config, expand):
        commands.append(command_cli)
    # vlan configuration
    for command_cli in vlan(config, db_config, expand):
        commands.append(command_cli)
    # bridge configuration
    for command_cli in bridge(config, db_config, expand):
        commands.append(command_cli)
    # vxlan configuration
    for command_cli in vxlan(config, db_config, expand):
        commands.append(command_cli)
    # ending configuration
    commands.append("net commit")

    print(commands)

    for trial in range(5):
        try:
            connection = ConnectHandler(**device_connection)
            output = connection.send_config_set(commands)
            print(output)
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}")
        except socket.timeout:
            print(f"Timeout - {trial + 1}")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}")
