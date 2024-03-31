From fedora:latest

COPY . tst_utils
WORKDIR tst_utils

USER root

RUN dnf install -y make podman pip

# Edit/add parameters here with your own information
ENTRYPOINT sh watch.sh -s data/signature.png -q photo -e MY_CALLBACK_URL