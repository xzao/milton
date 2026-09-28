#
#   src/worker/main.py
#
from shared import util
from task import interval, list_schedules, process
import functools
import logging
import os
import scheduler
import time


#
#   var[s]
#
EMAILS = '/etc/milton/emails'
RELOAD = util.env_int('MILTON_WORKER_RELOAD', 300)
TICK   = util.env_int('MILTON_WORKER_INTERVAL', 1)


#
#   logging
#
logging.basicConfig(
    level = logging.INFO
)


#
#   register
#
jobs       = scheduler.Scheduler()
registered = {}

def register():

    # found
    found = {}

    # user iterate
    for user in util.emails(EMAILS):

        # dir make
        for sub in ['inbox', 'outbox', 'sent', 'archive']:
            os.makedirs(f"{EMAILS}/{user}/mail/{sub}", exist_ok = True)

        # schedule[s]
        schedules = list_schedules(EMAILS, user)

        # schedule check
        if len(schedules) > 1 and f"{user}/{schedules[0]}" not in registered:
            logging.warning(f"[{user}] schedules[{len(schedules)}] share one inbox; the first to run takes the mail")

        # schedule iterate
        for name in schedules:
            found[f"{user}/{name}"] = [user, name]

    # removed iterate
    for key in list(registered):

        # key check
        if key in found:
            continue

        # job delete
        jobs.delete_job(registered.pop(key))

        # log
        logging.info(f"[{key}] unregistered")

    # added iterate
    for key in found:

        # key check
        if key in registered:
            continue

        # user, name
        user, name = found[key]

        # job add
        registered[key] = jobs.cyclic(interval(name), functools.partial(process, EMAILS, user, name))

        # log
        logging.info(f"[{key}] registered")

    # return
    return None


#
#   loop
#
reloaded = 0

while True:

    # reload check
    if time.time() - reloaded >= RELOAD:

        # register
        register()

        # reloaded
        reloaded = time.time()

    # exec
    jobs.exec_jobs()

    # sleep
    time.sleep(TICK)
