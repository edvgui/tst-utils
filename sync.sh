#!/bin/sh

set -e

# Define Help function

Help()
{
   # Display Help
   echo "Tool to fill in belgian TST file from trade republic monthly report."
   echo "This tool also creates a draft mail with the generated document and a qr code to pay the tax."
   echo
   echo "Syntax: sh sync.sh [-h|s|p|c] input_folder [output_folder]"
   echo "options:"
   echo "h     Display this help and exit."
   echo "s     Set the signature image file path, default value is 'data/signature.jpg'."
   echo "p     Set the personal informations json file path, default value is 'data/citizen.json'."
   echo "c     Set the Gmail credentials json file path, default value is 'data/credentials.json'."
   echo "arguments:"
   echo "input_folder     Set the input folder for the pdf(s), this argument is mandatory."
   echo "output_folder    Set the output folder for the generated pdf(s) and qr code, default value is 'output'."
   echo
   echo "Please make sure to provide options before arguments."
   echo
}

# Set default values for options
SIGNATURE_FILE="$(pwd)/data/signature.jpg"
PERSONAL_INFOS_FILE="$(pwd)/data/citizen.json"
CREDENTIALS_FILE="$(pwd)/data/credentials.json"

# Traverse arguments
while getopts ":hs:p:c:" option; do
   case $option in
      h) # display Help
        Help
        exit;;
      s) # Signature file
        SIGNATURE_FILE="$(pwd)/$OPTARG";;
      p) # Personal informations file
        PERSONAL_INFOS_FILE="$(pwd)/$OPTARG";;
      c) # Gmail credentials file
        CREDENTIALS_FILE="$(pwd)/$OPTARG";;
      \?) # Invalid option
        echo "Error: Invalid option '-$OPTARG'"
        echo "Run 'sh sync.sh -h' to get more information about existing options."
        exit;;
   esac
done

echo " ________  ______   ________      __    __  ________  ______  __        ______  ";
echo "/        |/      \ /        |    /  |  /  |/        |/      |/  |      /      \ ";
echo "\$\$\$\$\$\$\$\$//\$\$\$\$\$\$  |\$\$\$\$\$\$\$\$/     \$\$ |  \$\$ |\$\$\$\$\$\$\$\$/ \$\$\$\$\$\$/ \$\$ |     /\$\$\$\$\$\$  |";
echo "   \$\$ |  \$\$ \__\$\$/    \$\$ | _____ \$\$ |  \$\$ |   \$\$ |     \$\$ |  \$\$ |     \$\$ \__\$\$/ ";
echo "   \$\$ |  \$\$      \    \$\$ |/     |\$\$ |  \$\$ |   \$\$ |     \$\$ |  \$\$ |     \$\$      \ ";
echo "   \$\$ |   \$\$\$\$\$\$  |   \$\$ |\$\$\$\$$/ \$\$ |  \$\$ |   \$\$ |     \$\$ |  \$\$ |      \$\$\$\$\$\$  |";
echo "   \$\$ |  /  \__\$\$ |   \$\$ |       \$\$ \__\$\$ |   \$\$ |    _\$\$ |_ \$\$ |____ /  \__\$\$ |";
echo "   \$\$ |  \$\$    \$\$/    \$\$ |       \$\$    \$\$/    \$\$ |   / \$\$   |\$\$      |\$\$    \$\$/ ";
echo "   \$\$/    \$\$\$\$\$\$/     \$\$/         \$\$\$\$\$\$/     \$\$/    \$\$\$\$\$\$/ \$\$\$\$\$\$$/  \$\$\$\$\$\$/  ";
echo "                                                                                ";
echo "                                                                                ";

# shift (remove) all the processed parameters (variable $OPTIND)
shift $(($OPTIND - 1))

# Read input and output folder arguments
if [ -z "$1" ]; then
  # If input folder is not set, fail.
  echo "Please provide at least an input folder as argument."
  exit 1
fi

INPUT_DIR=$( cd -- "$1" > /dev/null && pwd )

if [ -z "$2" ]; 
then 
  # If output folder is not set, default to 'output'
  OUTPUT_DIR="$(pwd)/output"; 
else
  OUTPUT_DIR="$(pwd)/$2"
fi

# Create output dir only if it doesn't exist
mkdir -p $OUTPUT_DIR

# Resolve the dir where this file belongs
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Initial setup, make sure that everything is installed
cd "$SCRIPT_DIR/tr-report-parser"; make install; cd -
cd "$SCRIPT_DIR/tst-filler"; make install; cd -
cd "$SCRIPT_DIR/tst-sender"; make install; cd -
cd "$SCRIPT_DIR/tst-qr"; make install; cd -

# Go over all the pdf in the input folder
cd "${SCRIPT_DIR}"
for src_file in "$INPUT_DIR"/*.pdf; do
    filename=$(basename -- "$src_file")
    dst_file="${OUTPUT_DIR}/"$(basename -- "$src_file")
    qr_code="${OUTPUT_DIR}/${filename%.*}.png"

    # Print progress
    echo "Processing $src_file"

    if stat "$dst_file" &> /dev/null && stat "$qr_code" &> /dev/null; then
        # Nothing to do, the file already exists
        echo "$dst_file and $qr_code already exist"
        continue
    fi

    # Parse tst report
    data=$(./tr-report-parser/venv/bin/python tr-report-parser/extract_report.py "$src_file")

    echo "$data"

    if stat "$dst_file" &> /dev/null; then true; else
        # Fill in tst form
        echo "$data" | \
            ./tst-filler/run \
            --form-file data/form-original.pdf \
            --signature-file $SIGNATURE_FILE \
            --tax-person $PERSONAL_INFOS_FILE \
            --tax-data - \
            data/$(basename -- "$src_file")
        mv data/$(basename -- "$src_file") "$dst_file"

        # Prepare draft email
        echo "$data" | \
            ./tst-sender/venv/bin/python \
            tst-sender/send_tst.py \
            --app-credentials $CREDENTIALS_FILE \
            --tax-data - \
            --tax-person $PERSONAL_INFOS_FILE \
            "$dst_file"
        
        notify-send tst-sender "Created draft email for $dst_file"
    fi

    if stat "$qr_code" &> /dev/null; then true; else
        # Generate qr code for payment
        echo "$data" | \
            ./tst-qr/venv/bin/python \
            tst-qr/create_qrcode.py \
            --tax-data - \
            --tax-person $PERSONAL_INFOS_FILE \
            "$qr_code"
        
        notify-send tst-qr "Created payment qr code: $qr_code"
    fi
done
