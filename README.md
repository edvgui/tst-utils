# TST Utils

## Introduction

This project contains some helpers to parse a trade republic tst file (pdf report) and use the output data to fill in the belgian TST file that should be sent to state.

This code-base is purely opportunistic, and will rely on the simplest tools it can find to reach its goal.  Consistency of the technology used is not the primary goal, having a solution that works is.

## Prerequisites

The requirements are: 
```
- python>=3.10
- podman 
- make
- pip
```
Some tweaking with the gmail api is also necessary, see [tst-sender-readme](./tst-sender/README.md).

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

- The credentials json file used to access your gmail account, more information available [here](./tst-sender/README.md).
  Please make sure to add http://localhost:8080 in your allowed redirect urls of your google identifier.

## Quick start

To run the bash script, just run:

```
sh sync.sh
```

The options are defined as follow:

```
[xxxxxx@xxxxxx tst-utils]$ sh sync.sh -h
Tool to fill in belgian TST file from trade republic monthly report.
This tool also creates a draft mail with the generated document and a qr code to pay the tax.

Syntax: sh sync.sh [-h|s|p|c] input_folder [output_folder]
options:
h     Display this help and exit.
s     Set the signature image file path, default value is 'data/signature.jpg'.
p     Set the personal informations json file path, default value is 'data/citizen.json'.
c     Set the Gmail credentials json file path, default value is 'data/credentials.json'.
d     Set the Google drive folder to retrieve the pdf(s) from.
      This will download all the pdfs in the provided input_folder argument.
arguments:
input_folder     Set the input folder for the pdf(s), this argument is mandatory.
output_folder    Set the output folder for the generated pdf(s) and qr code, default value is 'output'.

Please make sure to provide options before arguments.
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

This one is written in python, using gmail api to prepare a draft email, that can be sent to the belgian administration.  The tst form filled is attached to the email. You can also decide to send the qr code by email or to your google photo library.

See [tst-sender](./tst-sender/).

## Watching trade republic drive folder

This component allows you to watch a google drive folder and wait to get notified by google when your trade republic report(s) get uploaded in the drive folder you are watching. It then automatically process all the reports using the `sync.sh` script. This component, unlike the others, runs continously so it is recommended to execute it on a server. It uses flask to be reachabled by google, which means you also need to ensure the application is reachable via reliable means (port forwarding, tunneling, ...). For more details, please refer to the readme of the component.

See [tr-report-watch](./tr-report-watch/)