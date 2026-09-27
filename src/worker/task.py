#
#   src/worker/task.py
#
from shared import mail, util, uuid7
import datetime
import json
import logging
import openai
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


def get_properties(root, user):

    # path
    path = f"{root}/{user}/properties.json"

    # path check
    if not os.path.isfile(path):
        return {}

    # file read
    with open(path) as fp:
        data = json.load(fp)

    # mail section
    section = data.get('mail') or {}

    # return
    return section


def get_key():

    # key
    key = util.env('MILTON_WORKER_API_KEY')

    # key check
    if key == None:
        raise Exception('model key missing')

    # return
    return key


#
#   model
#
def model(messages):

    # url
    url = util.env('MILTON_WORKER_API_URL', 'https://openrouter.ai/api/v1')

    # client
    client = openai.OpenAI(
        base_url = url,
        api_key  = get_key(),
        timeout  = 60
    )

    # completion
    completion = client.chat.completions.create(
        model      = util.env('MILTON_WORKER_MODEL', 'openrouter/free'),
        messages   = messages,
        max_tokens = 2000
    )

    # choice[s]
    choices = completion.choices or []

    # choice check
    if not choices:
        raise Exception('model choice missing')

    # return
    return completion.choices[0].message.content or ''


#
#   generate
#
def text_cut(text, limit):

    # limit check
    if len(text) <= limit:
        return text

    # return
    return text[:limit]

def html_extract(text):

    # text
    text = text.strip()

    # fence check
    if '```' in text:

        # part
        part = text.split('```')[1].strip()

        # line[s]
        lines = part.splitlines()

        # tag check
        if len(lines) > 1 and '<' not in lines[0]:
            part = part[len(lines[0]):].lstrip()

        # text
        text = part

    # return
    return text

def generate(prompt, context, bodies):

    # system
    system = 'reply with a single html fragment, no markdown and no code fences'

    # body[s]
    joined = '\n\n---\n\n'.join(bodies)

    # limit
    limit = 12000

    # content
    content = f"{prompt}\n\n# context\n\n{context}\n\n# mail\n\n{joined}"

    # message[s]
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": text_cut(content, limit)}
    ]

    # html
    html = html_extract(model(messages))

    # html check
    if not html:
        raise Exception('model html empty')

    # return
    return html


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

    # properties read
    section = get_properties(root, user)

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

    # html generate
    html = generate(prompt_text, context_text, bodies)

    # id
    id = uuid7.new()

    # outbox make
    outbox = f"{root}/{user}/mail/outbox/{id}"
    os.makedirs(outbox, exist_ok = True)

    # message file
    with open(f"{outbox}/message.html", 'w', encoding = 'utf-8') as fp:
        fp.write(html)

    # to
    to = section.get('to') or user

    # subject
    subject = section.get('subject') or schedule

    # cc
    cc = section.get('cc') or []

    # bcc
    bcc = section.get('bcc') or []

    # message properties
    data = {
        "to": to,
        "subject": subject,
        "cc": cc,
        "bcc": bcc
    }

    # properties file
    with open(f"{outbox}/properties.json", 'w') as fp:
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
