# TST Utils

## Introduction

This project contains some helpers to parse a trade republic tst file (pdf report) and use the output data to fill in the belgian TST file that should be sent to state.

This code-base is purely opportunistic, and will rely on the simplest tools it can find to reach its goal.  Consistency of the technology used is not the primary goal, having a solution that works is.

## Prerequisites

The requirements are: 
```
- python>=3.10
- podman 
```
Some tweaking with the gmail api is also necessary, see [tst-sender-readme](./tst-sender/README.md).

## Input files 

The script requires various input files in order to generate a correct TST pdf.
The complete list with is the following:

- Personal file informations as json file with the following format:
```
{
    "fullName": "FIRSTNAME LASTNAME",
    "nationalRegisterNumber": "",
    "address": [""]
}
```

- Signature file as png or jpg, in order to sign the TST file.

- The credentials json file used to access your gmail account, more information available [here](./tst-sender/README.md).

## Quick start

To run the bash script, just run:

```
sh sync.sh
```

The options are defined as follow:

```
[xxxxx@xxxxx tst-utils]$ sh sync.sh -h
Tool to fill in belgian TST file from trade republic monthly report.
This tool also creates a draft mail with the generated document and a qr code to pay the tax.

Syntax: sh sync.sh [-h|i|o|s|p|c]
options:
h     Display this help and exit.
i     Set the input folder for the pdf(s), default value is 'input'.
o     Set the output folder for the generated pdf(s) and qr code, default value is 'output'.
s     Set the signature image file path, default value is 'data/signature.jpg'.
p     Set the personal informations json file path, default value is 'data/citizen.json'.
c     Set the Gmail credentials json file path, default value is 'data/credentials.json'.
```


## Components
### Parsing Trade Republic transaction report

This is done in python, using pypdf and some naive regexes. There is no guarantee it will continue to work in the future.

See [tr-report-parser](./tr-report-parser/).

### Filling in TST form

This one is written in Javascript, and runs with node, inside a podman container.  The tool relies on the pdf-lib library, it is highly dependant on the form file used, and has only been tested with https://finance.belgium.be/sites/default/files/Changement%20de%20compte%20formulaire%20TST%20EN.pdf

See [tst-filler](./tst-filler/).

### Generate QR code for payment

This is done in python, using qrcode library.

See [tst-qr](./tst-qr/).

### Send TST form

This one is written in python, using gmail api to prepare a draft email, that can be sent to the belgian administration.  The tst form filled is attached to the email.

See [tst-sender](./tst-sender/).
