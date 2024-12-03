# Fill in TST form

**Prerequisites**:
1. Have python>=3.10 installed on your system

**Install dependencies**:  
```bash
make install
```

**Run tool**:  
```console
$ tst_filler/venv/bin/python -m tst_filler.fill_tob --help
Usage: python -m tst_filler.fill_tob [OPTIONS]

  Fill in the TST form for a given citizen and tax data.

  Arguments:     TAX_DATA : Data containing all the tax information required
  to fill the belgian tst pdf.

      TST_REPORT: Path to trade republic report.

      OUTPUT_FILE : File path where to save the resulting pdf.

      TAX_PERSON : Path to a file containing the data on the person filling in
      the form.

      TAX_SIGNATURE : Path to a file image containing the signature.

      SIGNATURE_LOCATION : Location (city) where the document has been signed.

      FORM_FILE : Belgian tst pdf template file to fill.

Options:
  --tax-data FILE       Path to a file containing the data on the actual tax
                        to pay to the state  [required]
  --output-file FILE    Folder containing trade republic report(s) in google
                        drive.  [required]
  --tax-person FILE     Path to a file containing the data on the person
                        filling in the form.  [required]
  --tax-signature FILE  Path to a file image containing the signature.
                        [required]
  --form-file FILE      Belgian tst  pdf template file to fill.  [required]
  --help                Show this message and exit.
```
