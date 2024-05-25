From fedora:latest

COPY . tst_utils
WORKDIR tst_utils

RUN make watch_install

# Edit/add parameters here with your own information
ENTRYPOINT venv/bin/python -m tr_report_watch.watch_report --tax-signature data/signature.png --qr-export photo --callback-url MY_CALLBACK_URL