#
#   src/worker/task.py
#
from shared import mail, uuid7
import datetime
import json
import logging
import os


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
#   list
#
def list_schedules(root, user):

    # path
    path = f"{root}/{user}/prompt"

    # item[s]
    items = []

    # path check
    if not os.path.isdir(path):
        return []

    # list
    for name in sorted(os.listdir(path)):

        # dir check
        if os.path.isdir(f"{path}/{name}"):
            items.append(name)

    # return
    return items


#
#   get[s]
#
def get_prompt(root, user, schedule):

    # path
    path = f"{root}/{user}/prompt/{schedule}/prompt.md"

    # path check
    if not os.path.isfile(path):
        raise Exception(f"prompt missing '{path}'")

    # file read
    with open(path) as fp:
        text = fp.read()

    # return
    return text

def get_context(root, user):

    # path
    path = f"{root}/{user}/context"

    # text
    text = ''

    # path check
    if not os.path.isdir(path):
        return ''

    # walk
    for dirpath, dirnames, filenames in os.walk(path):

        # dir[s] sort
        dirnames.sort()

        # file iterate
        for file in sorted(filenames):

            # file path
            file_path = os.path.join(dirpath, file)

            # file read
            with open(file_path) as fp:
                text += fp.read() + "\n"

    # return
    return text


#
#   generate
#
def generate(prompt, context, bodies):

    # feature not implemented
    return 'feature not implemented'


#
#   process
#
def process(root, user, schedule):

    # inbox path
    inbox = f"{root}/{user}/mail/inbox"

    # inbox check
    if not os.path.isdir(inbox):
        return None

    # prompt read
    prompt_text = get_prompt(root, user, schedule)

    # context read
    context_text = get_context(root, user)

    # mail path[s]
    paths = []

    # folder iterate
    for name in sorted(os.listdir(inbox)):

        # path
        path = f"{inbox}/{name}"

        # dir check
        if not os.path.isdir(path):
            continue

        # message path
        message_path = f"{path}/message.eml"

        # message check
        if not os.path.isfile(message_path):
            logging.debug(f"[{user}] skipped[{name}]")
            continue

        # append
        paths.append(path)

    # mail check
    if not paths:
        return None

    # body[s]
    bodies = []

    # path iterate
    for path in paths:

        # message read
        with open(f"{path}/message.eml", 'rb') as fp:
            raw = fp.read()

        # message parse
        message = mail.parse(raw)

        # body
        bodies.append(mail.body(message))

    # report generate
    text = generate(prompt_text, context_text, bodies)

    # id
    id = uuid7.new()

    # outbox make
    outbox = f"{root}/{user}/mail/outbox/{id}"
    os.makedirs(outbox, exist_ok = True)

    # report file
    with open(f"{outbox}/report.md", 'w') as fp:
        fp.write(text)

    # report data
    data = {
        "to": user,
        "subject": schedule
    }

    # report json
    with open(f"{outbox}/report.json", 'w') as fp:
        json.dump(data, fp)

    # archive make
    archive = f"{root}/{user}/mail/archive"
    os.makedirs(archive, exist_ok = True)

    # archive iterate
    for path in paths:

        # archive move
        os.rename(path, f"{archive}/{os.path.basename(path)}")

    # log
    logging.info(f"[{user}] [{schedule}] reported[{len(bodies)}]")

    # return
    return None
