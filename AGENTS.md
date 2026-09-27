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
│   │   └── requirements.txt scheduler
│   ├── dispatcher/
│   │   ├── main.py          report sender entrypoint
│   │   └── requirements.txt stdlib only (empty)
│   └── shared/
│       ├── __init__.py      re-exports util, mail, uuid7
│       ├── util.py          env helpers + address inference
│       ├── mail.py          email parse / body / attachments
│       └── uuid7.py         uuidv7 generator
├── test/
│   ├── conftest.py          adds src/ to sys.path for imports
│   └── receiver/  worker/  dispatcher/  shared/
├── mnt/                     runtime data — not committed (linked/mounted at /etc/milton)
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.sample
└── README.md
```

Rules:

- Code lives under `src/`; data lives under `mnt/`.
- Three services, one per directory, each with its own `main.py` and
  `requirements.txt`.
- `src/shared/` holds code used by more than one service; it is copied into
  every image and importable via `PYTHONPATH=src` in development.
- Each `main.py` is a **script**, not a module: it runs at import time. Do **not**
  add an `if __name__ == '__main__':` guard.
- Tests live under `test/` (one folder per component); run them with `make test`.
  Do not add packaging metadata or `pyproject.toml` unless asked.
- The `receiver` carries one small handler class (aiosmtpd's contract); it is
  the one allowed class.


#
#   file[s]
#

Every text file — Python, Makefile, Dockerfile, and any new one — opens with a
banner naming the file path, then a blank line (two in Python):

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
  `register`, `interval`, `list`, `prompt`, `working`, `command`.
- Sections are separated by **two blank lines**.
- Sections run top-to-bottom in dependency order. The established order is:

  | File | Section order |
  |---|---|
  | `src/receiver/main.py` | `var[s]` → `logging` → `controller` → `loop` |
  | `src/receiver/handler.py` | `handler` |
  | `src/worker/main.py` | `var[s]` → `logging` → `dir[s]` → `interval` → `list` → `get[s]` → `prompt` → `process` → `register` → `loop` |
  | `src/dispatcher/main.py` | `var[s]` → `logging` → `dir[s]` → `send` → `loop` |
  | `src/shared/util.py` | `env[s]` → `email[s]` |
  | `src/shared/mail.py` | `parse` → `body` → `attachment[s]` |
  | `src/shared/uuid7.py` | `new` |
  | `Dockerfile` | `working` → `service` → `requirement[s]` → `src` → `command` |
  | `Makefile` | `env[s]` → `target[s]` |

- The header banner is a section too — but it is separated from the imports by
  only the standard blank lines, never by a second banner.


#
#   step[s]
#

Inside a section, **every logical step gets its own one-line lowercase comment
on the line directly above it**, followed by a blank line before the next step.
This is the single most important habit in this codebase.

Rules:

- The comment is a terse fragment — a noun phrase or bare verb. Lowercase.
  No full stop. No trailing punctuation. Never a sentence.
- Common vocabulary: `# value`, `# value none`, `# return`, `# folder iterate`,
  `# message read`, `# message parse`, `# report`, `# outbox make`,
  `# archive move`, `# smtp send`, `# smtp quit`, `# sleep`, `# dir make`,
  `# address check`, `# to check`, `# to valid check`.
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

    # value none
    if value == None:
        return default

    # return
    return int(value)
```


#
#   function[s]
#

- `def name(params):` is always followed by a **blank line** before the first
  step comment. Never a docstring — the step comments replace it.
- Handle exceptions with `raise Exception('<lowercase message>')`. Messages are
  lowercase, unpunctuated, and use bracket context where useful:
  `raise Exception('report missing recipient')`,
  `raise Exception(f"invalid recipient '{to}'")`.
- Return `None` when nothing applies (`return None`). Return `True`/`False` for
  success/failure of a mutation (`return True` on a successful send).
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
EMAILS    = '/etc/milton/emails'
INTERVAL  = util.env_int('MILTON_DISPATCHER_INTERVAL', 60)
SMTP_HOST = util.env('MILTON_DISPATCHER_SMTP_HOST', 'localhost')
```

2. **Keyword arguments** — spaces *around* `=` (unlike PEP 8) and a single
   aligned column, including inside multi-line calls:

```python
controller = Controller(
    Handler,
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
    "to": user,
    "subject": schedule
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

1. First-party / relative imports first (`from shared import ...`,
   `from . import ...`).
2. Then the standard library and third-party modules in one alphabetical block
   (`datetime`, `email`, `functools`, `json`, `logging`, `os`, `scheduler`,
   `smtplib`, `time`, `aiosmtpd`).

One module per line. `import x`, not `from x import *`. No import sorting tools
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
from shared import mail, util, uuid7
import datetime
import functools
import json
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
  `"type": "A"`. Keep that split.
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
  `SMTP_HOST`.
- Function prefixes carry meaning and should be reused:
  - `get_*` — fetch a scalar (`get_prompt`, `get_context`).
  - `list_*` — fetch many, return a list (`list_schedules`).
  - `emails` / `valid` — infer valid addresses from the data tree.
- The one class is the `receiver` `Handler`; its instances are lowercase.
- Avoid abbreviations that are not already in the codebase (`fp`, `id`, `raw`
  are all established — use them).


#
#   control flow
#

- **Compare with `== None`, never `is None`.** This is consistent across the
  codebase and intentional to the style:

```python
if value == None:
    return default
```

- One-line guard clauses are welcome, with the statement on the same line:

```python
if not util.valid(EMAILS, address): return '550 not accepted'
```

- Use `if not x:` for falsy checks, as in `if not os.path.isdir(root):`.
- `None` is returned explicitly (`return None`); an implicit bare `return` is
  only used where the code already does so.
- No `match`, no ternary expressions, no comprehensions beyond the existing
  trivial `[line.rstrip() for line in fp]`.
- Loops are the outer shape of every service: each `main.py` ends in a
  `while True:` … `time.sleep(...)` with the sleep as the last step (`# sleep`).


#
#   logging
#

- Configured once, in each `main.py`, as its own section:

```python
logging.basicConfig(
    level = logging.INFO
)
```

- Use the `logging` module only — no `print`.
- Log lines are f-strings with **bracketed context** and a lowercase verb:

```python
logging.info(f"[{id}] received[{envelope.mail_from}] to[{address}]")
logging.info(f"[{user}] [{schedule}] processed[{name}]")
logging.info(f"[{id}] sent[{to}]")
```

- `logging.info` for state changes, `logging.debug` for the quiet loop detail.


#
#   service[s]
#

Three services share one data tree under `/etc/milton`. Each is one directory under
`src/` with a `main.py` and a `requirements.txt`, wired in `docker-compose.yml`.

- **receiver** — `aiosmtpd` listener. Its `Handler` accepts a recipient only
  when `util.valid(EMAILS, address)` (the address has a `mail/` folder), then
  writes `message.eml` + attachments into `mail/inbox/<uuid7>/`.
- **worker** — registers one `scheduler` job per `prompt/<schedule>/prompt.md`
  and runs them via `scheduler.exec_jobs()`. Each run reads the prompt, the
  user's context and the inbox, calls `report()` (stub for now), writes
  `mail/outbox/<uuid7>/report.md` + `report.json`, and archives the inbox.
- **dispatcher** — scans each user's `mail/outbox`, validates the recipient,
  sends via `smtplib`, and moves the report to `mail/sent`.

`src/shared/` holds the reusable pieces: `util` (env + address inference),
`mail` (parse/body/attachments), `uuid7` (uuidv7).

Adding a service means: create `src/<name>/main.py` + `requirements.txt`, add
the `from shared import ...` line, and add a `build.args.SERVICE` block to
`docker-compose.yml`.


#
#   config
#

All state lives under `/etc/milton`. `mnt/` is **not committed** — it is
gitignored and dockerignored; on the host the data lives at `./mnt/etc/milton`,
linked to `/etc/milton` in the devcontainer and bind-mounted at `/etc/milton`
by compose:

```
/etc/milton/emails/<email>/mail      inbox / outbox / sent / archive
/etc/milton/emails/<email>/context   read-only context files
/etc/milton/emails/<email>/prompt    <schedule>/prompt.md per schedule
```

A `<email>` is valid when its `mail/` folder exists. `util.emails(EMAILS)` lists
them; `util.valid(EMAILS, address)` checks one. The schedule folder names are
interval tokens: `5m`, `30m`, `1h`, `daily`, `weekly`.

Environment variables carry a **project prefix**:

```
MILTON_RECEIVER_SMTP_PORT
MILTON_WORKER_INTERVAL
MILTON_DISPATCHER_INTERVAL
MILTON_DISPATCHER_SMTP_HOST
MILTON_DISPATCHER_SMTP_PORT
MILTON_DISPATCHER_SMTP_FROM
MILTON_DISPATCHER_SMTP_USER
MILTON_DISPATCHER_SMTP_PASS
```

`.env.sample` is the committed template: bare `KEY=` lines, no values, no
quotes, one per line.


#
#   makefile & docker
#

The Makefile mirrors the file style: banner, `#` + TAB section banners, two
blank lines between sections, TAB-indented recipes, and a leading `@` when the
recipe just runs something (`@python src/receiver/main.py`, `@clear`).

Targets are one lowercase word and alphabetical inside `#\ttarget[s]`:
`develop`, `install`, `logs`, `restart`, `seed`, `shell`, `start`, `stop`,
`test`, plus a `%` catch-all (`arg[s]`) that accepts extra goal arguments.
`develop [service ...]` runs the listed services concurrently in dev
(`receiver`, `worker`, `dispatcher` — all three by default). `test
[component/...]` runs one test folder. `seed ADDR=you@example.com` creates a
new address folder.

The Dockerfile keeps `#   working` → `#   service` → `#   requirement[s]` →
`#   src` → `#   command`, FROM `python:3.10`, `WORKDIR /app`, a build `ARG
SERVICE` to select the service, and the spaced array form
`CMD [ "python", "./main.py" ]`.

`docker-compose.yml` runs the three services, each `build`ing with
`args: SERVICE: <name>`, `env_file: .env`, `restart: unless-stopped`, and the
bind mount `./mnt/etc/milton:/etc/milton`. `.dockerignore` keeps `mnt` (and `.git`, `.env*`,
`__pycache__`) out of the build context.

Important: the source is copied to `/app` **without** the `src/` level, so
`main.py` imports `from shared import ...`, not `from src.shared …`. Never
introduce a `src` package or relative imports that assume one.


#
#   test[s]
#

Tests live under `test/`, one folder per component (`receiver/`, `worker/`,
`dispatcher/`, `shared/`), plus `test/conftest.py` which puts `src/` on
`sys.path` so tests can `from shared import ...`. pytest is the runner and is
wired only through the Makefile: `make install` installs it, `make test` runs
all of `test/`, and `make test <component>/...` runs one folder. Therefore:

- keep pytest; do not add unittest / nose / tox;
- name files `test_<module>.py` and tests `test_<behaviour>`;
- write tests in this same banner-and-step style;
- tests must run without starting any service (no servers, no sockets);
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
- [ ] `== None` (never `is None`), one-line guards,
      `Exception('lowercase message')`;
- [ ] two blank lines between sections and between top-level functions;
- [ ] no docstrings, no `__main__` guard, no `print`;
- [ ] no new dependency without a reason, and any new one is added to the
      service's `requirements.txt`;
- [ ] no formatter run; imports are first-party first;
- [ ] `python -m py_compile` passes for every touched file.


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
ROOT = '/etc/milton/emails'


#
#   logging
#
logging.basicConfig(
    level = logging.INFO
)


#
#   loop
#
while True:

    # user iterate
    for user in util.emails(ROOT):
        logging.info(f"[{user}] tick")

    # sleep
    time.sleep(1)
```

Then wire it into `docker-compose.yml` with a `build.args.SERVICE` block.



