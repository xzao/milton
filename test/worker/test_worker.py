#
#   test/worker/test_worker.py
#
from email.message import EmailMessage
from shared import uuid7
from task import generate, get_context, get_prompt, interval, list_schedules, process
import datetime
import json
import os
import pytest


#
#   make[s]
#
def user_make(root, user, schedule = None, prompt = None):

    # mail make
    for sub in ['inbox', 'outbox', 'sent', 'archive']:
        os.makedirs(f"{root}/{user}/mail/{sub}", exist_ok = True)

    # context make
    os.makedirs(f"{root}/{user}/context", exist_ok = True)

    # prompt make
    if schedule != None:
        os.makedirs(f"{root}/{user}/prompt/{schedule}", exist_ok = True)
        with open(f"{root}/{user}/prompt/{schedule}/prompt.md", 'w') as fp:
            fp.write(prompt)

    # return
    return user

def message_make(root, user, body = 'hello body'):

    # id
    id = uuid7.new()

    # folder make
    folder = f"{root}/{user}/mail/inbox/{id}"
    os.makedirs(f"{folder}/attachments", exist_ok = True)

    # message
    message = EmailMessage()
    message['From']    = 'sender@example.com'
    message['To']      = user
    message['Subject'] = 'test'
    message.set_content(body)

    # message file
    with open(f"{folder}/message.eml", 'wb') as fp:
        fp.write(message.as_bytes())

    # return
    return id


#
#   test[s]
#
def test_interval_minute():

    # assert
    assert interval('5m') == datetime.timedelta(minutes = 5)


def test_interval_hour():

    # assert
    assert interval('2h') == datetime.timedelta(hours = 2)


def test_interval_daily():

    # assert
    assert interval('daily') == datetime.timedelta(days = 1)


def test_interval_weekly():

    # assert
    assert interval('weekly') == datetime.timedelta(days = 7)


def test_interval_unknown_is_daily():

    # assert
    assert interval('someday') == datetime.timedelta(days = 1)


def test_list_schedules_sorted(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # prompt make
    for schedule in ['30m', '5m', 'daily']:
        user_make(root, 'alice@example.com', schedule, 'prompt text')

    # assert
    assert list_schedules(root, 'alice@example.com') == ['30m', '5m', 'daily']


def test_list_schedules_ignores_files(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'prompt text')

    # file make
    with open(f"{root}/alice@example.com/prompt/notes.txt", 'w') as fp:
        fp.write('not a schedule')

    # assert
    assert list_schedules(root, 'alice@example.com') == ['daily']


def test_list_schedules_empty_without_prompt_dir(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com')

    # assert
    assert list_schedules(root, 'alice@example.com') == []


def test_get_prompt_reads_text(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # assert
    assert get_prompt(root, 'alice@example.com', 'daily') == 'summarise the new mail.'


def test_get_prompt_missing_raises(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # raises
    with pytest.raises(Exception, match = 'prompt missing'):
        get_prompt(root, 'alice@example.com', 'weekly')


def test_get_context_concatenates_sorted(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com')

    # file make
    for name in ['b.md', 'a.md']:
        with open(f"{root}/alice@example.com/context/{name}", 'w') as fp:
            fp.write(name[0])

    # assert
    assert get_context(root, 'alice@example.com') == 'a\nb\n'


def test_get_context_walks_nested_dirs(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com')

    # dir make
    os.makedirs(f"{root}/alice@example.com/context/team", exist_ok = True)

    # file make
    with open(f"{root}/alice@example.com/context/team/roster.md", 'w') as fp:
        fp.write('roster')

    # assert
    assert get_context(root, 'alice@example.com') == 'roster\n'


def test_get_context_empty_without_dir(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # mail make
    os.makedirs(f"{root}/alice@example.com/mail", exist_ok = True)

    # assert
    assert get_context(root, 'alice@example.com') == ''


def test_generate_is_stub():

    # assert
    assert generate('prompt', 'context', ['body']) == 'feature not implemented'


def test_process_writes_report_and_archives_inbox(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # message make
    id = message_make(root, 'alice@example.com', 'hello body')

    # process
    result = process(root, 'alice@example.com', 'daily')

    # outbox
    outbox = f"{root}/alice@example.com/mail/outbox"

    # report id
    report_id = os.listdir(outbox)[0]

    # report file
    with open(f"{outbox}/{report_id}/report.md") as fp:
        assert fp.read() == 'feature not implemented'

    # report data
    with open(f"{outbox}/{report_id}/report.json") as fp:
        assert json.load(fp) == {'to': 'alice@example.com', 'subject': 'daily'}

    # inbox empty
    assert os.listdir(f"{root}/alice@example.com/mail/inbox") == []

    # archive move
    assert os.path.isdir(f"{root}/alice@example.com/mail/archive/{id}")

    # assert
    assert result == None


def test_process_archives_all_mail(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # item[s]
    ids = []

    # message[s] make
    for _ in range(3):
        ids.append(message_make(root, 'alice@example.com'))

    # process
    process(root, 'alice@example.com', 'daily')

    # report count
    assert len(os.listdir(f"{root}/alice@example.com/mail/outbox")) == 1

    # archive move
    assert sorted(os.listdir(f"{root}/alice@example.com/mail/archive")) == sorted(ids)

    # inbox empty
    assert os.listdir(f"{root}/alice@example.com/mail/inbox") == []


def test_process_passes_all_mail_to_generate(tmp_path, monkeypatch):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # context make
    with open(f"{root}/alice@example.com/context/profile.md", 'w') as fp:
        fp.write('alice')

    # body[s]
    sent = ['first mail', 'second mail', 'third mail']

    # parsed body[s]
    parsed = ['first mail\n', 'second mail\n', 'third mail\n']

    # message[s] make
    for body in sent:
        message_make(root, 'alice@example.com', body)

    # call[s]
    calls = []

    # generate make
    def generate_stub(prompt, context, mail):
        calls.append({
            'prompt'  : prompt,
            'context' : context,
            'bodies'  : mail
        })
        return 'batch report'

    # generate patch
    monkeypatch.setattr('task.generate', generate_stub)

    # process
    process(root, 'alice@example.com', 'daily')

    # assert
    assert len(calls) == 1
    assert calls[0]['prompt'] == 'summarise the new mail.'
    assert calls[0]['context'] == 'alice\n'
    assert sorted(calls[0]['bodies']) == sorted(parsed)

    # report file
    outbox = f"{root}/alice@example.com/mail/outbox"
    with open(f"{outbox}/{os.listdir(outbox)[0]}/report.md") as fp:
        assert fp.read() == 'batch report'


def test_process_report_id_is_uuid7(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # message make
    message_make(root, 'alice@example.com')

    # process
    process(root, 'alice@example.com', 'daily')

    # id
    id = os.listdir(f"{root}/alice@example.com/mail/outbox")[0]

    # assert
    assert len(id) == 36
    assert id.split('-')[2][0] == '7'
    assert id.split('-')[3][0] in '89ab'


def test_process_empty_inbox_writes_nothing(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # process
    process(root, 'alice@example.com', 'daily')

    # assert
    assert os.listdir(f"{root}/alice@example.com/mail/outbox") == []


def test_process_ignores_inbox_files(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # file make
    with open(f"{root}/alice@example.com/mail/inbox/notes.txt", 'w') as fp:
        fp.write('not a message')

    # process
    process(root, 'alice@example.com', 'daily')

    # assert
    assert os.listdir(f"{root}/alice@example.com/mail/outbox") == []


def test_process_skips_message_without_eml(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # message make
    id = message_make(root, 'alice@example.com', 'hello body')

    # folder make
    partial = '01a0e000-0000-7000-8000-000000000000'
    os.makedirs(f"{root}/alice@example.com/mail/inbox/{partial}/attachments", exist_ok = True)

    # process
    process(root, 'alice@example.com', 'daily')

    # inbox keep
    assert os.listdir(f"{root}/alice@example.com/mail/inbox") == [partial]

    # archive move
    assert os.listdir(f"{root}/alice@example.com/mail/archive") == [id]

    # report count
    assert len(os.listdir(f"{root}/alice@example.com/mail/outbox")) == 1

    # root
    root = f"{tmp_path}/emails"

    # prompt make
    os.makedirs(f"{root}/alice@example.com/prompt/daily", exist_ok = True)
    with open(f"{root}/alice@example.com/prompt/daily/prompt.md", 'w') as fp:
        fp.write('summarise the new mail.')

    # process
    result = process(root, 'alice@example.com', 'daily')

    # assert
    assert result == None


def test_process_missing_prompt_raises(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # user make
    user_make(root, 'alice@example.com', 'daily', 'summarise the new mail.')

    # message make
    message_make(root, 'alice@example.com')

    # raises
    with pytest.raises(Exception, match = 'prompt missing'):
        process(root, 'alice@example.com', 'weekly')
