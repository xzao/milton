#
#   src/shared/uuid7.py
#
import os
import time


#
#   new
#
def new():

    # time
    ms = int(time.time() * 1000)

    # rand
    rand = os.urandom(10)

    # version
    version = (rand[0] & 0x0f) | 0x70

    # variant
    variant = (rand[2] & 0x3f) | 0x80

    # raw
    raw = ms.to_bytes(6, 'big') + bytes([version, rand[1], variant]) + rand[3:]

    # hex
    text = raw.hex()

    # uuid
    uuid = f"{text[0:8]}-{text[8:12]}-{text[12:16]}-{text[16:20]}-{text[20:]}"

    # return
    return uuid
