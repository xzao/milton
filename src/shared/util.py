#
#   src/shared/util.py
#
import os


#
#   env[s]
#
def env(name, default = None):

    # value
    value = os.getenv(name)

    # value check
    if not value:
        return default

    # return
    return value

def env_int(name, default):

    # value
    value = os.getenv(name)

    # value check
    if not value:
        return default

    # return
    return int(value)


#
#   email[s]
#
def emails(root):

    # item[s]
    items = []

    # root check
    if not os.path.isdir(root):
        return []

    # list
    for name in sorted(os.listdir(root)):

        # mail check
        if os.path.isdir(f"{root}/{name}/mail"):
            items.append(name)

    # return
    return items

def valid(root, address):

    # separator check
    if '/' in address or '\\' in address:
        return False

    # mail check
    return os.path.isdir(f"{root}/{address}/mail")
