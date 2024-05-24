venv:
	python3 -m venv venv

install: venv
	venv/bin/pip install -U --upgrade-strategy=eager \
		-r ../tr_report_loader/requirements.txt \
		-r ../tr_report_parser/requirements.txt \
		-r ../tst_qr/requirements.txt \
		-r ../tst_sender/requirements.txt \
		-r ../tst_filler/requirements.txt \
		-r requirements.txt
