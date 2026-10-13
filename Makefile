#
#	Makefile
#
.DEFAULT_GOAL := logs
.PHONY: develop flush init install logs preview restart shell start stop test upgrade version


#
#	env[s]
#
$(shell test -f .env || cp .env.sample .env)
include .env
export $(shell sed 's/=.*//' .env)
export TZ := $(or $(MILTON_TIMEZONE),UTC)


#
#	target[s]
#
develop:
	@services="$(filter-out $@,$(MAKECMDGOALS))"; \
	[ -n "$$services" ] || services="receiver worker dispatcher"; \
	for service in $$services; do \
		PYTHONPATH=src python src/$$service/main.py & \
	done; \
	wait

flush:
	@addresses="$(filter-out $@,$(MAKECMDGOALS))"; \
	[ -n "$$addresses" ] || addresses="$$(ls mnt/etc/milton/staples 2>/dev/null)"; \
	outboxes=""; \
	for address in $$addresses; do \
		outboxes="$$outboxes mnt/etc/milton/staples/$$address/mail/outbox"; \
	done; \
	reports="$$(find $$outboxes -mindepth 1 -maxdepth 1 2>/dev/null)"; \
	if [ -z "$$reports" ]; then \
		echo "outbox empty"; \
		exit 0; \
	fi; \
	echo "$$reports"; \
	printf "flush $$(echo "$$reports" | wc -l) report(s)? [y/N] "; \
	read answer; \
	if [ "$$answer" != "y" ]; then \
		echo "flush cancelled"; \
		exit 0; \
	fi; \
	echo "$$reports" | xargs rm -rf; \
	echo "outbox flushed"

init:
	@address="$(filter-out $@,$(MAKECMDGOALS))"; \
	skel="/etc/milton/skel"; \
	folder="mnt/etc/milton/staples/$$address"; \
	case "$$address" in \
		*@*) ;; \
		*) echo "usage: make init <email>"; exit 1 ;; \
	esac; \
	if [ ! -d "$$skel" ]; then \
		echo "skel missing '$$skel'"; \
		exit 1; \
	fi; \
	if [ -e "$$folder" ]; then \
		echo "address exists '$$folder'"; \
		exit 1; \
	fi; \
	mkdir -p "$$folder/repo"; \
	for sub in mail/inbox mail/outbox mail/sent mail/archive site/inbox site/archive; do \
		mkdir -p "$$folder/$$sub"; \
	done; \
	cp -r "$$skel/." "$$folder/"; \
	sudo chown -R $(or $(MILTON_UID),1000):$(or $(MILTON_GID),1000) "$$folder"; \
	echo "address created '$$folder'"

install:
	mkdir -p $(CURDIR)/mnt/etc/milton
	sudo ln -sfnT $(CURDIR)/mnt/etc/milton /etc/milton
	mkdir -p /etc/milton/skel
	cp -r --update=none $(CURDIR)/etc/milton/skel/. /etc/milton/skel/
	pip install pytest
	pip install -r src/receiver/requirements.txt
	pip install -r src/worker/requirements.txt
	pip install -r src/dispatcher/requirements.txt

logs:
	docker compose logs -f

preview:
	@python bin/milton worker process "${MILTON_CLI_WORKER_ADDRESS}" --preserve-inbox

restart:
	make stop
	make start

shell:
	docker exec -it receiver bash

start:
	docker compose up -d --build

stop:
	docker compose down

test:
	@clear
	pytest $(or $(addprefix test/,$(filter-out $@,$(MAKECMDGOALS))),test/)

upgrade:
	@git pull
	@docker compose up -d --build --force-recreate

version:
	@NEW_VERSION="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ -z "$$NEW_VERSION" ]; then \
		echo "Usage: make version <version>"; \
		echo "Example: make version 1.0.0.0 or make version 1.0.0.0-rc1"; \
		exit 1; \
	fi; \
	if git rev-parse "v$$NEW_VERSION" >/dev/null 2>&1; then \
		echo "Error: Version tag v$$NEW_VERSION already exists."; \
		exit 1; \
	fi; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Working directory is not clean. Please commit or stash your changes."; \
		git status --short; \
		exit 1; \
	fi; \
	echo "$$NEW_VERSION" > VERSION; \
	git add VERSION; \
	git commit -m "Version $$NEW_VERSION"; \
	git tag "v$$NEW_VERSION"; \
	echo "Successfully created version v$$NEW_VERSION"


#
#	arg[s]
#
%:
	@true
