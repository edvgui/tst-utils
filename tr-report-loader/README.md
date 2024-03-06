# Send tst form

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
$ tr_report_loader/venv/bin/python tr_report_loader/load_report.py --help
Usage: load_report.py [OPTIONS]

  Retrieve input file from google drive.

  Arguments:

      TR_PATH: Path to the Trade Republic report in google drive.

Options:
  --app-credentials FILE       Path to the credentials file that can be used
                               to interact with google drive api.  [required]
  --tr-drive-folder DIRECTORY  Folder containing trade republic report(s) in
                               google drive.  [required]
  --tr-output-path DIRECTORY   Folder path to download the pdf file(s) to.
                               [required]
  --tr-delete                  Flag to indicate that the trade republic
                               report(s) should be deleted from drive after
                               download.
  --help                       Show this message and exit.
```
