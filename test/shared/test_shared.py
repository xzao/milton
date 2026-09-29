#
#   test/shared/test_shared.py
#
from email.message import EmailMessage
from shared import mail, util
import logging


#
#   test[s]
#
def test_env_default():

    # value
    value = util.env_int('MILTON_TEST_UNSET', 7)

    # assert
    assert value == 7


def test_body_prefers_plain():

    # message
    message = EmailMessage()
    message.set_content('plain body')
    message.add_alternative('<p>html body</p>', subtype = 'html')

    # assert
    assert mail.body(mail.parse(message.as_bytes())) == 'plain body\n'


def test_body_falls_back_to_html():

    # message
    message = EmailMessage()
    message.set_content('<style>p {}</style><p>hello&amp;welcome</p><p>second <b>line</b></p>', subtype = 'html')

    # assert
    assert mail.body(mail.parse(message.as_bytes())) == 'hello&welcome\nsecond line'


def test_body_empty_without_text():

    # message
    message = EmailMessage()
    message.set_content(b'data', maintype = 'application', subtype = 'octet-stream')

    # assert
    assert mail.body(mail.parse(message.as_bytes())) == ''


def test_log_setup_format(monkeypatch):

    # handler[s]
    monkeypatch.setattr(logging.root, 'handlers', [])

    # setup
    util.log_setup()

    # record
    record = logging.LogRecord('milton', logging.WARNING, '/app/main.py', 24, 'retrying', None, None)
    record.created = 0

    # line
    line = logging.root.handlers[0].format(record)

    # assert
    assert line.endswith('  WARN  main.py:24 ➔ retrying')
