# Fill in TST form

**Prerequisites**:
1. Have podman installed on your system (no need for nodejs)

**Install dependencies**:  
```bash
make install
```

**Run tool**:  
```console
$ ./run --help
Usage: fillTob [options] <output-file>

Fill in the TST form for a given citizen and tax data

Arguments:
  output-file                   The name of the filled in form file

Options:
  --form-file <path>            Path to the TST form file (pdf) that we should fill in. (default: "/home/guillaume/Documents/taxes/tst-filler/form-original.pdf")
  --signature-location <value>  The geographical location where the signature of the document is taking place (default: "Bruxelles")
  --signature-file <path>       Path to the image file that should be used as a signature.
  --tax-person <path>           Path to a file containing the data on the person filling in the form
  --tax-data <path>             Path to a file containing the data on the actual tax to pay to the state
  -h, --help                    display help for command
```
