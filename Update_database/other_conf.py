import re


def updateHostname(configuration):
    hostname = {}
    for i, line in enumerate(configuration):
        if re.search("^hostname [\w]", line):
            temp_split = line.split(" ")
            hostname["hostname"] = temp_split[1]
            break
    return hostname


def updateStaticRoute(configuration):
    static_route = {"static routes": {}}
    for i, line in enumerate(configuration):
        if re.search("^ip route \S+", line):
            temp_split = line.split(" ")
            static_route["static routes"][temp_split[2]] = {"via": temp_split[3]}
    return static_route
