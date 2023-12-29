# Pay tst

**Prerequisites**:
1. Have python>=3.10 installed on your system

**Install dependencies**:  
```bash
make install
```


**Run tool**:  
```console
$ venv/bin/python create_qrcode.py --help
Usage: create_qrcode.py [OPTIONS] OUTPUT_FILE

  Create a QR Code containing all payment info for the tst.

  Arguments:

      OUTPUT_FILE: Path to the generated qr code image.

Options:
  --tax-data FILE    Path to a file containing the data on the actual tax to
                     pay to the state  [required]
  --tax-person FILE  Path to a file containing the data on the person filling
                     in the form  [required]
  --help             Show this message and exit.
```
