import socket
import netmiko.ssh_exception
import paramiko.buffered_pipe
from netmiko import ConnectHandler


def devicesConfiguration(devices_list, config_list):
    device_connection = []
    commands = []
    for (counter, device), config in zip(enumerate(devices_list), config_list):
        device_connection_temp = {
            "device_type": device.get("machine type"),
            "ip": device.get("ip address"),
            "username": device.get("username"),
            "password": device.get("password"),
            "secret": device.get("secret"),
            "port": device.get("port"),
            "verbose": True
        }
        device_connection.append(device_connection_temp)
        commands_temp = []
        # Commands for Cumulus VX virtual machines
        # hard configuration reset
        if config.get("hard clear config") is True:
            commands_temp.append("net del all")
        # hostname configuration
        if config.get("hostname"):
            commands_temp.append(f"net add hostname {config.get('hostname')}")
        # interfaces configuration
        if config.get("interfaces"):
            for interface in config.get("interfaces"):
                if config.get("interfaces").get(interface).get("ip address"):
                    for ipAddr in config.get("interfaces").get(interface).get("ip address"):
                        if ipAddr:
                            commands_temp.append(f"net add interface {interface} ip address {ipAddr}")
                if config.get("interfaces").get(interface).get("shutdown"):
                    commands_temp.append(f"net add interface {interface} link down")
                elif not config.get("interfaces").get(interface).get("shutdown"):
                    commands_temp.append(f"net del interface {interface} link down")
        # loopback configuration
        if config.get("loopback"):
            if config.get("loopback").get("ip address"):
                for ipAddr in config.get("loopback").get("ip address"):
                    commands_temp.append(f"net add loopback lo ip address {ipAddr}")
        # ospf configuration
        if config.get("ospf"):
            commands_temp.append("net add ospf")
            if config.get("ospf").get("router-id"):
                commands_temp.append(f"net add ospf router-id {config.get('ospf').get('router-id')}")
            if config.get("ospf").get("interfaces"):
                for interface in config.get("ospf").get("interfaces"):
                    if interface == "lo":
                        if config.get("ospf").get("interfaces").get(interface).get("area"):
                            area = config.get("ospf").get("interfaces").get(interface).get("area")
                            commands_temp.append(f"net add loopback {interface} ospf area {area}")
                        if config.get("ospf").get("interfaces").get(interface).get("passive interface"):
                            commands_temp.append(f"net add loopback {interface} ospf passive")
                        if config.get("ospf").get("interfaces").get(interface).get("passive interface ipv6"):
                            commands_temp.append(f"net add loopback {interface} ospf6 passive")
                        continue
                    if config.get("ospf").get("interfaces").get(interface).get("area"):
                        area = config.get("ospf").get("interfaces").get(interface).get("area")
                        commands_temp.append(f"net add interface {interface} ospf area {area}")
                    if config.get("ospf").get("interfaces").get(interface).get("passive interface"):
                        commands_temp.append(f"net add interface {interface} ospf passive")
                    if config.get("ospf").get("interfaces").get(interface).get("passive interface ipv6"):
                        commands_temp.append(f"net add interface {interface} ospf6 passive")
                    if config.get("ospf").get("interfaces").get(interface).get("network"):
                        commands_temp.append(f'net add interface {interface} ospf network \
    {config.get("ospf").get("interfaces").get(interface).get("network")}')
        # bgp configuration
        if config.get("bgp"):
            if config.get("bgp").get("as"):
                commands_temp.append(f'net add bgp autonomous-system {config.get("bgp").get("as")}')
                if config.get("bgp").get("router-id"):
                    commands_temp.append(f'net add bgp router-id {config.get("bgp").get("router-id")}')
                if config.get("bgp").get("neighbors"):
                    for neighbor in config.get("bgp").get("neighbors"):
                        if config.get("bgp").get("neighbors").get(neighbor).get("remote"):
                            commands_temp.append(f'net add bgp neighbor {neighbor} remote-as \
    {config.get("bgp").get("neighbors").get(neighbor).get("remote")}')
                        if config.get("bgp").get("neighbors").get(neighbor).get("update"):
                            commands_temp.append(f'net add bgp neighbor {neighbor} update-source \
    {config.get("bgp").get("neighbors").get(neighbor).get("update")}')
                        if config.get("bgp").get("neighbors").get(neighbor).get("activate evpn"):
                            commands_temp.append(f"net add bgp l2vpn evpn neighbor {neighbor} activate")
                        if config.get("bgp").get("neighbors").get(neighbor).get("rrc"):
                            commands_temp.append(f"net add bgp neighbor {neighbor} route-reflector-client")
                        if config.get("bgp").get("neighbors").get(neighbor).get("evpn rrc"):
                            commands_temp.append(f"net add bgp l2vpn evpn neighbor {neighbor} route-reflector-client")
                if config.get("bgp").get("advertise-all-vni"):
                    commands_temp.append("net add bgp l2vpn evpn advertise-all-vni")
        # vlan configuration
        if config.get("vlan"):
            for vlan in config.get("vlan"):
                if config.get("vlan").get(vlan).get("ip address"):
                    for ipAddr in config.get("vlan").get(vlan).get("ip address"):
                        commands_temp.append(f"net add vlan {vlan} ip address {ipAddr}")
        # bridge configuration
        if config.get("bridge"):
            if config.get("bridge").get("ports"):
                for port in config.get("bridge").get("ports"):
                    commands_temp.append(f"net add bridge bridge ports {port}")
            if config.get("bridge").get("vids"):
                for vid in config.get("bridge").get("vids"):
                    commands_temp.append(f"net add bridge bridge vids {vid}")
                    if config.get("bridge").get("vids").get(vid).get("bridge access"):
                        for interface in config.get("bridge").get("vids").get(vid).get("bridge access"):
                            commands_temp.append(f"net add interface {interface} bridge access {vid}")
        # vxlan configuration
        if config.get("vxlan"):
            if config.get("vxlan").get("vnis"):
                for vni in config.get("vxlan").get("vnis"):
                    if config.get("vxlan").get("vnis").get(vni).get("id"):
                        commands_temp.append(
                            f'net add vxlan {vni} vxlan id {config.get("vxlan").get("vnis").get(vni).get("id")}')
                    if config.get("vxlan").get("vnis").get(vni).get("bridge access"):
                        commands_temp.append(
                            f'net add vxlan {vni} bridge access {config.get("vxlan").get("vnis").get(vni).get("bridge access")}')
                    if config.get("vxlan").get("vnis").get(vni).get("bridge learning"):
                        commands_temp.append(f"net del vxlan {vni} bridge learning off")
                    else:
                        commands_temp.append(f"net add vxlan {vni} bridge learning off")
                    if config.get("vxlan").get("vnis").get(vni).get("local-tunnelip"):
                        commands_temp.append(f'net add vxlan {vni} vxlan local-tunnelip \
    {config.get("vxlan").get("vnis").get(vni).get("local-tunnelip")}')
                    if config.get("vxlan").get("vnis").get(vni).get("remoteip"):
                        for remoteip in config.get("vxlan").get("vnis").get(vni).get("remoteip"):
                            commands_temp.append(f'net add vxlan {vni} vxlan remoteip {remoteip}')
        # ending configuration
        if config.get("commit"):
            commands_temp.append("net commit")
        commands.append(commands_temp)

    for deviceCommands in commands:
        print(deviceCommands)

    for counter, device in enumerate(device_connection):
        for trial in range(5):
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
