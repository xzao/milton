# services :: milton

milton listens on smtp, runs scheduled prompts over received mail and context,
and mails the resulting reports.

#
#   service[s]
#

- `receiver` — smtp listener; writes accepted mail into the owner's `mail/inbox`.
- `worker` — runs each schedule in the address `properties.json` `schedules`
  list; each run asks the configured model to turn all mail in the inbox into
  an html report with the shared `prompt/` text, then archives it.
- `dispatcher` — validates each finished report and sends it with amazon ses.

#
#   data
#

all state lives under `/etc/milton` (host data at `./mnt/etc/milton`; not
committed — gitignored and dockerignored, linked in the devcontainer and
mounted by compose):

```
/etc/milton/emails/<email>/properties.json  address properties (mail, schedules sections)
/etc/milton/emails/<email>/mail             mail spool (inbox/outbox/sent/archive)
/etc/milton/emails/<email>/context          read-only context for the prompts
/etc/milton/emails/<email>/prompt           prompt text (every file, shared by all schedules)
```

an `<email>` is valid when its `mail/` folder exists.

`properties.json` at the address root holds the loose per-address settings, one
section per concern. its `mail` section (`to`, `subject`, `cc`, `bcc`) becomes
the properties of every message the worker writes to
`mail/outbox/<id>/properties.json`, next to the generated html body in
`mail/outbox/<id>/message.html`, which the dispatcher reads back: `to` defaults
to the address, `subject` to the schedule name, and `cc` / `bcc` are lists
applied as message headers. the body is sent as `text/html`.

its `schedules` section is the list of schedules to run — each entry an
interval token, so a schedule exists when it is listed:

```json
{
    "mail": {
        "to": "you@example.com",
        "subject": "",
        "cc": [],
        "bcc": []
    },
    "schedules": ["5m", "30m", "1h", "daily", "weekly"]
}
```

every schedule shares one prompt: the text of every file under `prompt/`, read
in sorted order and each labelled with its path, the same way `context/` is
read.

#
#   usage
#

```
make develop [receiver worker dispatcher]   run services locally (all three by default)
make seed ADDR=you@example.com     create a new address
make start                         build and start the stack
make logs                          follow service logs
bin/milton worker process [address] [--preserve-inbox]   process on demand
```

`bin/milton` runs a service command on demand (`milton <service> <command>`).
`worker process` runs `task.process` once per address (`[address]` narrows it to
one) and `--preserve-inbox` leaves the batch in `mail/inbox` instead of moving
it to `mail/archive`, so the report in `mail/outbox/<id>/message.html` can be
previewed locally without consuming the mail. the run is labelled `preview`,
which is also the report subject when the `mail` section has none. set
`MILTON_WORKER_API_KEY` first.

#
#   env
#

copy `.env.sample` to `.env` (the makefile does this on first run) and set the
receiver port and the ses settings.

the services run as `MILTON_UID` / `MILTON_GID` (default `1000`) inside the
containers, so files written into `mnt/` stay owned by you — set them to the
output of `id -u` and `id -g` when that is not `1000`.

the worker writes the report html with an openai-compatible chat completions
api, openrouter by default. set `MILTON_WORKER_API_KEY`, and optionally
`MILTON_WORKER_API_URL` and `MILTON_WORKER_MODEL` (`openrouter/free` by
default). the prompts should ask for an html fragment — the reply becomes the
message body. the model gets each mail as a `<message>` block with its headers,
each `context/` and `prompt/` file as a `<file path="…">` block, and the prompt
last — so a `prompt/template.html` is read as the template to fill and
`context/` files as reference. the mail and context text is cut to
`MILTON_WORKER_INPUT_LIMIT` characters (`12000` by default; the prompt is never
cut) and the reply is
capped at `MILTON_WORKER_MAX_TOKENS` tokens (`2000` by default), so raise both
when the prompt, the context and the html template are large.

the dispatcher sends reports with amazon ses. `MILTON_DISPATCHER_SES_FROM` must
be a verified identity in ses, and the region comes from
`MILTON_DISPATCHER_SES_REGION` or `AWS_DEFAULT_REGION`; reports are left in the
outbox unless `AWS_SECRET_ACCESS_KEY` is set.
