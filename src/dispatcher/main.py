#
#   src/dispatcher/main.py
#
from shared import util
import email.message
import json
import logging
import os
import smtplib
import time


#
#   var[s]
#
EMAILS    = '/etc/milton/emails'
INTERVAL  = util.env_int('MILTON_DISPATCHER_INTERVAL', 60)
SMTP_HOST = util.env('MILTON_DISPATCHER_SMTP_HOST', 'localhost')
SMTP_PORT = util.env_int('MILTON_DISPATCHER_SMTP_PORT', 25)
SMTP_FROM = util.env('MILTON_DISPATCHER_SMTP_FROM', 'milton@localhost')
SMTP_USER = util.env('MILTON_DISPATCHER_SMTP_USER')
SMTP_PASS = util.env('MILTON_DISPATCHER_SMTP_PASS')


#
#   logging
#
logging.basicConfig(
    level = logging.INFO
)


#
#   dir[s]
#
for user in util.emails(EMAILS):

    # dir make
    for sub in ['outbox', 'sent']:
        os.makedirs(f"{EMAILS}/{user}/mail/{sub}", exist_ok = True)


#
#   send
#
def header(value):

    # text
    if isinstance(value, str):
        return value

    # return
    return ', '.join(value or [])

def send(folder, user):

    # id
    id = os.path.basename(folder)

    # properties read
    with open(f"{folder}/properties.json") as fp:
        data = json.load(fp)

    # to
    to = data.get('to')

    # to check
    if to == None:
        raise Exception('report missing recipient')

    # to valid check
    if not util.valid(EMAILS, to):
        raise Exception(f"invalid recipient '{to}'")

    # body read
    with open(f"{folder}/report.md") as fp:
        body = fp.read()

    # subject
    subject = data.get('subject') or 'milton report'

    # cc
    cc = data.get('cc') or []

    # bcc
    bcc = data.get('bcc') or []

    # message
    message = email.message.EmailMessage()
    message['From']    = SMTP_FROM
    message['To']      = to
    message['Subject'] = subject
    message.set_content(body)

    # cc header
    if cc:
        message['Cc'] = header(cc)

    # bcc header
    if bcc:
        message['Bcc'] = header(bcc)

    # smtp
    smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

    # smtp login
    if SMTP_USER != None:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)

    # smtp send
    smtp.send_message(message)

    # smtp quit
    smtp.quit()

    # sent move
    sent = f"{EMAILS}/{user}/mail/sent"
    os.rename(folder, f"{sent}/{id}")

    # log
    logging.info(f"[{id}] sent[{to}]")

    # return
    return True


#
#   loop
#
while True:

    # user iterate
    for user in util.emails(EMAILS):

        # outbox path
        outbox = f"{EMAILS}/{user}/mail/outbox"

        # folder iterate
        for name in sorted(os.listdir(outbox)):

            # path
            path = f"{outbox}/{name}"

            # dir check
            if os.path.isdir(path):
                send(path, user)

    # sleep
    logging.debug(f"sleeping for '{INTERVAL}'")
    time.sleep(INTERVAL)
