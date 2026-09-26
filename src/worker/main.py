#
#   src/worker/main.py
#
from shared import mail, util, uuid7
import datetime
import functools
import json
import logging
import os
import scheduler
import time


#
#   var[s]
#
EMAILS = '/etc/milton/emails'
TICK   = util.env_int('MILTON_WORKER_INTERVAL', 1)


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
    for sub in ['inbox', 'outbox', 'sent', 'archive']:
        os.makedirs(f"{EMAILS}/{user}/mail/{sub}", exist_ok = True)


#
#   interval
#
def interval(schedule):

    # minute
    if schedule.endswith('m'):
        return datetime.timedelta(minutes = int(schedule[:-1]))

    # hour
    if schedule.endswith('h'):
        return datetime.timedelta(hours = int(schedule[:-1]))

    # daily
    if schedule == 'daily':
        return datetime.timedelta(days = 1)

    # weekly
    if schedule == 'weekly':
        return datetime.timedelta(days = 7)

    # return
    return datetime.timedelta(days = 1)


#
#   list
#
def list_schedules(user):

    # root
    root = f"{EMAILS}/{user}/prompt"

    # item[s]
    items = []

    # list
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            items.append(name)

    # return
    return items


#
#   get[s]
#
def get_prompt(user, schedule):

    # path
    path = f"{EMAILS}/{user}/prompt/{schedule}/prompt.md"

    # file read
    with open(path) as fp:
        text = fp.read()

    # return
    return text

def get_context(user):

    # text
    text = ''

    # walk
    for dirpath, dirnames, filenames in os.walk(f"{EMAILS}/{user}/context"):

        # file iterate
        for file in filenames:

            # path
            path = os.path.join(dirpath, file)

            # file read
            with open(path) as fp:
                text += fp.read() + "\n"

    # return
    return text


#
#   prompt
#
def report(prompt, context, body):

    # feature not implemented
    return 'feature not implemented'


#
#   process
#
def process(user, schedule):

    # inbox path
    inbox = f"{EMAILS}/{user}/mail/inbox"

    # prompt read
    prompt_text = get_prompt(user, schedule)

    # context read
    context_text = get_context(user)

    # folder iterate
    for name in sorted(os.listdir(inbox)):

        # path
        path = f"{inbox}/{name}"

        # message read
        with open(f"{path}/message.eml", 'rb') as fp:
            raw = fp.read()

        # message parse
        message = mail.parse(raw)

        # body
        body = mail.body(message)

        # report
        text = report(prompt_text, context_text, body)

        # id
        id = uuid7.new()

        # outbox make
        outbox = f"{EMAILS}/{user}/mail/outbox/{id}"
        os.makedirs(outbox, exist_ok = True)

        # report file
        with open(f"{outbox}/report.md", 'w') as fp:
            fp.write(text)

        # report data
        data = {
            "to": user,
            "subject": schedule
        }

        # report json
        with open(f"{outbox}/report.json", 'w') as fp:
            json.dump(data, fp)

        # archive make
        archive = f"{EMAILS}/{user}/mail/archive"
        os.makedirs(archive, exist_ok = True)

        # archive move
        os.rename(path, f"{archive}/{name}")

        # log
        logging.info(f"[{user}] [{schedule}] processed[{name}]")

    # return
    return None


#
#   register
#
jobs = scheduler.Scheduler()

# user iterate
for user in util.emails(EMAILS):

    # schedule iterate
    for name in list_schedules(user):
        jobs.cyclic(interval(name), functools.partial(process, user, name))


#
#   loop
#
while True:

    # exec
    jobs.exec_jobs()

    # sleep
    time.sleep(TICK)
