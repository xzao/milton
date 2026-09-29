#
#   src/worker/main.py
#
from shared import util
from task import interval, list_schedules, process, timing
import functools
import logging
import os
import scheduler
import time
import zoneinfo


#
#   var[s]
#
EMAILS = '/etc/milton/emails'
RELOAD = util.env_int('MILTON_WORKER_RELOAD', 300)
TICK   = util.env_int('MILTON_WORKER_INTERVAL', 1)
ZONE   = zoneinfo.ZoneInfo(util.env('MILTON_WORKER_TIMEZONE', 'UTC'))


#
#   logging
#
util.log_setup()


#
#   register
#
jobs       = scheduler.Scheduler(tzinfo = ZONE)
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

        # handle
        handle = functools.partial(process, EMAILS, user, name)

        # timing guard
        try:
            triggers = timing(name, ZONE)
        except Exception as error:
            logging.warning(f"[{key}] refused[{error}]")
            continue

        # job add
        if triggers == None:
            registered[key] = jobs.cyclic(interval(name), handle)
        else:
            registered[key] = jobs.weekly(triggers, handle)

        # log
        logging.info(f"[{key}] registered[{registered[key].datetime}]")

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
