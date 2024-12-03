# Parse trade republic tst report

**Prerequisites**:
1. Have python>=3.10 installed on your system

**Setup venv and install dependencies**:  
```bash
make install
```

**Run tool**:  
```console
$ venv/bin/python extract_report.py --help
Usage: extract_report.py [OPTIONS] TRANSACTIONS_REPORT

  Extract relevant information from a trade republic tst report document

  Arguments:

      TRANSACTIONS_REPORT: Path to a tax report document that should be parsed.

Options:
  --help  Show this message and exit.
```
