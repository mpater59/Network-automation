from Other.other import key_exists
from Other.other import check_if_exists


def del_bgp_neighbor(neighbor, config):
    commands = []
    if key_exists(config, "remote"):
        commands.append(f"net del bgp neighbor {neighbor} remote-as {config['remote']}")
    if key_exists(config, "update"):
        commands.append(f"net del bgp neighbor {neighbor} update-source")
    if key_exists(config, "activate evpn") and config["activate evpn"] is True:
        commands.append(f"net del bgp l2vpn evpn neighbor {neighbor} activate")
    if key_exists(config, "rrc") and config["rrc"] is True:
        commands.append(f"net del bgp neighbor {neighbor} route-reflector-client")
    if key_exists(config, "evpn rrc") and config["evpn rrc"] is True:
        commands.append(f"net del bgp l2vpn evpn neighbor {neighbor} route-reflector-client")
    if key_exists(config, "next-hop-self") and config["next-hop-self"] is True:
        commands.append(f"net del bgp neighbor {neighbor} next-hop-self")
    return commands


def config_neighbors(bgp_config, db_bgp_config, expand, reset_bgp):
    commands = []

    if key_exists(db_bgp_config, "neighbors") and expand is False and reset_bgp is False:
        for dbNeighbor in db_bgp_config["neighbors"]:
            neighbors = list(bgp_config["neighbors"].keys())
            if check_if_exists(dbNeighbor, neighbors) is False:
                for commands_cli in del_bgp_neighbor(dbNeighbor, db_bgp_config["neighbors"][dbNeighbor]):
                    commands.append(commands_cli)

    for neigh in bgp_config["neighbors"]:
        neighbor = bgp_config["neighbors"][neigh]

        if key_exists(db_bgp_config, "neighbors", neigh):
            db_neighbor = db_bgp_config["neighbors"][neigh]
        else:
            db_neighbor = None

        # config remote
        if key_exists(neighbor, "remote"):
            if key_exists(db_neighbor, "remote") and str(db_neighbor["remote"]) != str(neighbor["remote"]):
                commands.append(f"net del bgp neighbor {neigh} remote-as {db_neighbor['remote']}")
                commands.append(f"net add bgp neighbor {neigh} remote-as {neighbor['remote']}")
            elif db_neighbor is None or reset_bgp is True:
                commands.append(f"net add bgp neighbor {neigh} remote-as {neighbor['remote']}")
        else:
            if key_exists(db_neighbor, "remote") and expand is False and reset_bgp is False:
                commands.append(f"net del bgp neighbor {neigh} remote-as {db_neighbor['remote']}")

        # config update-source
        if key_exists(neighbor, "update"):
            if key_exists(db_neighbor, "update") and db_neighbor["update"] != neighbor["update"]:
                commands.append(f"net del bgp neighbor {neigh} update-source")
                commands.append(f"net add bgp neighbor {neigh} update-source {neighbor['update']}")
            elif db_neighbor is None or reset_bgp is True:
                commands.append(f"net add bgp neighbor {neigh} update-source {neighbor['update']}")
        else:
            if key_exists(db_neighbor, "update") and expand is False and reset_bgp is False:
                commands.append(f"net del bgp neighbor {neigh} update-source")

        # config activate evpn
        if key_exists(neighbor, "activate evpn"):
            if key_exists(db_neighbor, "activate evpn") and db_neighbor["activate evpn"] != \
                    neighbor["activate evpn"]:
                if neighbor["activate evpn"] is True:
                    commands.append(f"net add bgp l2vpn evpn neighbor {neigh} activate")
                elif neighbor["activate evpn"] is False:
                    commands.append(f"net del bgp l2vpn evpn neighbor {neigh} activate")
            elif db_neighbor is None or reset_bgp is True:
                if neighbor["activate evpn"] is True:
                    commands.append(f"net add bgp l2vpn evpn neighbor {neigh} activate")
        else:
            if key_exists(db_neighbor, "activate evpn") and expand is False and reset_bgp is False:
                if db_neighbor["activate evpn"] is True:
                    commands.append(f"net del bgp l2vpn evpn neighbor {neigh} activate")

        # config rrc
        if key_exists(neighbor, "rrc"):
            if key_exists(db_neighbor, "rrc") and db_neighbor["rrc"] != neighbor["rrc"]:
                if neighbor["rrc"] is True:
                    commands.append(f"net add bgp neighbor {neigh} route-reflector-client")
                elif neighbor["rrc"] is False:
                    commands.append(f"net del bgp neighbor {neigh} route-reflector-client")
            elif db_neighbor is None or reset_bgp is True:
                if neighbor["rrc"] is True:
                    commands.append(f"net add bgp neighbor {neigh} route-reflector-client")
        else:
            if key_exists(db_neighbor, "rrc") and expand is False and reset_bgp is False:
                if db_neighbor["rrc"] is True:
                    commands.append(f"net add bgp neighbor {neigh} route-reflector-client")

        # config evpn rrc
        if key_exists(neighbor, "evpn rrc"):
            if key_exists(db_neighbor, "evpn rrc") and db_neighbor["evpn rrc"] != neighbor["evpn rrc"]:
                if neighbor["evpn rrc"] is True:
                    commands.append(f"net add bgp l2vpn evpn neighbor {neigh} route-reflector-client")
                elif neighbor["evpn rrc"] is False:
                    commands.append(f"net del bgp l2vpn evpn neighbor {neigh} route-reflector-client")
            elif db_neighbor is None or reset_bgp is True:
                if neighbor["evpn rrc"] is True:
                    commands.append(f"net add bgp l2vpn evpn neighbor {neigh} route-reflector-client")
        else:
            if key_exists(db_neighbor, "evpn rrc") and expand is False and reset_bgp is False:
                if db_neighbor["evpn rrc"] is True:
                    commands.append(f"net del bgp l2vpn evpn neighbor {neigh} route-reflector-client")

        # config next-hop-self
        if key_exists(neighbor, "next-hop-self"):
            if key_exists(db_neighbor, "next-hop-self") and db_neighbor["next-hop-self"] != neighbor["next-hop-self"]:
                if neighbor["next-hop-self"] is True:
                    commands.append(f"net add bgp neighbor {neigh} next-hop-self")
                elif neighbor["next-hop-self"] is False:
                    commands.append(f"net del bgp neighbor {neigh} next-hop-self")
            elif db_neighbor is None or reset_bgp is True:
                if neighbor["next-hop-self"] is True:
                    commands.append(f"net add bgp neighbor {neigh} next-hop-self")
        else:
            if key_exists(db_neighbor, "next-hop-self") and expand is False and reset_bgp is False:
                if db_neighbor["next-hop-self"] is True:
                    commands.append(f"net del bgp neighbor {neigh} next-hop-self")

    return commands


def bgp(config, db_config=None, expand=False):
    commands = []

    # config bgp
    if key_exists(config, "bgp"):
        bgp_config = config["bgp"]

        if key_exists(db_config, "bgp") and len(db_config["bgp"]) > 0:
            db_bgp_config = db_config["bgp"]
        else:
            db_bgp_config = None

        # config AS
        reset_bgp = False
        if key_exists(bgp_config, "as"):
            if key_exists(db_bgp_config, "as") and db_bgp_config["as"] != bgp_config["as"]:
                commands.append(f"net del bgp autonomous-system {db_bgp_config['as']}")
                commands.append(f"net add bgp autonomous-system {bgp_config['as']}")
                reset_bgp = True
            elif db_bgp_config is None:
                commands.append(f"net add bgp autonomous-system {bgp_config['as']}")
        else:
            if key_exists(db_bgp_config, "as") and expand is False:
                commands.append(f"net del bgp autonomous-system {db_bgp_config['as']}")

        # config router-id
        if key_exists(bgp_config, "router-id"):
            if key_exists(db_bgp_config, "router-id") and db_bgp_config["router-id"] != bgp_config["router-id"] and \
                    reset_bgp is False:
                commands.append("net del bgp router-id")
                commands.append(f"net add bgp router-id {bgp_config['router-id']}")
            elif db_bgp_config is None or reset_bgp is True:
                commands.append(f"net add bgp router-id {bgp_config['router-id']}")
        else:
            if key_exists(db_bgp_config, "router-id") and expand is False and reset_bgp is False:
                commands.append("net del bgp router-id")

        # config neighbors
        if key_exists(bgp_config, "neighbors"):
            for command_cli in config_neighbors(bgp_config, db_bgp_config, expand, reset_bgp):
                commands.append(command_cli)
        else:
            if key_exists(db_bgp_config, "neighbors") and expand is False and reset_bgp is False:
                for dbNeighbor in db_bgp_config["neighbors"]:
                    for command_cli in del_bgp_neighbor(dbNeighbor, db_bgp_config["neighbors"][dbNeighbor]):
                        commands.append(command_cli)

        # config advertise-all-vni
        if key_exists(bgp_config, "advertise-all-vni"):
            if key_exists(db_bgp_config, "advertise-all-vni") and bgp_config["advertise-all-vni"] != \
                    db_bgp_config["advertise-all-vni"]:
                if bgp_config["advertise-all-vni"] is True:
                    commands.append("net add bgp l2vpn evpn advertise-all-vni")
                elif bgp_config["advertise-all-vni"] is False:
                    commands.append("net del bgp l2vpn evpn advertise-all-vni")
            elif db_bgp_config is None or reset_bgp is True:
                if bgp_config["advertise-all-vni"] is True:
                    commands.append("net add bgp l2vpn evpn advertise-all-vni")
        else:
            if key_exists(db_bgp_config, "advertise-all-vni") and expand is False and reset_bgp is False:
                if db_bgp_config["advertise-all-vni"] is False:
                    commands.append("net del bgp l2vpn evpn advertise-all-vni")

        # config networks
        if key_exists(bgp_config, "networks"):
            if key_exists(db_bgp_config, "networks") and expand is False:
                for network in db_bgp_config["networks"]:
                    if check_if_exists(network, bgp_config["networks"]) is False:
                        commands.append(f'net del bgp network {network}')

            for network in bgp_config["networks"]:
                if key_exists(db_bgp_config, "networks"):
                    if check_if_exists(network, db_bgp_config["networks"]) is False:
                        commands.append(f'net add bgp network {network}')
                else:
                    commands.append(f'net add bgp network {network}')
        else:
            if key_exists(db_bgp_config, "networks") and expand is False:
                for network in db_bgp_config["networks"]:
                    commands.append(f'net del bgp network {network}')
    else:
        if key_exists(db_config, "bgp", "as") and expand is False:
            commands.append(f"net del bgp autonomous-system {db_config['bgp']['as']}")

    return commands
