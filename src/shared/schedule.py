#
#   src/shared/schedule.py
#
from scheduler import trigger
import datetime
import re


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
#   timing
#
def timing(schedule, zone):

    # part[s]
    parts = schedule.split()

    # time check
    if len(parts) < 2:
        return None

    # weekday[s]
    weekdays = [trigger.Monday, trigger.Tuesday, trigger.Wednesday, trigger.Thursday, trigger.Friday, trigger.Saturday, trigger.Sunday]

    # day map
    names = {
        'daily'    : [0, 1, 2, 3, 4, 5, 6],
        'weekdays' : [0, 1, 2, 3, 4],
        'weekends' : [5, 6],
        'mon'      : [0],
        'tue'      : [1],
        'wed'      : [2],
        'thu'      : [3],
        'fri'      : [4],
        'sat'      : [5],
        'sun'      : [6]
    }

    # day[s]
    days = []

    # name iterate
    for name in parts[0].lower().split(','):

        # name check
        if name not in names:
            raise Exception(f"invalid schedule day '{name}'")

        # day iterate
        for day in names[name]:

            # day check
            if day not in days:
                days.append(day)

    # time[s]
    times = []

    # part iterate
    for part in parts[1:]:

        # time check
        if not re.fullmatch(r'\d{1,2}:\d{2}', part):
            raise Exception(f"invalid schedule time '{part}'")

        # hour, minute
        hour, minute = part.split(':')

        # range check
        if int(hour) > 23 or int(minute) > 59:
            raise Exception(f"invalid schedule time '{part}'")

        # time append
        times.append(datetime.time(int(hour), int(minute), tzinfo = zone))

    # trigger[s]
    triggers = []

    # day iterate
    for day in sorted(days):

        # time iterate
        for time in times:
            triggers.append(weekdays[day](time))

    # return
    return triggers
