#
#   src/shared/mail.py
#
import email
import email.policy
import html
import re


#
#   parse
#
def parse(raw):

    # message
    message = email.message_from_bytes(raw, policy = email.policy.default)

    # return
    return message


#
#   body
#
def text(markup):

    # block[s] drop
    markup = re.sub(r'(?is)<(script|style)\b.*?</\1\s*>', '', markup)

    # break[s]
    markup = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h[1-6])\s*>', '\n', markup)

    # tag[s] drop
    markup = re.sub(r'<[^>]+>', '', markup)

    # entity[s]
    markup = html.unescape(markup)

    # space[s]
    markup = re.sub(r'[ \t\r\f\v]+', ' ', markup)

    # line[s]
    markup = re.sub(r' *\n[ \n]*', '\n', markup)

    # return
    return markup.strip()

def body(message):

    # plain part
    part = message.get_body(preferencelist = ('plain',))

    # plain check
    if part != None:
        return part.get_content() or ''

    # html part
    part = message.get_body(preferencelist = ('html',))

    # html check
    if part != None:
        return text(part.get_content() or '')

    # return
    return ''


#
#   attachment[s]
#
def attachments(message):

    # item[s]
    items = []

    # part iterate
    for part in message.walk():

        # attachment check
        if part.get_content_disposition() != 'attachment':
            continue

        # name
        name = part.get_filename() or 'attachment'

        # data
        data = part.get_payload(decode = True) or b''

        # append
        items.append({
            'name' : name,
            'data' : data
        })

    # return
    return items
