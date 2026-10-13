#
#   test/shared/test_schedule.py
#
from shared import schedule
import datetime
import pytest
import zoneinfo


#
#   test[s]
#
def test_interval_minute():

    # assert
    assert schedule.interval('5m') == datetime.timedelta(minutes = 5)


def test_interval_hour():

    # assert
    assert schedule.interval('2h') == datetime.timedelta(hours = 2)


def test_interval_daily():

    # assert
    assert schedule.interval('daily') == datetime.timedelta(days = 1)


def test_interval_weekly():

    # assert
    assert schedule.interval('weekly') == datetime.timedelta(days = 7)


def test_interval_unknown_is_daily():

    # assert
    assert schedule.interval('someday') == datetime.timedelta(days = 1)


def test_timing_none_without_time():

    # assert
    assert schedule.timing('daily', datetime.timezone.utc) == None
    assert schedule.timing('5m', datetime.timezone.utc) == None


def test_timing_daily_every_day():

    # zone
    zone = zoneinfo.ZoneInfo('Australia/Melbourne')

    # trigger[s]
    triggers = schedule.timing('daily 08:30', zone)

    # assert
    assert len(triggers) == 7
    assert triggers[0].time == datetime.time(8, 30, tzinfo = zone)


def test_timing_multiple_days_and_times():

    # trigger[s]
    triggers = schedule.timing('mon,weekends 08:00 17:30', datetime.timezone.utc)

    # day[s]
    days = []

    # trigger iterate
    for item in triggers:
        days.append([type(item).__name__, item.time.hour, item.time.minute])

    # assert
    assert days == [
        ['Monday', 8, 0],
        ['Monday', 17, 30],
        ['Saturday', 8, 0],
        ['Saturday', 17, 30],
        ['Sunday', 8, 0],
        ['Sunday', 17, 30]
    ]


def test_timing_weekdays_skips_duplicate_days():

    # assert
    assert len(schedule.timing('weekdays,mon 09:00', datetime.timezone.utc)) == 5


def test_timing_invalid_day_raises():

    # assert
    with pytest.raises(Exception, match = 'invalid schedule day'):
        schedule.timing('someday 08:00', datetime.timezone.utc)


def test_timing_invalid_time_raises():

    # assert
    with pytest.raises(Exception, match = 'invalid schedule time'):
        schedule.timing('daily 25:00', datetime.timezone.utc)

    # assert
    with pytest.raises(Exception, match = 'invalid schedule time'):
        schedule.timing('daily 8am', datetime.timezone.utc)
