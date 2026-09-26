#
#   Dockerfile
#
FROM python:3.10


#
#   working
#
WORKDIR /app


#
#   service
#
ARG SERVICE=receiver


#
#   requirement[s]
#
COPY src/${SERVICE}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


#
#   src
#
COPY src/shared/ ./shared/
COPY src/${SERVICE}/ ./


#
#   command
#
CMD [ "python", "./main.py" ]
