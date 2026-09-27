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
#   register
#
jobs = scheduler.Scheduler()

# user iterate
for user in util.emails(EMAILS):

    # schedule iterate
    for name in list_schedules(EMAILS, user):
        jobs.cyclic(interval(name), functools.partial(process, EMAILS, user, name))


#
#   loop
#
while True:

    # exec
    jobs.exec_jobs()

    # sleep
    time.sleep(TICK)
