import re


def updateHostname(configuration):
    hostname = {}
    for i, line in enumerate(configuration):
        if re.search("^hostname [\w]", line):
            temp_split = line.split(" ")
            hostname["hostname"] = temp_split[1]
            break
    return hostname
