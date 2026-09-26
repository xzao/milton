#
#	Makefile
#
.DEFAULT_GOAL := logs


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
	mkdir -p /etc/milton
	if [ -d mnt ]; then rm -rf /etc/milton; ln -s $(CURDIR)/mnt/etc/milton /etc/milton; fi
	pip install pytest
	pip install -r src/receiver/requirements.txt
	pip install -r src/worker/requirements.txt
	pip install -r src/dispatcher/requirements.txt

logs:
	docker-compose logs -f

restart:
	make stop
	make start

seed:
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/mail
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/context
	@mkdir -p mnt/etc/milton/emails/$(ADDR)/prompt/daily
	@echo 'summarise the new mail.' > mnt/etc/milton/emails/$(ADDR)/prompt/daily/prompt.md

shell:
	docker exec -it receiver bash

start:
	docker-compose up -d --build

stop:
	docker-compose down

test:
	@clear
	pytest "${TEST}"
