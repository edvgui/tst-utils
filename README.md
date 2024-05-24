# TST Utils

## Introduction

This project contains some helpers to parse a trade republic tst file (pdf report) and use the output data to fill in the belgian TST file that should be sent to state.

This code-base is purely opportunistic, and will rely on the simplest tools it can find to reach its goal.  Consistency of the technology used is not the primary goal, having a solution that works is.

## Prerequisites

The requirements are: 
```
- python>=3.10 
- make
- pip
```
Some tweaking with the gmail api is also necessary, see [tst-sender-readme](./tst_sender/README.md).

## Input files 

The script requires various input files in order to generate a correct TST pdf.
The complete list is the following:

- Personal information file, as json payload, with the following format:
```
{
    "fullName": "FIRSTNAME LASTNAME",
    "nationalRegisterNumber": "",
    "address": [""]
}
```

- Signature file as png or jpg, in order to sign the TST file.

- The credentials json file used to access your gmail account, more information available [here](./tst_sender/README.md).
  Please make sure to add http://localhost:8080 in your allowed redirect urls of your google identifier and make sure to set your google project in production and not testing (otherwise you will have to reconnect to your google account each month because the refresh token will expire).

## Quick start

To run the bash script, just run:

```
venv/bin/python -m main 
```

The options are defined as follow:

```
[xxxxxx@xxxxxx tst-utils]$ venv/bin/python -m main --help
Usage: main.py [OPTIONS] INPUT_FOLDER OUTPUT_FOLDER

  Tool to fill in belgian TST file from trade republic monthly report. This
  tool also creates a draft mail with the generated document and a qr code to
  pay the tax.

Options:
  --tax-signature FILE      Path to a file image containing the signature.
                            [required]
  --tax-person FILE         Path to a file containing the data on the person
                            filling in the form.  [required]
  --app-credentials FILE    Path to the credentials file that can be used to
                            interact with google drive api.  [required]
  --tr-drive-folder TEXT    Folder containing trade republic report(s) in
                            google drive.
  --tr-delete               Flag to indicate that the files in input and
                            output folders should be cleaned.
  --qr-export [mail|photo]  Way to export the QR code, either gmail or google
                            photo.
  --help                    Show this message and exit.
```


## Components
### Parsing Trade Republic transaction report

This is done in python, using pypdf and some naive regexes. There is no guarantee it will continue to work in the future.

See [tr-report-parser](./tr_report_parser/).

### Filling in TST form

This is done in python and relies on the pyMupdf library, written in c and highly optimized. It is highly dependant on the form file used, and has only been tested with https://finance.belgium.be/sites/default/files/Changement%20de%20compte%20formulaire%20TST%20EN.pdf

See [tst-filler](./tst_filler/).

### Generate QR code for payment

This is done in python, using qrcode library.

See [tst-qr](./tst_qr/).

### Send TST form

This one is written in python, using gmail api to prepare a draft email, that can be sent to the belgian administration.  The tst form filled is attached to the email. You can also decide to send the qr code by email or to your google photo library.

See [tst-sender](./tst_sender/).

## Watching trade republic drive folder

This component allows you to watch a google drive folder and wait to get notified by google when your trade republic report(s) get uploaded in the drive folder you are watching. It then automatically process all the reports using the `sync.sh` script. This component, unlike the others, runs continously so it is recommended to execute it on a server. It uses flask to be reachabled by google, which means you also need to ensure the application is reachable via reliable means (port forwarding, tunneling, ...).

### Run the watch component

```
cd tr-report-watch
make install
venv/bin/python -m "tr-report-watch.watch_report"
```

For more details about the argument, please refer to [tr-report-watch README](./tr_report_watch/README.md).
