# agents :: milton

`milton` is a small python service stack that listens on smtp, runs scheduled
prompts over received mail and context, and emails the resulting reports. It is
three services — `receiver`, `worker`, `dispatcher` — sharing one data volume.

Everything is written in a deliberately literal, comment-first style: every
file, every section and every step is announced by a lowercase comment banner.
This document describes that style so new code, new files and new services look
like they were always there.

When in doubt, **copy the shape of an existing file** instead of inventing one.
There is no linter config and no formatter config — the existing files are the
spec.


#
#   layout
#

```
milton/
├── src/
│   ├── receiver/
│   │   ├── main.py          smtp listener entrypoint
│   │   ├── handler.py       smtp handler (importable / testable)
│   │   └── requirements.txt aiosmtpd
│   ├── worker/
│   │   ├── main.py          scheduler + prompt loop entrypoint
│   │   ├── task.py          prompt run logic (importable / testable)
│   │   └── requirements.txt openai, scheduler
│   ├── dispatcher/
│   │   ├── main.py          ses sender entrypoint
│   │   ├── message.py       ses destination / content (importable / testable)
│   │   └── requirements.txt boto3
│   └── shared/
│       ├── __init__.py      re-exports util, mail, uuid7
│       ├── util.py          env helpers + address inference + log setup
│       ├── mail.py          email parse / body / attachments
│       └── uuid7.py         uuidv7 generator
├── bin/
│   └── milton               developer command (service + command front door)
├── test/
│   ├── conftest.py          adds src/ to sys.path for imports
│   └── receiver/  worker/  dispatcher/  shared/
├── mnt/                     runtime data — not committed (linked/mounted at /etc/milton)
├── .devcontainer/           devcontainer (runs `make install`)
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── pyrightconfig.json       editor import paths (src + each service dir)
├── .env.sample
├── .dockerignore
├── .gitignore
└── README.md
```

Rules:

- Code lives under `src/`; developer commands under `bin/`; data lives under
  `mnt/`.
- Three services, one per directory, each with its own `main.py` and
  `requirements.txt`.
- `src/shared/` holds code used by more than one service; it is copied into
  every image and importable via `PYTHONPATH=src` in development.
- Each `main.py` is a **script**, not a module: it runs at import time. Do **not**
  add an `if __name__ == '__main__':` guard.
- `bin/milton` is the developer front door: `milton <service> <command>
  [flag ...]`, one nested subparser per service and command, dispatched through
  `set_defaults(run = ...)` with a `#   command[s]` function per command named
  `<service>_<command>`. It is a script like `main.py` (no `__main__` guard) and
  bootstraps `sys.path` in a `#   path` section before its imports. It is never
  copied into an image and no service imports it.
- A service may carry one service-local importable module beside its `main.py`
  (`handler.py`, `task.py`, `message.py`) when its logic needs tests. Such a
  module does no work at import, takes `root` instead of reading the data tree
  from a module constant, and is imported bare (`from task import process`);
  `main.py` keeps the env, directories, registration and loop.
- Tests live under `test/` (one folder per component); run them with `make test`.
  Do not add packaging metadata or `pyproject.toml` unless asked.
- The `receiver` carries one small handler class (aiosmtpd's contract); it is
  the one allowed class.


#
#   file[s]
#

Every Python file, the Makefile, the Dockerfile and `bin/milton` opens with a
banner naming the file path. In Python the imports follow the banner directly,
with no blank line, and two blank lines close the import block:

```python
#
#   src/receiver/main.py
#
from shared import mail, util, uuid7
import logging


#
#   var[s]
#
```

- The banner is a bare `#`, then `#   <path>`, then `#`.
- Paths are relative to the repo root, using `/`.
- `bin/milton` keeps its `#!/usr/bin/python3` shebang above the banner.
- Data and config files carry no banner: `docker-compose.yml`,
  `pyrightconfig.json`, `requirements.txt`, `.env.sample`. The ignore files use
  one short `# <group>` comment above each group of patterns.
- Python files use a plain `#`. The Makefile uses `#` + TAB for sections
  (`#\tMakefile`). Match whichever file you are in.


#
#   section[s]
#

Sections split a file into named blocks. Every section is:

```
#
#   <name>
#
```

- The name is **lowercase**, a bare noun or verb, singular.
- Add a **`[s]` suffix when the section may hold more than one item**:
  `var[s]`, `get[s]`, `attachment[s]`, `service[s]`, `target[s]`. Singular when
  it holds one: `logging`, `loop`, `handler`, `controller`, `send`, `process`,
  `register`, `interval`, `list`, `model`, `generate`, `path`, `parser`,
  `run`, `working`, `command`.
- Sections are separated by **two blank lines**.
- Sections run top-to-bottom in dependency order. The established order is:

  | File | Section order |
  |---|---|
  | `src/receiver/main.py` | `var[s]` → `logging` → `controller` → `loop` |
  | `src/receiver/handler.py` | `handler` |
  | `src/worker/main.py` | `var[s]` → `logging` → `register` → `loop` |
  | `src/worker/task.py` | `interval` → `get[s]` → `list` → `model` → `generate` → `process` |
  | `src/dispatcher/main.py` | `var[s]` → `logging` → `dir[s]` → `send` → `loop` |
  | `src/dispatcher/message.py` | `address` → `destination` → `content` |
  | `src/shared/util.py` | `env[s]` → `email[s]` → `log` |
  | `src/shared/mail.py` | `parse` → `body` → `attachment[s]` |
  | `src/shared/uuid7.py` | `new` |
  | `Dockerfile` | `working` → `service` → `requirement[s]` → `src` → `command` |
  | `bin/milton` | `path` → `import[s]` → `var[s]` → `logging` → `command[s]` → `parser` → `run` |
  | `Makefile` | `env[s]` → `target[s]` → `arg[s]` |
  | `test/conftest.py`, `test/<service>/conftest.py` | `var[s]` → `path` |
  | `test/<component>/test_*.py` | `make[s]` (tree / stub builders) → `test[s]` |

- The header banner is a section too, but no `import[s]` banner follows it: the
  imports sit directly under the header. `bin/milton` is the exception — it must
  fix `sys.path` first, so there the imports get their own `#   import[s]`
  section after `#   path`.


#
#   step[s]
#

Inside a section, **every logical step gets its own one-line lowercase comment
on the line directly above it**, followed by a blank line before the next step.
This is the single most important habit in this codebase.

Rules:

- The comment is a terse fragment — a noun phrase or bare verb. Lowercase.
  No full stop. No trailing punctuation. Never a sentence.
- Common vocabulary: `# value`, `# value check`, `# path`, `# path check`,
  `# return`, `# log`, `# folder iterate`, `# message read`, `# message parse`,
  `# outbox make`, `# archive move`, `# sent move`, `# ses send`,
  `# send guard`, `# process guard`, `# sleep`, `# dir make`,
  `# address check`, `# to check`, `# to valid check`.
- The shape is `<noun>` for an assignment and `<noun> <verb>` for an action:
  `check` for a test, `iterate` for a loop, `read` / `make` / `move` for file
  work, `guard` for a `try`.
- Use the `[s]` suffix on the trailing noun when the step touches a collection:
  `# item[s]`, `# folder iterate`, `# part iterate`.
- `# return` goes directly above the `return` in any function with more than a
  couple of lines. It is the last step.
- Guard clauses and one-liners inside a section still get their own comment when
  they are a distinct step.
- No trailing whitespace, one space after `#`.

Verbatim example — `src/shared/util.py`:

```python
def env_int(name, default):

    # value
    value = os.getenv(name)

    # value check
    if not value:
        return default

    # return
    return int(value)
```


#
#   function[s]
#

- `def name(params):` is always followed by a **blank line** before the first
  step comment. Never a docstring — the step comments replace it. The one
  exception is the `Handler.__init__` two-liner, which has no blank line and no
  step comments.
- Small helpers used by one section live in that section, above the function
  that uses them (`text_cut` and `html_extract` sit in `#   generate`,
  `get_text` heads `#   get[s]`).
- Handle exceptions with `raise Exception('<lowercase message>')`. Messages are
  lowercase, unpunctuated, and use bracket context where useful:
  `raise Exception('report missing recipient')`,
  `raise Exception(f"invalid recipient '{to}'")`.
- Return `None` when nothing applies (`return None`), `''` / `[]` when an empty
  text or list is the natural answer (`get_text`, `util.emails`). Return
  `True`/`False` for success/failure of a mutation (`return True` on a
  successful send, `ok` from a `bin/milton` command).
- Type hints are **rare and optional**. Do not annotate unless a wire-facing
  helper genuinely benefits.
- No decorators, no classes except the `receiver` handler, no `__all__`, no
  property/`@classmethod` patterns. Plain functions only.


#
#   alignment
#

Alignment is what makes the style recognisable. Apply it to **contiguous
blocks**; a lone statement keeps a single space.

1. **Assignments** — pad the left-hand sides so the `=` line up:

```python
EMAILS     = '/etc/milton/emails'
INTERVAL   = util.env_int('MILTON_DISPATCHER_INTERVAL', 60)
SES_FROM   = util.env('MILTON_DISPATCHER_SES_FROM', 'milton@localhost')
SES_REGION = util.env('MILTON_DISPATCHER_SES_REGION')
```

2. **Keyword arguments** — spaces *around* `=` (unlike PEP 8) and a single
   aligned column, including inside multi-line calls:

```python
controller = Controller(
    Handler(EMAILS),
    hostname = '0.0.0.0',
    port     = PORT
)
```

3. **Hand-written config dicts** — a space before the `:` and aligned colons
   when the keys are of similar width:

```python
items.append({
    'name' : name,
    'data' : data
})
```

   Wire-format / JSON payload dicts are the exception: keys are double-quoted
   JSON and left single-spaced, unaligned:

```python
data = {
    "to": to,
    "subject": subject,
    "cc": cc,
    "bcc": bcc
}
```

4. **Short dicts stay on one line** when they fit and are a single step.
5. **Multi-line literals close on their own line** at the owning indentation —
   `)`, `}`, `]` alone, not trailing the last item.
6. **Nested dicts/lists** open their own block and indent by 4.

Alignment is a manual, hand-tuned column. Do not run Black/autopep8/`ruff
format` over the code — it will collapse the keyword-argument spacing.


#
#   import[s]
#

Imports sit immediately after the file banner with no blank line between the
banner and the block, then **two blank lines** after the block.

Order:

1. `from x import y` lines first — `shared`, the service's own module, and any
   third-party class (`from aiosmtpd.controller import Controller`), or
   `from . import ...` inside `shared/__init__.py`.
2. Then every plain `import x` — standard library and third-party together — in
   one alphabetical block (`argparse`, `boto3`, `datetime`, `email`,
   `functools`, `json`, `logging`, `openai`, `os`, `scheduler`, `sys`, `time`).

One module per `import` line. Never `from x import *`. No import sorting tools
— the order above is intentional and stable.

A service's own modules (e.g. `src/receiver/handler.py`) are imported bare —
`from handler import Handler` — not as `receiver.handler`. The service
directory is on the path at runtime (the script's own directory, or
`PYTHONPATH=src` in dev, or the flattened `/app` in the image) and is listed in
`pyrightconfig.json` `extraPaths` so the editor resolves it too.

```python
#
#   src/worker/main.py
#
from shared import util
from task import interval, list_schedules, process
import functools
import logging
import os
import scheduler
import time
```


#
#   quoting & literal[s]
#

- **Defaults to single quotes** for paths, env names and plain strings:
  `'/etc/milton/emails'`, `'MILTON_WORKER_INTERVAL'`, `'0.0.0.0'`.
- **Double quotes only for wire-format / JSON payloads**: `"to"`, `"subject"`,
  `"role": "system"`, `"ToAddresses"`. Keep that split.
- f-strings for every interpolation: `f"{EMAILS}/{user}/mail/inbox"`. No `%` or
  `.format()`.
- Booleans are `True` / `False`. Collections are plain `{}` / `[]` — no
  `dict()` / `list()` constructors.


#
#   naming
#

- `snake_case` for functions, variables, parameters, module names.
- Modules are a single lowercase word: `util`, `mail`, `uuid7`, `receiver`,
  `worker`, `dispatcher`.
- Module-level constants are `SCREAMING_SNAKE_CASE`: `EMAILS`, `PORT`, `TICK`,
  `SES_FROM`.
- Function prefixes carry meaning and should be reused:
  - `get_*` — fetch one value (`get_text`, `get_prompt`, `get_context`,
    `get_properties(root, user, section)`, `get_key`).
  - `list_*` — fetch many, return a list (`list_schedules`).
  - `emails` / `valid` — infer valid addresses from the data tree.
  - `<noun>_<verb>` — a small transform (`text_cut`, `html_extract`); in tests,
    a tree / stub builder (`user_make`, `message_make`, `model_make`).
  - `<service>_<command>` — a `bin/milton` command (`worker_process`).
- The one class is the `receiver` `Handler`; its instances are lowercase.
- Avoid abbreviations that are not already in the codebase (`fp`, `id`, `raw`,
  `sub` are all established — use them). Caught exceptions are `error`.


#
#   control flow
#

- **Compare with `== None`, never `is None`.** This is consistent across the
  codebase and intentional to the style:

```python
if key == None:
    raise Exception('model key missing')
```

- Use `if not x:` for falsy checks, as in `if not os.path.isdir(root):` and
  `if not value:` for an unset env var.
- Guard clauses keep their body on its own indented line, under their own step
  comment — `continue`, `return None`, `return default` or `raise`:

```python
# dir check
if not os.path.isdir(path):
    continue
```

- `None` is returned explicitly (`return None`); an implicit bare `return` is
  only used where the code already does so.
- No `match`, no ternary expressions, no comprehensions — build lists with an
  `# item[s]` / `append` loop. A default is an `or` fallback
  (`section.get('to') or user`) or an `if` / `else` block.
- Loops are the outer shape of every service: each `main.py` ends in a
  `while True:` … `time.sleep(...)` with the sleep as the last step (`# sleep`).
  The receiver is the exception — aiosmtpd runs in its own thread, so its loop
  is a bare `while True: time.sleep(3600)` keep-alive.


#
#   logging
#

- Configured once, in each `main.py` (and `bin/milton`), as its own section,
  through the shared `util.log_setup()` so every component prints one format:

```python
#
#   logging
#
util.log_setup()
```

```
2026-09-29 12:04:15  INFO  main.py:18 ➔ [user] registered
2026-09-29 12:04:16  WARN  main.py:24 ➔ [user] refused[...]
2026-09-29 12:04:18  ERROR task.py:30 ➔ [user] failed[...]
```

- Change the format only in `util.log_setup` (`WARNING` prints as `WARN`,
  `CRITICAL` as `CRIT`); never add a `basicConfig` elsewhere.

- Use the `logging` module only — no `print`.
- Log lines are f-strings with **bracketed context** and a lowercase verb:

```python
logging.info(f"[{id}] received[{envelope.mail_from}] to[{address}]")
logging.info(f"[{user}] [{schedule}] reported[{len(bodies)}]")
logging.info(f"[{id}] sent[{to}] message[{message_id}]")
logging.error(f"[{name}] failed[{error}]")
```

- `logging.info` for state changes, `logging.debug` for the quiet loop detail,
  `logging.warning` for a refusal, `logging.error` for a step that failed.


#
#   service[s]
#

Three services share one data tree under `/etc/milton`. Each is one directory under
`src/` with a `main.py` and a `requirements.txt`, wired in `docker-compose.yml`.

- **receiver** — `aiosmtpd` listener. Its `Handler` accepts a recipient only
  when `util.valid(EMAILS, address)` (the address has a `mail/` folder) and
  appends it to `envelope.rcpt_tos` — aiosmtpd only auto-records recipients
  when there is no `handle_RCPT` hook — then writes `message.eml` +
  attachments into `mail/inbox/<uuid7>/`, logging rejected addresses and save
  failures.
- **worker** — `register()` adds one `scheduler` job per schedule in the
  address `properties.json` `schedules` list (and makes the `mail/` folders).
  The loop calls it again every `MILTON_WORKER_RELOAD` seconds, adding and
  removing only the jobs that changed, and runs the jobs via
  `scheduler.exec_jobs()`. Every schedule of an address shares one inbox, so the
  first to run takes the mail; `register` warns when an address lists more than
  one.
  Each run is `task.process(root, user, schedule)`: it reads the shared prompt
  and the user's context, takes messages from `mail/inbox` in sorted order
  while they fit in `MILTON_WORKER_INPUT_LIMIT` less the context (at least one; the rest wait
  for the next run), and calls `generate(prompt, context, messages, template)` once.
  The model sees tagged blocks — `<mail>` of
  `<message id from to date subject attachments>`, then `<context>`, then
  `<template>` (every `.html` file under `prompt/` or `context/`, via
  `get_template`; never cut), then `<prompt>` last, each file a
  `<file path="prompt/…">` — and a system message telling the model to return
  the template filled in, keeping its markup, and
  naming each block's role and saying mail and context are data, not
  instructions. `task.tag_guard` escapes any `</file`, `</message`, `</mail`,
  `</context`, `</prompt` inside a block so its text cannot forge one.
  `generate` cuts the mail and context (never the prompt) to
  `MILTON_WORKER_INPUT_LIMIT` characters and asks the configured
  chat-completions model (`task.model`, openai client against openrouter by
  default, reply capped at `MILTON_WORKER_MAX_TOKENS`) for the html body —
  writes a single `mail/outbox/<uuid7>/message.html` + `properties.json`
  (to/subject/cc/bcc from the address `properties.json` `mail` section), and
  archives the batch. `task.process(root, user, schedule, preserve_inbox =
  True)` leaves the batch in `mail/inbox` — what `bin/milton worker process
  [address] --preserve-inbox` (and `make process`) uses to preview a report
  locally, with the fixed schedule label `preview`.
- **dispatcher** — scans each user's `mail/outbox`, validates the recipient,
  sends `message.html` with amazon ses (`message.py` builds the destination and
  content from `properties.json`), and moves the report to `mail/sent`. `send`
  returns `False` without sending when `AWS_SECRET_ACCESS_KEY` is unset.

`src/shared/` holds the reusable pieces: `util` (env + address inference),
`mail` (parse/body/attachments), `uuid7` (uuidv7).

Adding a service means: create `src/<name>/main.py` + `requirements.txt`, add
the `from shared import ...` line, and add a `build.args.SERVICE` block to
`docker-compose.yml`. Then list it wherever the three services are listed:
the `pip install -r` lines and the `develop` default in the `Makefile`, the
service dir loop in `bin/milton`, and `extraPaths` in `pyrightconfig.json`.


#
#   config
#

All state lives under `/etc/milton`. `mnt/` is **not committed** — it is
gitignored and dockerignored; on the host the data lives at `./mnt/etc/milton`,
linked to `/etc/milton` in the devcontainer and bind-mounted at `/etc/milton`
by compose:

```
/etc/milton/emails/<email>/properties.json  address properties (mail, schedules sections)
/etc/milton/emails/<email>/mail             inbox / outbox / sent / archive
/etc/milton/emails/<email>/context          read-only context files
/etc/milton/emails/<email>/prompt           prompt text — every file, shared by all schedules
```

`properties.json` at the address root holds the address settings, one section
per concern. Its `mail` section (`to`, `subject`, `cc`, `bcc`) is copied into
every `mail/outbox/<uuid7>/properties.json` the worker writes and applied by the
dispatcher; `to` defaults to the address, `subject` to the schedule. Its
`schedules` section lists the schedules to run — a schedule exists when it is
listed.

A `<email>` is valid when its `mail/` folder exists. `util.emails(EMAILS)` lists
them; `util.valid(EMAILS, address)` checks one. The `schedules` entries are
interval tokens (`5m`, `30m`, `1h`, `daily`, `weekly`, via `task.interval` and
`jobs.cyclic`) or a day list and `HH:MM` times (`daily 08:00`,
`weekdays 08:30 17:00`, `mon,fri 09:00`, via `task.timing` and `jobs.weekly`),
the times in the `TZ` zone (`UTC` by default); `register` logs and
skips an entry `timing` refuses. All schedules share one
prompt: `prompt/` is read like `context/` — every file under it, sorted, each
wrapped in a `<file path="prompt/…">` block, is the prompt.

Environment variables carry a **project prefix**:

```
MILTON_UID
MILTON_GID
MILTON_TIMEZONE
MILTON_RECEIVER_SMTP_PORT
MILTON_WORKER_INTERVAL
MILTON_WORKER_API_KEY
MILTON_WORKER_API_URL
MILTON_WORKER_MODEL
MILTON_WORKER_INPUT_LIMIT
MILTON_WORKER_MAX_TOKENS
MILTON_WORKER_RELOAD
MILTON_DISPATCHER_INTERVAL
MILTON_DISPATCHER_SES_FROM
MILTON_DISPATCHER_SES_REGION
MILTON_CLI_WORKER_ADDRESS
```

`MILTON_TIMEZONE` is read by no service: `docker-compose.yml` and the Makefile
pass it on as the standard `TZ` (`UTC` by default), which sets log timestamps
and the worker's schedule zone.

`MILTON_CLI_*` variables feed developer commands only (`make process` passes
`MILTON_CLI_WORKER_ADDRESS` to `bin/milton worker process`); no service reads
them. Every variable has a default in code (`util.env` / `util.env_int`),
and an empty value counts as unset.

the dispatcher's ses client also reads the standard `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` and `AWS_DEFAULT_REGION`
variables through boto3.

`.env.sample` is the committed template: bare `KEY=` lines, no values, no
quotes, one per line, sorted alphabetically. `make` copies it to `.env` when
`.env` is missing.


#
#   makefile & docker
#

The Makefile mirrors the file style: banner, `#` + TAB section banners, two
blank lines between sections, TAB-indented recipes, and a leading `@` when the
recipe just runs something (`@python bin/milton ...`, `@clear`, `@git pull`).
`.DEFAULT_GOAL` is `logs`; every target belongs in `.PHONY`.

Targets are one lowercase word and alphabetical inside `#\ttarget[s]`:
`develop`, `install`, `logs`, `process`, `restart`, `seed`, `shell`, `start`,
`stop`, `test`, `upgrade`, `version`. A `%` catch-all in its own last section,
`#\targ[s]`, swallows extra goal arguments so targets can read them from
`$(MAKECMDGOALS)`:

- `develop [service ...]` runs the listed services concurrently in dev
  (`receiver`, `worker`, `dispatcher` — all three by default);
- `process` previews a report for `MILTON_CLI_WORKER_ADDRESS` (every address
  when empty) without consuming the inbox;
- `seed ADDR=you@example.com` creates a new address folder with `mail/`,
  `context/`, a `prompt/prompt.md` and a `properties.json` scheduled `daily`;
- `test [component ...]` runs one test folder (all of `test/` by default);
- `upgrade` pulls and rebuilds the stack; `version <x.y.z>` writes `VERSION`,
  commits and tags `v<x.y.z>` on a clean tree.

The Dockerfile keeps `#   working` → `#   service` → `#   requirement[s]` →
`#   src` → `#   command`, FROM `python:3.10`, `WORKDIR /app`, a build `ARG
SERVICE` to select the service, and the spaced array form
`CMD [ "python", "./main.py" ]`.

`docker-compose.yml` runs the three services, each `build`ing with
`args: SERVICE: <name>` and running as
`user: ${MILTON_UID:-1000}:${MILTON_GID:-1000}` so the files it writes through
the bind mount stay owned by the host user, with `env_file: .env`,
`environment: TZ: ${MILTON_TIMEZONE:-UTC}`,
`restart: unless-stopped` and the bind mount `./mnt/etc/milton:/etc/milton`.
`.dockerignore` keeps `mnt` (and `.git`, `.env*`, `__pycache__`) out of the
build context.

Important: the source is copied to `/app` **without** the `src/` level, so
`main.py` imports `from shared import ...`, not `from src.shared …`. Never
introduce a `src` package or relative imports that assume one.


#
#   test[s]
#

Tests live under `test/`, one folder per component (`receiver/`, `worker/`,
`dispatcher/`, `shared/`; `milton/` for `bin/milton` once it has tests), plus
`test/conftest.py` which puts `src/` on
`sys.path` so tests can `from shared import ...`. A component that carries its
own importable module adds a folder `conftest.py` putting `src/<service>` on
`sys.path` (`test/receiver/`, `test/worker/`, `test/dispatcher/`), so tests can
`from task import process`. pytest is the runner and is wired only through the
Makefile: `make install` installs it, `make test` runs all of `test/`, and
`make test <component>/...` runs one folder. Therefore:

- keep pytest; do not add unittest / nose / tox;
- name files `test_<component>.py` (plus `test_<module>.py` for a second
  module, as `test_message.py`) and tests `test_<function>_<behaviour>`
  (`test_get_prompt_missing_raises`);
- write tests in this same banner-and-step style, with builders in `#   make[s]`
  and tests in `#   test[s]`;
- stub the model and env with pytest's `monkeypatch` — no network calls;
- tests must run without starting any service (no servers, no sockets);
- tests must pass on a fresh repo — build every tree they need under
  `tmp_path`, never under `/etc/milton` or `mnt/`;
- do not add `pyproject.toml`, `pytest.ini` or `setup.cfg` unless asked.


#
#   check[s]
#

Before finishing any change:

- [ ] file opens with the `#` / `#   <path>` / `#` banner, path correct;
- [ ] every block is a `#` section banner — lowercase, `[s]` only when plural;
- [ ] every step has its one-line lowercase comment, and a blank line after it;
- [ ] every multi-line function has a blank line after `def`, and `# return`
      above its `return`;
- [ ] `=`, `:`, and keyword arguments are aligned in every contiguous block;
- [ ] single quotes, except JSON payload dicts;
- [ ] `== None` (never `is None`), guards under their own step comment,
      `Exception('lowercase message')`;
- [ ] two blank lines around section banners, one blank line between functions
      inside a section (`util.py`, `task.py`);
- [ ] AGENTS.md and README.md still match the change (layout, section order,
      env vars, make targets, data tree);
- [ ] no docstrings, no `__main__` guard, no `print`;
- [ ] no new dependency without a reason, and any new one is added to the
      service's `requirements.txt`;
- [ ] no formatter run; `from` imports first, then `import` alphabetical;
- [ ] `python -m py_compile` passes for every touched file, and `make test`
      passes.


#
#   skeleton
#

A canonical new service module, in the house style:

```python
#
#   src/service/main.py
#
from shared import util
import logging
import os
import time


#
#   var[s]
#
EMAILS = '/etc/milton/emails'


#
#   logging
#
util.log_setup()


#
#   loop
#
while True:

    # user iterate
    for user in util.emails(EMAILS):
        logging.info(f"[{user}] tick")

    # sleep
    time.sleep(1)
```

Then wire it in as described under `#   service[s]`.


