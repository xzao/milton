#
#   test/scraper/test_scraper.py
#
from page import collect, extract, fetch, last, list_schedules, list_sites, scrape
import json
import os
import page
import pytest


#
#   make[s]
#
MARKUP = '<html><head><title>news</title><script>var x = 1;</script></head><body><h1>title</h1><div class="post"><p>first</p></div><div class="post"><a href="/second">second</a></div></body></html>'

def user_make(root, user, sites = None, schedules = ['1h']):

    # mail make
    os.makedirs(f"{root}/{user}/mail/inbox", exist_ok = True)

    # sites check
    if sites == None:
        return user

    # staple json file
    with open(f"{root}/{user}/staple.json", 'w') as fp:
        json.dump({'schedules': {'scraper': schedules}, 'sites': sites}, fp)

    # return
    return user

def site_make(name = 'news', xpath = '', request = None):

    # site
    site = {
        "name": name,
        "url": "https://example.com/news",
        "xpath": xpath
    }

    # request check
    if request != None:
        site["request"] = request

    # return
    return site

def request_make(monkeypatch, text = MARKUP, status = 200):

    # call[s]
    calls = []

    # response
    def response():
        return None

    response.text        = text
    response.status_code = status

    # stub
    def stub(method, url, **options):

        # call append
        calls.append({
            'method'  : method,
            'url'     : url,
            'options' : options
        })

        # return
        return response

    # patch
    monkeypatch.setattr(page.requests, 'request', stub)

    # return
    return calls


#
#   test[s]
#
def test_list_sites_missing_file(tmp_path):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # assert
    assert list_sites(tmp_path, user) == []


def test_list_sites_skips_empty_url(tmp_path):

    # user
    user = user_make(tmp_path, 'a@example.com', [{'name': 'skeleton', 'url': ''}, site_make()])

    # site[s]
    sites = list_sites(tmp_path, user)

    # assert
    assert len(sites) == 1
    assert sites[0]['name'] == 'news'


def test_list_schedules_missing_file(tmp_path):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # assert
    assert list_schedules(tmp_path, user) == []


def test_list_schedules_reads_staple_json(tmp_path):

    # user
    user = user_make(tmp_path, 'a@example.com', [], ['1h', 'daily 06:00'])

    # assert
    assert list_schedules(tmp_path, user) == ['1h', 'daily 06:00']


def test_fetch_default_request(monkeypatch):

    # call[s]
    calls = request_make(monkeypatch)

    # assert
    assert fetch(site_make(), 5) == MARKUP
    assert calls[0]['method'] == 'GET'
    assert calls[0]['url'] == 'https://example.com/news'
    assert calls[0]['options'] == {'headers': {}, 'params': {}, 'timeout': 5}


def test_fetch_request_skeleton(monkeypatch):

    # call[s]
    calls = request_make(monkeypatch)

    # request
    request = {
        "method": "POST",
        "headers": {"Authorization": "Bearer key"},
        "params": {"page": "1"},
        "body": {"query": "patch"}
    }

    # fetch
    fetch(site_make(request = request))

    # option[s]
    options = calls[0]['options']

    # assert
    assert calls[0]['method'] == 'POST'
    assert options['headers'] == {'Authorization': 'Bearer key'}
    assert options['params'] == {'page': '1'}
    assert options['json'] == {'query': 'patch'}
    assert 'data' not in options


def test_fetch_text_body(monkeypatch):

    # call[s]
    calls = request_make(monkeypatch)

    # fetch
    fetch(site_make(request = {'method': 'POST', 'body': 'a=1&b=2'}))

    # assert
    assert calls[0]['options']['data'] == 'a=1&b=2'
    assert 'json' not in calls[0]['options']


def test_fetch_status_raises(monkeypatch):

    # stub
    request_make(monkeypatch, status = 503)

    # assert
    with pytest.raises(Exception, match = "site status '503'"):
        fetch(site_make())


def test_extract_whole_page():

    # text
    text = extract(MARKUP)

    # assert
    assert 'title' in text
    assert 'first' in text
    assert 'var x' not in text


def test_extract_xpath_elements():

    # assert
    assert extract(MARKUP, '//div[@class="post"]') == 'first\n\nsecond'


def test_extract_xpath_attributes():

    # assert
    assert extract(MARKUP, '//a/@href') == '/second'


def test_extract_xpath_value():

    # assert
    assert extract(MARKUP, 'string(//h1)') == 'title'


def test_extract_xpath_no_match():

    # assert
    assert extract(MARKUP, '//table') == ''


def test_extract_xml_declaration():

    # assert
    assert extract(f"<?xml version=\"1.0\" encoding=\"utf-8\"?>{MARKUP}", '//h1') == 'title'


def test_scrape_writes_page(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # stub
    request_make(monkeypatch)

    # id
    id = scrape(tmp_path, user, site_make(xpath = '//h1'))

    # folder
    folder = f"{tmp_path}/{user}/xml/inbox/{id}"

    # page json read
    with open(f"{folder}/page.json") as fp:
        data = json.load(fp)

    # page text read
    with open(f"{folder}/page.txt") as fp:
        text = fp.read()

    # assert
    assert sorted(os.listdir(f"{tmp_path}/{user}/xml")) == ['inbox']
    assert data['name'] == 'news'
    assert data['url'] == 'https://example.com/news'
    assert data['date']
    assert text == 'title'


def test_scrape_unchanged_skips(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # stub
    request_make(monkeypatch)

    # first
    id = scrape(tmp_path, user, site_make(xpath = '//h1'))

    # archive move
    os.makedirs(f"{tmp_path}/{user}/xml/archive")
    os.rename(f"{tmp_path}/{user}/xml/inbox/{id}", f"{tmp_path}/{user}/xml/archive/{id}")

    # assert
    assert scrape(tmp_path, user, site_make(xpath = '//h1')) == None
    assert os.listdir(f"{tmp_path}/{user}/xml/inbox") == []


def test_scrape_changed_writes_again(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # id[s]
    ids = ['0002', '0001']

    # id patch
    monkeypatch.setattr(page.uuid7, 'new', ids.pop)

    # first
    request_make(monkeypatch)
    scrape(tmp_path, user, site_make(xpath = '//h1'))

    # second
    request_make(monkeypatch, text = '<h1>changed</h1>')
    scrape(tmp_path, user, site_make(xpath = '//h1'))

    # assert
    assert len(os.listdir(f"{tmp_path}/{user}/xml/inbox")) == 2
    assert last(tmp_path, user, 'news') == 'changed'


def test_scrape_name_separates_sites(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # stub
    request_make(monkeypatch)

    # scrape
    scrape(tmp_path, user, site_make(name = 'one', xpath = '//h1'))
    scrape(tmp_path, user, site_make(name = 'two', xpath = '//h1'))

    # assert
    assert len(os.listdir(f"{tmp_path}/{user}/xml/inbox")) == 2


def test_scrape_empty_skips(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # stub
    request_make(monkeypatch)

    # assert
    assert scrape(tmp_path, user, site_make(xpath = '//table')) == None
    assert not os.path.isdir(f"{tmp_path}/{user}/xml")


def test_collect_scrapes_every_site(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com', [site_make(name = 'one'), site_make(name = 'two')])

    # stub
    request_make(monkeypatch)

    # assert
    assert collect(tmp_path, user) == True
    assert len(os.listdir(f"{tmp_path}/{user}/xml/inbox")) == 2


def test_collect_failed_site_carries_on(tmp_path, monkeypatch):

    # user
    user = user_make(tmp_path, 'a@example.com', [site_make(name = 'one', xpath = '//['), site_make(name = 'two')])

    # stub
    request_make(monkeypatch)

    # assert
    assert collect(tmp_path, user) == False
    assert len(os.listdir(f"{tmp_path}/{user}/xml/inbox")) == 1


def test_collect_invalid_file_fails(tmp_path):

    # user
    user = user_make(tmp_path, 'a@example.com')

    # staple json file
    with open(f"{tmp_path}/{user}/staple.json", 'w') as fp:
        fp.write('{')

    # assert
    assert collect(tmp_path, user) == False
