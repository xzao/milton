#
#   src/dispatcher/main.py
#
from shared import util
from message import content, destination
import boto3
import json
import logging
import os
import time


#
#   var[s]
#
EMAILS     = '/etc/milton/emails'
INTERVAL   = util.env_int('MILTON_DISPATCHER_INTERVAL', 60)
SES_FROM   = util.env('MILTON_DISPATCHER_SES_FROM', 'milton@localhost')
SES_REGION = util.env('MILTON_DISPATCHER_SES_REGION')


#
#   logging
#
util.log_setup()


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
def send(folder, user):

    # id
    id = os.path.basename(folder)

    # key check
    if util.env('AWS_SECRET_ACCESS_KEY') == None:
        logging.debug(f"[{id}] skipped[aws key missing]")
        return False

    # properties read
    with open(f"{folder}/properties.json") as fp:
        data = json.load(fp)

    # to
    to = data.get('to')

    # to check
    if to == None:
        raise Exception('report missing recipient')

    # to valid check
    if '@' not in to:
        raise Exception(f"invalid recipient '{to}'")

    # html read
    with open(f"{folder}/message.html", encoding = 'utf-8') as fp:
        html = fp.read()

    # subject
    subject = data.get('subject') or 'milton report'

    # cc
    cc = data.get('cc') or []

    # bcc
    bcc = data.get('bcc') or []

    # client
    client = boto3.client('sesv2', region_name = SES_REGION)

    # ses send
    response = client.send_email(
        FromEmailAddress = SES_FROM,
        Destination      = destination(to, cc, bcc),
        Content          = content(subject, html)
    )

    # message id
    message_id = response.get('MessageId')

    # sent make
    sent = f"{EMAILS}/{user}/mail/sent"
    os.makedirs(sent, exist_ok = True)

    # sent move
    os.rename(folder, f"{sent}/{id}")

    # log
    logging.info(f"[{id}] sent[{to}] message[{message_id}]")

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

        # outbox check
        if not os.path.isdir(outbox):
            continue

        # folder iterate
        for name in sorted(os.listdir(outbox)):

            # path
            path = f"{outbox}/{name}"

            # dir check
            if os.path.isdir(path):

                # send guard
                try:
                    send(path, user)
                except Exception as error:
                    logging.error(f"[{name}] failed[{error}]")

    # sleep
    logging.debug(f"sleeping for '{INTERVAL}'")
    time.sleep(INTERVAL)
