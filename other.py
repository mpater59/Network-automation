def compare_list(list1, list2):
    list1.sort()
    list2.sort()
    if list1 == list2:
        return True
    else:
        return False


def key_exists(dictionary, *keys):
    if dictionary is None:
        return False
    elif not isinstance(dictionary, dict):
        return False
    for key in keys:
        try:
            dictionary = dictionary[key]
            if dictionary is None or dictionary == "":
                return False
        except KeyError:
            return False
    return True


def check_if_exists(var_item, var_list):
    if var_list is None:
        return False
    elif not isinstance(var_list, list):
        return False
    for item in var_list:
        if item == var_item:
            return True
        else:
            continue
    return False


def stringToBool(string):
    string = string.lower()
    if string in ["true", "yes"]:
        string = True
        return string
    elif string in ["false", "no"]:
        string = False
        return string
    else:
        print("Entered parameter is not boolean!")
        exit()