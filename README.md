# services :: milton

milton listens on smtp, runs scheduled prompts over received mail and context,
and mails the resulting reports.

#
#   service[s]
#

- `receiver` — smtp listener; writes accepted mail into the owner's `mail/inbox`.
- `worker` — runs each user's `prompt/<schedule>/prompt.md` on its schedule.
- `dispatcher` — validates and sends finished reports, then archives them.

#
#   data
#

all state lives under `/etc/milton` (host data at `./mnt/etc/milton`; not
committed — gitignored and dockerignored, linked in the devcontainer and
mounted by compose):

```
/etc/milton/emails/<email>/mail      mail spool (inbox/outbox/sent/archive)
/etc/milton/emails/<email>/context   read-only context for the prompts
/etc/milton/emails/<email>/prompt    <schedule>/prompt.md per schedule
```

an `<email>` is valid when its `mail/` folder exists.

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
smtp and port variables.
