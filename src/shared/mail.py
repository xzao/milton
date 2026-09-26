#
#   src/shared/mail.py
#
import email
import email.policy


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
def body(message):

    # part iterate
    for part in message.walk():

        # part check
        if part.get_content_type() != 'text/plain':
            continue

        # payload
        payload = part.get_content()

        # return
        return payload or ''

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
