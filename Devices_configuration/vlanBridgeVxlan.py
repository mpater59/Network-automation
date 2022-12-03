from Other.other import key_exists
from Other.other import check_if_exists


def vlan(config, db_config=None, expand=False):
    commands = []

    # config vlan
    if key_exists(config, "vlan"):
        vlan_list = list(config["vlan"].keys())

        if key_exists(db_config, "vlan") and expand is False:
            for dbVlan in list(db_config["vlan"].keys()):
                if check_if_exists(dbVlan, vlan_list) is False:
                    commands.append(f"net del vlan {dbVlan}")
                    if key_exists(db_config, "vlan", dbVlan, "ip address"):
                        db_config["vlan"].pop(dbVlan)
                    if key_exists(db_config, "bridge", "vids", dbVlan, "bridge access") and \
                            key_exists(db_config, "bridge", "ports"):
                        for port in db_config["bridge"]["ports"]:
                            if check_if_exists(port, db_config["bridge"]["vids"][dbVlan]["bridge access"]):
                                db_config["bridge"]["ports"].remove(port)
                    if key_exists(db_config, "bridge", "vids", dbVlan, "bridge access"):
                        if key_exists(db_config, "vids", dbVlan):
                            db_config["vids"].pop(dbVlan)
                    if key_exists(db_config, "vxlan", "vnis"):
                        for vni in db_config["vxlan"]["vnis"]:
                            if db_config["vxlan"]["vnis"][vni]["id"] == dbVlan:
                                db_config["vxlan"]["vnis"][vni].pop("id")

        for vlan_id in config["vlan"]:
            vlan_config = config["vlan"][vlan_id]

            if key_exists(db_config, "vlan", vlan_id) and len(db_config["vlan"][vlan_id]) > 0:
                db_vlan_config = db_config["vlan"][vlan_id]
            else:
                db_vlan_config = None

            # config vlan id
            if db_vlan_config is None:
                commands.append(f"net add vlan {vlan_id}")

            # config ip address
            if key_exists(vlan_config, "ip address"):
                ip_address = vlan_config["ip address"]

                if key_exists(db_vlan_config, "ip address"):
                    db_ip_address = db_vlan_config["ip address"]
                    for dbIpAddr in db_ip_address:
                        if check_if_exists(dbIpAddr, ip_address) is False:
                            commands.append(f"net del vlan {vlan_id} ip address {dbIpAddr}")
                else:
                    db_ip_address = None

                for ipAddr in ip_address:
                    if check_if_exists(ipAddr, db_ip_address) is False:
                        commands.append(f"net add vlan {vlan_id} ip address {ipAddr}")
    else:
        if key_exists(db_config, "vlan") and expand is False:
            for dbVlan in list(db_config["vlan"].keys()):
                commands.append(f"net del vlan {dbVlan}")

    return commands


def del_vid(db_vids_config, vid):
    commands = []

    commands.append(f"net del bridge bridge vids {vid}")
    if key_exists(db_vids_config, vid, "bridge access"):
        interfaces = db_vids_config[vid]["bridge access"]
        for interface in interfaces:
            commands.append(f"net del interface {interface} bridge access {vid}")
    return commands


def bridge(config, db_config=None, expand=False):
    commands = []

    # config bridge
    if key_exists(config, "bridge"):
        bridge_config = config["bridge"]

        if key_exists(db_config, "bridge") and len(db_config["bridge"]) > 0:
            db_bridge_config = db_config["bridge"]
        else:
            db_bridge_config = None

        # config ports
        if key_exists(bridge_config, "ports"):
            ports = bridge_config["ports"]

            if key_exists(db_bridge_config, "ports") and expand is False:
                db_ports = db_bridge_config["ports"]

                for db_port in db_ports:
                    if check_if_exists(db_port, ports) is False:
                        commands.append(f"net del bridge bridge ports {db_port}")
            else:
                db_ports = None

            for port in ports:
                if check_if_exists(port, db_ports) is False:
                    commands.append(f"net add bridge bridge ports {port}")
        else:
            if key_exists(db_bridge_config, "ports") and expand is False:
                db_ports = db_bridge_config["ports"]
                for db_port in db_ports:
                    commands.append(f"net del bridge bridge ports {db_port}")

        # config vids
        if key_exists(bridge_config, "vids"):
            vids = bridge_config["vids"]

            if key_exists(db_bridge_config, "vids") and expand is False:
                db_vids = db_bridge_config["vids"]
                for dbVid in db_vids:
                    if check_if_exists(dbVid, list(vids.keys())) is False:
                        for command_cli in del_vid(db_vids, dbVid):
                            commands.append(command_cli)
            else:
                db_vids = None

            for vid in vids:
                if db_vids is not None and check_if_exists(vid, list(db_vids.keys())) is False:
                    commands.append(f"net add bridge bridge vids {vid}")

                # config bridge access
                if key_exists(vids, vid, "bridge access"):
                    interfaces = vids[vid]["bridge access"]

                    if key_exists(db_vids, vid, "bridge access") and expand is False:
                        db_interfaces = db_vids[vid]["bridge access"]

                        for db_interface in db_interfaces:
                            if check_if_exists(db_interface, interfaces) is False:
                                commands.append(f"net del interface {db_interface} bridge access {vid}")
                    else:
                        db_interfaces = None

                    for interface in interfaces:
                        if check_if_exists(interface, db_interfaces) is False:
                            commands.append(f"net add interface {interface} bridge access {vid}")
                else:
                    if key_exists(db_vids, vid, "bridge access") and expand is False:
                        for interface in db_vids[vid]["bridge access"]:
                            commands.append(f"net del interface {interface} bridge access {vid}")
        else:
            if key_exists(db_bridge_config, "vids") and expand is False:
                db_vids = db_bridge_config["vids"]
                for dbVid in db_vids:
                    for command_cli in del_vid(db_vids, dbVid):
                        commands.append(command_cli)
    else:
        if key_exists(db_config, "bridge") and expand is False:
            commands.append("net del bridge")
            if key_exists(db_config, "vlan"):
                db_config.pop("vlan")
                for command_cli in vlan(config, db_config, expand):
                    commands.append(command_cli)
            else:
                db_config.pop("vlan")
            db_config.pop("bridge")

    return commands


def vxlan(config, db_config=None, expand=False):
    commands = []

    # config vxlan
    if key_exists(config, "vxlan"):
        vxlan_config = config["vxlan"]

        if key_exists(db_config, "vxlan") and len(db_config["vxlan"]) > 0:
            db_vxlan_config = db_config["vxlan"]
        else:
            db_vxlan_config = None

        # config vnis
        if key_exists(vxlan_config, "vnis"):
            vnis = vxlan_config["vnis"]

            if key_exists(db_vxlan_config, "vnis") and expand is False:
                db_vnis = db_vxlan_config["vnis"]

                for db_vni_id in db_vnis:
                    if check_if_exists(db_vni_id, list(vnis.keys())) is False:
                        commands.append(f"net del vxlan {db_vni_id}")
            else:
                db_vnis = None

            for vni_id in vnis:
                vni = vnis[vni_id]

                if key_exists(db_vnis, vni_id):
                    db_vni = db_vnis[vni_id]
                else:
                    db_vni = None

                # config id
                if key_exists(vni, "id"):
                    if key_exists(db_vni, "id") and vni["id"] != db_vni["id"]:
                        commands.append(f"net del vxlan {vni_id} vxlan id")
                        commands.append(f"net add vxlan {vni_id} vxlan id {vni['id']}")
                    elif db_vni is None:
                        commands.append(f"net add vxlan {vni_id} vxlan id {vni['id']}")
                else:
                    if key_exists(db_vni, "id") and expand is False:
                        commands.append(f"net del vxlan {vni_id} vxlan id")

                # config bridge access
                if key_exists(vni, "bridge access"):
                    if key_exists(db_vni, "bridge access") and vni["bridge access"] != db_vni["bridge access"]:
                        commands.append(f"net del vxlan {vni_id} bridge access")
                        commands.append(f"net add vxlan {vni_id} bridge access {vni['bridge access']}")
                    elif db_vni is None:
                        commands.append(f"net add vxlan {vni_id} bridge access {vni['bridge access']}")
                else:
                    if key_exists(db_vni, "bridge access") and expand is False:
                        commands.append(f"net del vxlan {vni_id} bridge access")

                # config bridge learning
                if key_exists(vni, "bridge learning"):
                    if key_exists(db_vni, "bridge learning") and vni["bridge learning"] != db_vni["bridge learning"]:
                        if vni["bridge learning"] is False:
                            commands.append(f"net add vxlan {vni_id} bridge learning off")
                        else:
                            commands.append(f"net del vxlan {vni_id} bridge learning off")
                    elif db_vni is None:
                        if vni["bridge learning"] is False:
                            commands.append(f"net add vxlan {vni_id} bridge learning off")
                        else:
                            commands.append(f"net del vxlan {vni_id} bridge learning off")
                else:
                    if key_exists(db_vni, "bridge learning") and expand is False:
                        commands.append(f"net del vxlan {vni_id} bridge learning off")

                # config local-tunnelip
                if key_exists(vni, "local-tunnelip"):
                    if key_exists(db_vni, "local-tunnelip") and vni["local-tunnelip"] != db_vni["local-tunnelip"]:
                        commands.append(f"net del vxlan {vni_id} vxlan local-tunnelip")
                        commands.append(f"net add vxlan {vni_id} vxlan local-tunnelip {vni['local-tunnelip']}")
                    elif db_vni is None:
                        commands.append(f"net add vxlan {vni_id} vxlan local-tunnelip {vni['local-tunnelip']}")
                else:
                    if key_exists(db_vni, "local-tunnelip") and expand is False:
                        commands.append(f"net del vxlan {vni_id} vxlan local-tunnelip")

                # config remoteip
                if key_exists(vni, "remoteip"):
                    if key_exists(db_vni, "remoteip") and expand is False:
                        for remote_ip in db_vni["remoteip"]:
                            if check_if_exists(remote_ip, vni["remoteip"]) is False:
                                commands.append(f'net del vxlan {vni_id} vxlan remoteip {remote_ip}')

                    for remote_ip in vni["remoteip"]:
                        if key_exists(db_vni, "remoteip"):
                            if check_if_exists(remote_ip, db_vni["remoteip"]) is False:
                                commands.append(f'net add vxlan {vni_id} vxlan remoteip {remote_ip}')
                        else:
                            commands.append(f'net add vxlan {vni_id} vxlan remoteip {remote_ip}')
                else:
                    if key_exists(db_vni, "remoteip") and expand is False:
                        for remote_ip in db_vni["remoteip"]:
                            commands.append(f'net del vxlan {vni_id} vxlan remoteip {remote_ip}')
        else:
            if key_exists(db_vxlan_config, "vnis") and expand is False:
                for vni in db_vxlan_config["vnis"]:
                    commands.append(f"net del vxlan {vni}")
    else:
        if key_exists(db_config, "vxlan", "vnis") and expand is False:
            for vni in db_config["vxlan"]["vnis"]:
                commands.append(f"net del vxlan {vni}")

    return commands
