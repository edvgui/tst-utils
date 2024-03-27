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
$ tr-report-loader/venv/bin/python -m tr-report-loader.load_report --help
Usage: python -m tr-report-loader.load_report [OPTIONS]

  Retrieve input file from google drive.

  Arguments:

      TR_DRIVE_FOLDER : Path to the Trade Republic report in google drive.
      TR_OUTPUT_PATH: Path to the folder where the trade republic report
      should be downloaded.     TR_DELETE: Boolean indicating if the report
      should be deleted in google drive after download.

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
