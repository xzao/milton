#
#   src/receiver/main.py
#
from aiosmtpd.controller import Controller
from handler import Handler
from shared import util
import logging
import time


#
#   var[s]
#
EMAILS = '/etc/milton/emails'
PORT   = util.env_int('MILTON_RECEIVER_SMTP_PORT', 2525)


#
#   logging
#
util.log_setup()


#
#   controller
#
controller = Controller(
    Handler(EMAILS),
    hostname = '0.0.0.0',
    port     = PORT
)

controller.start()


#
#   loop
#
while True:
    time.sleep(3600)
