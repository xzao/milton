#
#   test/receiver/test_receiver.py
#
from aiosmtpd.smtp import Envelope
from email.message import EmailMessage
from handler import Handler
import asyncio
import os
import pytest


#
#   test[s]
#
def test_rcpt_accepts_valid_address(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # address make
    os.makedirs(f"{root}/alice@example.com/mail", exist_ok = True)

    # envelope
    envelope = Envelope()
    envelope.mail_from = 'sender@example.com'

    # handler
    handler = Handler(root)

    # rcpt
    status = asyncio.run(handler.handle_RCPT(None, None, envelope, 'alice@example.com', None))

    # assert
    assert status == '250 OK'
    assert envelope.rcpt_tos == ['alice@example.com']


def test_rcpt_rejects_unknown_address(tmp_path, caplog):

    # root
    root = f"{tmp_path}/emails"

    # envelope
    envelope = Envelope()
    envelope.mail_from = 'sender@example.com'

    # handler
    handler = Handler(root)

    # rcpt
    status = asyncio.run(handler.handle_RCPT(None, None, envelope, 'nope@example.com', None))

    # assert
    assert status == '550 not accepted'
    assert envelope.rcpt_tos == []
    assert 'rejected' in caplog.text


def test_data_writes_message_and_attachment(tmp_path):

    # root
    root = f"{tmp_path}/emails"

    # address make
    os.makedirs(f"{root}/alice@example.com/mail", exist_ok = True)

    # message
    message = EmailMessage()
    message['From']    = 'sender@example.com'
    message['To']      = 'alice@example.com'
    message['Subject'] = 'test'
    message.set_content('hello body')
    message.add_attachment(b'file-bytes', maintype = 'application', subtype = 'octet-stream', filename = 'file.txt')

    # envelope
    envelope = Envelope()
    envelope.mail_from = 'sender@example.com'
    envelope.rcpt_tos  = ['alice@example.com']
    envelope.content   = message.as_bytes()

    # handler
    handler = Handler(root)

    # data
    status = asyncio.run(handler.handle_DATA(None, None, envelope))

    # assert
    assert status == '250 OK'

    # inbox
    inbox = f"{root}/alice@example.com/mail/inbox"

    # id
    id = os.listdir(inbox)[0]

    # message file
    with open(f"{inbox}/{id}/message.eml", 'rb') as fp:
        assert b'hello body' in fp.read()

    # attachment file
    with open(f"{inbox}/{id}/attachments/file.txt", 'rb') as fp:
        assert fp.read() == b'file-bytes'


def test_data_save_failure_logs_and_raises(tmp_path, caplog):

    # root
    root = f"{tmp_path}/emails"

    # address make
    os.makedirs(f"{root}/alice@example.com/mail", exist_ok = True)

    # inbox block
    with open(f"{root}/alice@example.com/mail/inbox", 'w') as fp:
        fp.write('blocked')

    # envelope
    envelope = Envelope()
    envelope.mail_from = 'sender@example.com'
    envelope.rcpt_tos  = ['alice@example.com']
    envelope.content   = b'From: sender@example.com\n\nhello body\n'

    # handler
    handler = Handler(root)

    # raises
    with pytest.raises(OSError):
        asyncio.run(handler.handle_DATA(None, None, envelope))

    # assert
    assert 'failed' in caplog.text
