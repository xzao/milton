#
#   src/dispatcher/message.py
#


#
#   address
#
def addresses(value):

    # text
    if isinstance(value, str):
        return [value]

    # return
    return value or []


#
#   destination
#
def destination(to, cc, bcc):

    # item
    item = {
        "ToAddresses": [to]
    }

    # cc check
    if cc:
        item["CcAddresses"] = addresses(cc)

    # bcc check
    if bcc:
        item["BccAddresses"] = addresses(bcc)

    # return
    return item


#
#   content
#
def content(subject, html):

    # item
    item = {
        "Simple": {
            "Subject": {
                "Data": subject
            },
            "Body": {
                "Html": {
                    "Data": html
                }
            }
        }
    }

    # return
    return item
