#
#   src/scraper/page.py
#
from shared import mail, uuid7
import datetime
import json
import logging
import lxml.etree
import lxml.html
import os
import re
import requests


#
#   get[s]
#
def get_properties(root, user):

    # path
    path = f"{root}/{user}/staple.json"

    # path check
    if not os.path.isfile(path):
        return {}

    # file read
    with open(path) as fp:
        properties = json.load(fp)

    # return
    return properties


#
#   list
#
def list_schedules(root, user):

    # schedule[s]
    schedules = get_properties(root, user).get('schedules') or {}

    # return
    return schedules.get('scraper') or []

def list_sites(root, user):

    # item[s]
    items = []

    # site iterate
    for site in get_properties(root, user).get('sites') or []:

        # url check
        if not site.get('url'):
            continue

        # append
        items.append(site)

    # return
    return items


#
#   fetch
#
def fetch(site, timeout = 30):

    # request
    request = site.get('request') or {}

    # body
    body = request.get('body')

    # option[s]
    options = {
        'headers' : request.get('headers') or {},
        'params'  : request.get('params') or {},
        'timeout' : timeout
    }

    # json body
    if isinstance(body, (dict, list)):
        options['json'] = body

    # text body
    if isinstance(body, str) and body:
        options['data'] = body

    # response
    response = requests.request(request.get('method') or 'GET', site['url'], **options)

    # status check
    if response.status_code >= 400:
        raise Exception(f"site status '{response.status_code}'")

    # return
    return response.text


#
#   extract
#
def extract(markup, xpath = ''):

    # xpath check
    if not xpath:
        return mail.text(markup)

    # declaration drop
    markup = re.sub(r'^\s*<\?xml[^>]*\?>', '', markup)

    # markup check
    if not markup.strip():
        return ''

    # node[s]
    nodes = lxml.html.fromstring(markup).xpath(xpath)

    # value check
    if not isinstance(nodes, list):
        nodes = [nodes]

    # part[s]
    parts = []

    # node iterate
    for node in nodes:

        # element check
        if lxml.etree.iselement(node):
            part = mail.text(lxml.html.tostring(node, encoding = 'unicode', with_tail = False))
        else:
            part = str(node).strip()

        # part check
        if part:
            parts.append(part)

    # return
    return '\n\n'.join(parts)


#
#   scrape
#
def last(root, user, name):

    # folder[s]
    folders = []

    # sub iterate
    for sub in ['inbox', 'archive']:

        # path
        path = f"{root}/{user}/xml/{sub}"

        # path check
        if not os.path.isdir(path):
            continue

        # folder iterate
        for id in os.listdir(path):
            folders.append([id, f"{path}/{id}"])

    # folder iterate
    for id, folder in sorted(folders, reverse = True):

        # page check
        if not os.path.isfile(f"{folder}/page.json") or not os.path.isfile(f"{folder}/page.txt"):
            continue

        # page json read
        with open(f"{folder}/page.json", encoding = 'utf-8') as fp:
            data = json.load(fp)

        # name check
        if data.get('name') != name:
            continue

        # page text read
        with open(f"{folder}/page.txt", encoding = 'utf-8') as fp:
            text = fp.read()

        # return
        return text

    # return
    return None

def scrape(root, user, site, timeout = 30):

    # name
    name = site.get('name') or site['url']

    # markup
    markup = fetch(site, timeout)

    # text
    text = extract(markup, site.get('xpath') or '')

    # text check
    if not text:
        logging.warning(f"[{user}] [{name}] empty")
        return None

    # last check
    if text == last(root, user, name):
        logging.debug(f"[{user}] [{name}] unchanged")
        return None

    # id
    id = uuid7.new()

    # folder make
    folder = f"{root}/{user}/xml/{id}"
    os.makedirs(folder, exist_ok = True)

    # page data
    data = {
        "name": name,
        "url": site['url'],
        "date": datetime.datetime.now().astimezone().isoformat(timespec = 'seconds')
    }

    # page json file
    with open(f"{folder}/page.json", 'w', encoding = 'utf-8') as fp:
        json.dump(data, fp, indent = 4, ensure_ascii = False)

    # page text file
    with open(f"{folder}/page.txt", 'w', encoding = 'utf-8') as fp:
        fp.write(text)

    # inbox make
    inbox = f"{root}/{user}/xml/inbox"
    os.makedirs(inbox, exist_ok = True)

    # inbox move
    os.rename(folder, f"{inbox}/{id}")

    # log
    logging.info(f"[{user}] [{name}] scraped[{len(text)}]")

    # return
    return id


#
#   collect
#
def collect(root, user, timeout = 30):

    # site guard
    try:
        sites = list_sites(root, user)
    except Exception as error:
        logging.error(f"[{user}] failed[{error}]")
        return False

    # ok
    ok = True

    # site iterate
    for site in sites:

        # scrape guard
        try:
            scrape(root, user, site, timeout)
        except Exception as error:
            logging.error(f"[{user}] [{site.get('name') or site.get('url')}] failed[{error}]")
            ok = False

    # return
    return ok
