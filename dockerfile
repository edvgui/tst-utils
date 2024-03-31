From ubuntu:latest

COPY . tst_utils
WORKDIR tst_utils

USER root

RUN apt-get update && apt-get -y upgrade && \
    apt-get install -y make && \ 
    apt-get install -y podman && \
    apt-get install -y pip &&\
    apt-get install -y python3.10-venv && \
    apt-get install -y vim

# Edit/add parameters here with your own information
ENTRYPOINT sh watch.sh -s data/signature.png -q photo -e MY_CALLBACK_URL