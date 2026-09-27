# services :: milton

milton listens on smtp, runs scheduled prompts over received mail and context,
and mails the resulting reports.

#
#   service[s]
#

- `receiver` — smtp listener; writes accepted mail into the owner's `mail/inbox`.
- `worker` — runs each user's `prompt/<schedule>/prompt.md` on its schedule;
  each run asks the configured model to turn all mail in the inbox into an html
  report, then archives it.
- `dispatcher` — validates each finished report and sends it with amazon ses.

#
#   data
#

all state lives under `/etc/milton` (host data at `./mnt/etc/milton`; not
committed — gitignored and dockerignored, linked in the devcontainer and
mounted by compose):

```
/etc/milton/emails/<email>/properties.json  mail properties (to/subject/cc/bcc)
/etc/milton/emails/<email>/mail             mail spool (inbox/outbox/sent/archive)
/etc/milton/emails/<email>/context          read-only context for the prompts
/etc/milton/emails/<email>/prompt           <schedule>/prompt.md per schedule
```

an `<email>` is valid when its `mail/` folder exists.

`properties.json` at the address root holds the loose per-address settings. its
`mail` section (`to`, `subject`, `cc`, `bcc`) becomes the properties of every
message the worker writes to `mail/outbox/<id>/properties.json`, next to the
generated html body in `mail/outbox/<id>/message.html`, which the dispatcher
reads back: `to` defaults to the address, `subject` to the schedule name, and
`cc` / `bcc` are lists applied as message headers. the body is sent as
`text/html`.

#
#   usage
#

```
make develop [receiver worker dispatcher]   run services locally (all three by default)
make seed ADDR=you@example.com     create a new address
make start                         build and start the stack
make logs                          follow service logs
```

#
#   env
#

copy `.env.sample` to `.env` (the makefile does this on first run) and set the
receiver port and the ses settings.

the worker writes the report html with an openai-compatible chat completions
api, openrouter by default. set `MILTON_WORKER_API_KEY`, and optionally
`MILTON_WORKER_API_URL` and `MILTON_WORKER_MODEL` (`openrouter/free` by
default). the prompts should ask for an html fragment — the reply becomes the
message body.

the dispatcher sends reports with amazon ses. `MILTON_DISPATCHER_SES_FROM` must
be a verified identity in ses, and the region comes from
`MILTON_DISPATCHER_SES_REGION` or `AWS_DEFAULT_REGION`; aws credentials come
from the standard `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` variables or the
instance role.
