# services :: milton

milton listens on smtp, scrapes html sites, runs scheduled prompts over
received mail, scraped pages and context, and mails the resulting reports.

#
#   service[s]
#

- `receiver` — smtp listener; writes accepted mail into the owner's `mail/inbox`.
- `scraper` — runs each schedule in the address `staple.json`
  `schedules` `scraper` list; each run fetches every site in its `sites` list and writes a page that changed into the owner's `xml/inbox`.
- `worker` — runs each schedule in the address `staple.json` `schedules`
  `worker` list; each run asks the configured model to turn the new mail and scraped
  xml pages into json with the shared `prompt.md`, renders it into an html
  report, then archives them.
- `dispatcher` — validates each finished report and sends it with amazon ses.

#
#   data
#

all state lives under `/etc/milton` (host data at `./mnt/etc/milton`; not
committed — gitignored and dockerignored, linked in the devcontainer and
mounted by compose):

```
/etc/milton/staples/<email>/staple.json      address settings (mail headers, schedules, sites)
/etc/milton/staples/<email>/template.json    data skeleton of template.html, sent to the model as the schema
/etc/milton/staples/<email>/code             reference files, sent to the model as context
/etc/milton/staples/<email>/xml              scraped pages, one folder each (inbox/archive)
/etc/milton/staples/<email>/mail             mail spool (inbox/outbox/sent/archive)
/etc/milton/staples/<email>/prompt.md        prompt text (shared by all schedules)
/etc/milton/staples/<email>/template.html    jinja2 email template (optional)
/etc/milton/skel                            files every new address starts with
```

an `<email>` is valid when its `mail/` folder exists.

`staple.json` at the address root holds the address settings — mail
headers, schedules and sites. none of it is sent to the model.

```json
{
    "from": "reports@example.com",
    "to": "you@example.com",
    "subject": "",
    "cc": [],
    "bcc": [],
    "schedules": {
        "worker": ["daily 08:00"],
        "scraper": ["1h"]
    },
    "sites": [
        {
            "name": "advisories",
            "url": "https://example.com/advisories",
            "xpath": "//article",
            "request": {
                "method": "GET",
                "headers": { "Authorization": "Bearer …" },
                "params": { "page": "1" },
                "body": ""
            }
        }
    ]
}
```

`from`, `to`, `subject`, `cc`, `bcc` become the headers of every message the
worker writes to `mail/outbox/<id>/message.json`, next to the generated html
body in `mail/outbox/<id>/message.html`, which the dispatcher reads back:
`from` and `to` default to the address, `subject` to the schedule name, and
`cc` / `bcc` are lists applied as message headers. the body is sent as
`text/html`.

`schedules` holds one list per service: `worker` is when to report and
`scraper` is when to scrape. a schedule exists when it is listed. each entry
is either an interval token — `5m`, `30m`, `1h`, `daily`, `weekly`, counted
from when the service registers it — or a day and one or more `HH:MM` times:

- `daily 08:00` — every day at 08:00;
- `weekdays 08:30 17:00` — monday to friday, twice a day;
- `weekends 10:00`;
- `mon,wed,fri 09:00` — any comma list of `mon` … `sun`, `daily`, `weekdays`,
  `weekends`.

timed schedules run in `MILTON_TIMEZONE` (an iana name such as
`Australia/Melbourne`; `UTC` by default), daylight saving included. docker
compose (and the Makefile, for `make develop` / `make preview`) passes it to
every service as `TZ`, so log timestamps use it too. an entry
with an unknown day or time is logged and skipped.

`sites` is the html sites to scrape, one request skeleton each:

- `name` labels the page and is what a change is tracked by (the `url` when
  empty);
- `url` is the page to fetch — an entry without one is skipped, so the empty
  entry a new address starts with does nothing;
- `xpath` picks what to keep: elements become text, `//a/@href` or
  `string(//h1)` are kept as they are, and matches are joined by a blank line.
  empty keeps the text of the whole page;
- `request` is optional: `method` (`GET` by default), `headers`, `params` (the
  query string) and `body` (an object is sent as json, a text as is). keys and
  tokens are written here in the clear — the file lives in `mnt/`, which is
  never committed.

every schedule fetches every site (`MILTON_SCRAPER_TIMEOUT`, `30` seconds by
default, bounds each request), so an address with no `scraper`
schedule is never scraped. an interval such as `1h` is counted from when the
scraper registers it, so the first scrape is one interval after start — use
`bin/milton scraper scrape` to fetch now. the scraper re-reads addresses and
`schedules` every `MILTON_SCRAPER_RELOAD` seconds (`300` by default). a run
writes `xml/inbox/<id>/page.json` (`name`, `url`, `date`) and `page.txt`
only when the text differs from the last page of that `name`, so an unchanged
site is reported once. a site that fails is logged and tried again next time.

`template.json` is the data skeleton of `template.html` and nothing else: the
json object the model fills in for each report (the whole file is sent to the
model as the schema), and what `template.html` is rendered with.

```json
{
    "headline": "",
    "summary": "",
    "items": [{ "title": "", "detail": "" }]
}
```

every schedule shares one prompt, `prompt.md`, and one email template,
`template.html`, both at the address root next to `template.json`.

every schedule also shares one inbox, so when an address lists several, the
first to run reports on the mail and archives it — the others find it empty.
scraped pages go in `xml/inbox/<id>/` (any files in the folder) and are
reported and archived to `xml/archive` just like mail. when there is no new
mail and no new page, the model is not called and a schedule still sends a
short "nothing to report" email; set `MILTON_WORKER_SUPPRESS_EMPTY=1` to skip
those runs instead.
list one schedule per address unless that is what you want; the worker warns
when it sees more than one. the worker re-reads addresses and `schedules` every
`MILTON_WORKER_RELOAD` seconds (`300` by default), so new addresses and
schedule edits need no restart.

#
#   usage
#

```
make develop [receiver scraper worker dispatcher]   run services locally (all four by default)
make flush [address ...]           clear unsent reports from mail/outbox (asks first)
make init you@example.com         create a new address from /etc/milton/skel
make permissions                   chown mnt/ to MILTON_UID:MILTON_GID (1000:1000)
make preview                       preview a report without consuming the inbox
make start                         build and start the stack
make logs                          follow service logs
bin/milton scraper scrape [address]                      scrape on demand
bin/milton worker process [address] [--preserve-inbox]   process on demand
```

`make init <email>` creates `/etc/milton/staples/<email>/` with
its folders (`code/`, `mail/` with its `inbox`, `outbox`, `sent` and
`archive`, and `xml/` with its `inbox` and `archive`) and a copy of every file in
`/etc/milton/skel` — a `prompt.md`, `staple.json`, `template.json` and `template.html` to
edit. `from` and `to` can stay empty in
the skel's `staple.json`: they default to the address. it refuses an address
that already exists.

the defaults are committed in the repo `etc/milton/skel/`. `make install` (run
when the devcontainer is created) copies them into `/etc/milton/skel`, keeping
any file already there, so edit the copy in `/etc/milton/skel` to change what
new addresses start with locally.

`bin/milton` runs a service command on demand (`milton <service> <command>`).
`worker process` runs `task.process` once per address (`[address]` narrows it to
one) and `--preserve-inbox` leaves the batch in `mail/inbox` and `xml/inbox`
instead of moving it to the archive, so the report in
`mail/outbox/<id>/message.html` can be previewed locally, xml pages included,
without consuming them. `scraper scrape` fetches the `sites` of each address
once, into `xml/inbox`. the worker run is labelled `preview`,
which is also the report subject when `staple.json` has none. set
`MILTON_WORKER_API_KEY` first.

#
#   env
#

copy `.env.sample` to `.env` (the makefile does this on first run) and set the
receiver port and the ses settings.

the services run as `MILTON_UID` / `MILTON_GID` (default `1000`) inside the
containers, so files written into `mnt/` stay owned by you — set them to the
output of `id -u` and `id -g` when that is not `1000`.

the worker asks an openai-compatible chat completions api (openrouter by
default) for the report data as one json object, then renders the email html
itself. set `MILTON_WORKER_API_KEY`, and optionally `MILTON_WORKER_API_URL` and
`MILTON_WORKER_MODEL` (`openrouter/free` by default). the model gets each mail
as a `<message>` block with its headers, each `code/` file as a
`<file path="…">` block, the address `template.json` as the
`<schema>` — the json skeleton it must fill in,
every key and value type kept, lists grown to fit — and the prompt last.

the address `template.html` is a
[jinja2](https://jinja.palletsprojects.com/) template rendered with that
json: `{{ headline }}`, `{% for item in items %}…{% endfor %}`,
`{% if … %}`. values are html-escaped, and a key the json lacks is an error —
guard an optional one with `{% if key is defined %}` or `{{ key | default('—') }}`.
`x.key` always reads the json key, even one named like a dict method (`items`,
`clear`, `keys`).
the template is never sent to the model. when the reply is not json or the
render fails, the error is logged and the report is still sent: the error, then
the reply pretty-printed in a `<pre>` block, so nothing is lost. an address with
no template always gets that json layout. the model reply is kept in
`mail/outbox/<id>/message.json` under `data` — what the template is rendered
with (the raw text when it is not json).

html-only mail is converted to text. each run takes as much mail as fits in
`MILTON_WORKER_INPUT_LIMIT` characters (`12000` by default) after the context,
and leaves the rest in the inbox for the next run (the schema and the prompt
are never cut), and the reply is capped at `MILTON_WORKER_MAX_TOKENS` tokens
(`2000` by default), so raise both when the prompt, the context and the json
are large.

the dispatcher sends reports with amazon ses. each address's `mail` `from` (the
address itself when unset) must be a verified identity in ses, and the region comes from
`MILTON_DISPATCHER_SES_REGION` or `AWS_DEFAULT_REGION`; reports are left in the
outbox unless `AWS_SECRET_ACCESS_KEY` is set.
