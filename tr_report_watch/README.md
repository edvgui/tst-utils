# Download tax report from google drive

**Prerequisites**:
1. Have python>=3.10 installed on your system
2. A project on the google console, with access to the google drive api: https://console.cloud.google.com/workspace-api

**Install dependencies**:  
```bash
make install
```

**Setup google drive api**:
cf. https://developers.google.com/drive/api/quickstart/python


**Run tool**:
```console
$ venv/bin/python -m tr_report_watch.watch_report --help
Usage: python -m tr_report_watch.watch_report [OPTIONS]

  Watch for trade republics reports in a specific google drive folder and
  process them as they are uploaded.

Options:
  --app-credentials FILE    Path to the credentials file that can be used to
                            interact with google drive api.  [required]
  --tax-person FILE         Path to a file containing the data on the person
                            filling in the form.  [required]
  --tax-signature FILE      Path to a file image containing the signature.
                            [required]
  --qr-export [mail|photo]  Way to export the QR code, either gmail or google
                            photo.
  --tr-drive-folder TEXT    Folder containing trade republic report(s) in
                            google drive.  [required]
  --callback-url TEXT       Url used by google to send notifications to upon
                            changes in folder.  [required]
  --help                    Show this message and exit.
```

**Application setup**:

A recommended way to run this component is to host it on a server that you have to make reachable.
In order to do so, either setup yourself the port forwarding or use a tunneling service. 
