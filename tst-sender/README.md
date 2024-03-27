# Send tst form

**Prerequisites**:
1. Have python>=3.10 installed on your system
2. A project on the google console, with access to the gmail api: https://console.cloud.google.com/workspace-api

**Install dependencies**:  
```bash
make install
```

**Setup google api**:
cf. https://developers.google.com/gmail/api/quickstart/python


**Run tool**:  
```console
tst-sender/venv/bin/python -m tst-sender.send_tst --help
Usage: python -m tst-sender.send_tst [OPTIONS] TST_FORM

  Prepare a draft email with the given tst file for the belgian finance
  administration.

  Arguments:

      TST_FORM: Path to the filled in tax report to send to the
      administration.

      TAX_DATA: Path to a file containing the data on the actual tax to pay to
      the state.

      TAX_PERSON: Path to a file containing the data on the person filling in
      the form.

      TST_QR: Path to a file containing the QR code to pay the tax.

      QR_EXPORT: Way to export the QR code, either gmail or google photo.

Options:
  --app-credentials FILE    Path to the credentials file that can be used to
                            interact with gmail api.  [required]
  --tax-data FILE           Path to a file containing the data on the actual
                            tax to pay to the state.  [required]
  --tax-person FILE         Path to a file containing the data on the person
                            filling in the form.  [required]
  --tst-qr FILE             Path to a file containing the QR code to pay the
                            tax.
  --qr-export [mail|photo]  Way to export the QR code, either by mail or
                            google photo. Default value is mail.
  --help                    Show this message and exit.
```
