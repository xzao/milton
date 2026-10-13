#
#   src/scraper/main.py
#
from shared import schedule, util
from page import collect, list_schedules
import functools
import logging
import scheduler
import time
import zoneinfo


#
#   var[s]
#
EMAILS  = '/etc/milton/staples'
RELOAD  = util.env_int('MILTON_SCRAPER_RELOAD', 300)
TICK    = util.env_int('MILTON_SCRAPER_INTERVAL', 1)
TIMEOUT = util.env_int('MILTON_SCRAPER_TIMEOUT', 30)
ZONE    = zoneinfo.ZoneInfo(util.env('TZ', 'UTC'))


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

        # schedule guard
        try:
            schedules = list_schedules(EMAILS, user)
        except Exception as error:
            logging.error(f"[{user}] failed[{error}]")
            continue

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
        handle = functools.partial(collect, EMAILS, user, TIMEOUT)

        # timing guard
        try:
            triggers = schedule.timing(name, ZONE)
        except Exception as error:
            logging.warning(f"[{key}] refused[{error}]")
            continue

        # job add
        if triggers == None:
            registered[key] = jobs.cyclic(schedule.interval(name), handle)
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
