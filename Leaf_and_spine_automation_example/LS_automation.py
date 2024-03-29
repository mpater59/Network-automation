import socket

import netmiko.ssh_exception
import paramiko.buffered_pipe
import yaml
from netmiko import ConnectHandler

stream = open("config.yaml", 'r')
devicesTemp = yaml.load_all(stream, Loader=yaml.SafeLoader)
devices = []
for counter, device in enumerate(devicesTemp):
    print(f"Device {counter + 1}. - test:")
    devices.append(device)
    for key, value in device.items():
        print(key + " : " + str(value))
    print()

deviceConnection = []
commands = []
for counter, device in enumerate(devices):
    deviceConnectionTemp = {
        "device_type": device.get("machine type"),
        "ip": device.get("ip address"),
        "username": device.get("username"),
        "password": device.get("password"),
        "secret": device.get("secret"),
        "port": device.get("port"),
        "verbose": True
    }
    deviceConnection.append(deviceConnectionTemp)
    commandsTemp = []
    # Commands for Cumulus VX virtual machines
    # hard configuration reset
    if device.get("hard clear config"):
        commandsTemp.append("net del all")
    # hostname configuration
    if device.get("hostname"):
        commandsTemp.append(f"net add hostname {device.get('hostname')}")
    # interfaces configuration
    if device.get("interfaces"):
        for interface in device.get("interfaces"):
            if device.get("interfaces").get(interface).get("ip address"):
                for ipAddr in device.get("interfaces").get(interface).get("ip address"):
                    if ipAddr:
                        commandsTemp.append(f"net add interface {interface} ip address {ipAddr}")
            if device.get("interfaces").get(interface).get("shutdown"):
                commandsTemp.append(f"net add interface {interface} link down")
            elif not device.get("interfaces").get(interface).get("shutdown"):
                commandsTemp.append(f"net del interface {interface} link down")
    # loopback configuration
    if device.get("loopback"):
        if device.get("loopback").get("ip address"):
            for ipAddr in device.get("loopback").get("ip address"):
                commandsTemp.append(f"net add loopback lo ip address {ipAddr}")
    # ospf configuration
    if device.get("ospf"):
        commandsTemp.append("net add ospf")
        if device.get("ospf").get("router-id"):
            commandsTemp.append(f"net add ospf router-id {device.get('ospf').get('router-id')}")
        if device.get("ospf").get("interfaces"):
            for interface in device.get("ospf").get("interfaces"):
                if interface == "lo":
                    if device.get("ospf").get("interfaces").get(interface).get("area"):
                        area = device.get("ospf").get("interfaces").get(interface).get("area")
                        commandsTemp.append(f"net add loopback {interface} ospf area {area}")
                    if device.get("ospf").get("interfaces").get(interface).get("passive interface"):
                        commandsTemp.append(f"net add loopback {interface} ospf passive")
                    else:
                        commandsTemp.append(f"net del loopback {interface} ospf passive")
                    continue
                if device.get("ospf").get("interfaces").get(interface).get("area"):
                    area = device.get("ospf").get("interfaces").get(interface).get("area")
                    commandsTemp.append(f"net add interface {interface} ospf area {area}")
                if device.get("ospf").get("interfaces").get(interface).get("passive interface"):
                    commandsTemp.append(f"net add interface {interface} ospf passive")
                else:
                    commandsTemp.append(f"net del interface {interface} ospf passive")
                if device.get("ospf").get("interfaces").get(interface).get("network"):
                    commandsTemp.append(f'net add interface {interface} ospf network \
{device.get("ospf").get("interfaces").get(interface).get("network")}')
    # bgp configuration
    if device.get("bgp"):
        if device.get("bgp").get("as"):
            commandsTemp.append(f'net add bgp autonomous-system {device.get("bgp").get("as")}')
            if device.get("bgp").get("router-id"):
                commandsTemp.append(f'net add bgp router-id {device.get("bgp").get("router-id")}')
            if device.get("bgp").get("neighbors"):
                for neighbor in device.get("bgp").get("neighbors"):
                    if device.get("bgp").get("neighbors").get(neighbor).get("remote"):
                        commandsTemp.append(f'net add bgp neighbor {neighbor} remote-as \
{device.get("bgp").get("neighbors").get(neighbor).get("remote")}')
                    if device.get("bgp").get("neighbors").get(neighbor).get("update"):
                        commandsTemp.append(f'net add bgp neighbor {neighbor} update-source \
{device.get("bgp").get("neighbors").get(neighbor).get("update")}')
                    if device.get("bgp").get("neighbors").get(neighbor).get("activate evpn"):
                        commandsTemp.append(f"net add bgp l2vpn evpn neighbor {neighbor} activate")
                    if device.get("bgp").get("neighbors").get(neighbor).get("rrc"):
                        commandsTemp.append(f"net add bgp neighbor {neighbor} route-reflector-client")
                    if device.get("bgp").get("neighbors").get(neighbor).get("evpn rrc"):
                        commandsTemp.append(f"net add bgp l2vpn evpn neighbor {neighbor} route-reflector-client")
            if device.get("bgp").get("advertise-all-vni"):
                commandsTemp.append("net add bgp l2vpn evpn advertise-all-vni")
    # vlan configuration
    if device.get("vlan"):
        for vlan in device.get("vlan"):
            if device.get("vlan").get(vlan).get("ip address"):
                for ipAddr in device.get("vlan").get(vlan).get("ip address"):
                    commandsTemp.append(f"net add vlan {vlan} ip address {ipAddr}")
    # bridge configuration
    if device.get("bridge"):
        if device.get("bridge").get("ports"):
            for port in device.get("bridge").get("ports"):
                commandsTemp.append(f"net add bridge bridge ports {port}")
        if device.get("bridge").get("vids"):
            for vid in device.get("bridge").get("vids"):
                commandsTemp.append(f"net add bridge bridge vids {vid}")
                if device.get("bridge").get("vids").get(vid).get("bridge access"):
                    for interface in device.get("bridge").get("vids").get(vid).get("bridge access"):
                        commandsTemp.append(f"net add interface {interface} bridge access {vid}")
    # vxlan configuration
    if device.get("vxlan"):
        if device.get("vxlan").get("vnis"):
            for vni in device.get("vxlan").get("vnis"):
                if device.get("vxlan").get("vnis").get(vni).get("id"):
                    commandsTemp.append(f'net add vxlan {vni} vxlan id {device.get("vxlan").get("vnis").get(vni).get("id")}')
                if device.get("vxlan").get("vnis").get(vni).get("bridge access"):
                    commandsTemp.append(f'net add vxlan {vni} bridge access {device.get("vxlan").get("vnis").get(vni).get("bridge access")}')
                if device.get("vxlan").get("vnis").get(vni).get("bridge learning"):
                    commandsTemp.append(f"net del vxlan {vni} bridge learning off")
                else:
                    commandsTemp.append(f"net add vxlan {vni} bridge learning off")
                if device.get("vxlan").get("vnis").get(vni).get("local-tunnelip"):
                    commandsTemp.append(f'net add vxlan {vni} vxlan local-tunnelip \
{device.get("vxlan").get("vnis").get(vni).get("local-tunnelip")}')
                if device.get("vxlan").get("vnis").get(vni).get("remoteip"):
                    for remoteip in device.get("vxlan").get("vnis").get(vni).get("remoteip"):
                        commandsTemp.append(f'net add vxlan {vni} vxlan remoteip {remoteip}')
    # ending configuration
    if device.get("commit"):
        commandsTemp.append("net commit")
    commands.append(commandsTemp)

for deviceCommands in commands:
    print(deviceCommands)

for counter, device in enumerate(deviceConnection):
    for trial in range (3):
        try:
            connection = ConnectHandler(**device)
            output = connection.send_config_set(commands[counter])
            print(output)
            connection.disconnect()
            break
        except paramiko.buffered_pipe.PipeTimeout:
            print(f"Timeout - {trial + 1}")
        except socket.timeout:
            print(f"Timeout - {trial + 1}")
        except netmiko.ssh_exception.NetmikoTimeoutException:
            print(f"Timeout - {trial + 1}")
