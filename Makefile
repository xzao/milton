#
#	Makefile
#
.DEFAULT_GOAL := logs
.PHONY: develop install logs restart seed shell start stop test


#
#	env[s]
#
$(shell test -f .env || cp .env.sample .env)
include .env
export $(shell sed 's/=.*//' .env)


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

install:
	mkdir -p $(CURDIR)/mnt/etc/milton
	sudo ln -sf $(CURDIR)/mnt/etc/milton /etc/milton
	pip install pytest
	pip install -r src/receiver/requirements.txt
	pip install -r src/worker/requirements.txt
	pip install -r src/dispatcher/requirements.txt

logs:
	docker compose logs -f

process:
	@python bin/milton worker process "${MILTON_CLI_WORKER_ADDRESS}" "${MILTON_CLI_WORKER_SCHEDULE}" --preserve-inbox

restart:
	make stop
	make start

seed:
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/mail
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/context
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/prompt/daily
	@echo 'summarise the new mail as an html email body.' > mnt/etc/milton/emails/$(ADDR)/prompt/daily/prompt.md
	@echo '{"mail": {"to": "$(ADDR)", "subject": "", "cc": [], "bcc": []}}' > mnt/etc/milton/emails/$(ADDR)/properties.json
	@sudo chown -R 1000:1000 mnt

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
