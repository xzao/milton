#
#   src/receiver/handler.py
#
from aiosmtpd.handlers import MessageBase
from shared import mail, util, uuid7
import logging
import os


#
#   handler
#
class Handler(MessageBase):

    def __init__(self, root):
        super().__init__()
        self.root = root

    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):

        # address check
        if not util.valid(self.root, address):
            return '550 not accepted'

        # return
        return '250 OK'

    async def handle_DATA(self, server, session, envelope):

        # rcpt iterate
        for address in envelope.rcpt_tos:

            # id
            id = uuid7.new()

            # folder
            folder = f"{self.root}/{address}/mail/inbox/{id}"

            # folder make
            os.makedirs(f"{folder}/attachments", exist_ok = True)

            # message file
            with open(f"{folder}/message.eml", 'wb') as fp:
                fp.write(envelope.content)

            # message parse
            message = mail.parse(envelope.content)

            # attachment iterate
            for attachment in mail.attachments(message):

                # name
                name = os.path.basename(attachment['name'])

                # attachment file
                with open(f"{folder}/attachments/{name}", 'wb') as fp:
                    fp.write(attachment['data'])

            # log
            logging.info(f"[{id}] received[{envelope.mail_from}] to[{address}]")

        # return
        return '250 OK'
