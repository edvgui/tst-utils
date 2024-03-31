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
   echo "d     Set the Google drive folder to retrieve the pdf(s) from."
   echo "      This will download all the pdfs in the provided input_folder argument."
   echo "r     flag used to decide if input and output folders should be cleaned after the run."
   echo "      If set, you have to specify an export method for the QR code with -q option."
   echo "q     Specify the way to export the QR code, either send an email by specifying 'mail'"
   echo "      or upload to google photo by specifying 'photo'. This option is mandatory only if -r flag is specified."
   echo "arguments:"
   echo "input_folder     Set the input folder for the pdf(s), this argument is mandatory."
   echo "output_folder    Set the output folder for the generated pdf(s) and qr code, default value is 'output'."
   echo
   echo "Please make sure to provide options before arguments."
   echo
}

# Set default values for options
SIGNATURE_FILE=$(readlink -f data/signature.jpg)
PERSONAL_INFOS_FILE=$(readlink -f data/citizen.json)
CREDENTIALS_FILE=$(readlink -f data/credentials.json)
CLEANUP=false

# Traverse arguments
while getopts ":hs:p:c:d:q:r" option; do
   case $option in
      h) # display Help
        Help
        exit;;
      s) # Signature file
        SIGNATURE_FILE=$(readlink -f $OPTARG);;
      p) # Personal informations file
        PERSONAL_INFOS_FILE=$(readlink -f $OPTARG);;
      c) # Gmail credentials file
        CREDENTIALS_FILE=$(readlink -f $OPTARG);;
      d) # Google drive folder
        GOOGLE_DRIVE_FOLDER=$OPTARG;;
      r) # Flag to delete files in input and output folders
        CLEANUP=true;;
      q) # Provide a way to export QR code (mail or google photo)
        case $OPTARG in
          mail|photo) # valid values for -q 
            EXPORT_QR=$OPTARG
            ;;
          *) # Every other values are wrong
             echo "Error: Invalid value '$OPTARG' for option -$option !"
             echo "Possible values are [mail, photo]."
             exit 1
        esac
        ;;
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
  echo "Error: Please provide at least an input folder as argument."
  exit 1
fi

INPUT_DIR=$( cd -- "$1" > /dev/null && pwd )

if [ -z "$2" ]; 
then 
  # If output folder is not set, default to 'output'
  OUTPUT_DIR=$(readlink -f output); 
else
  OUTPUT_DIR=$( cd -- "$2" > /dev/null && pwd )
fi

# Create output dir only if it doesn't exist
mkdir -p $OUTPUT_DIR

# Check if qr code is exported when cleanup is enabled
if [[ $CLEANUP == true ]] && [ -z $EXPORT_QR ]; then
  echo "Error: Please provide a way (with -q option) to export the QR when cleaning up input and output folders."
  echo "Possible values are [mail, photo]."
  exit 1
fi

# Resolve the dir where this file belongs
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE:-$0}" )" &> /dev/null && pwd )

# Initial setup, make sure that everything is installed
cd "$SCRIPT_DIR/tr-report-loader"; make install; cd -
cd "$SCRIPT_DIR/tr-report-parser"; make install; cd -
cd "$SCRIPT_DIR/tst-filler"; make install; cd -
cd "$SCRIPT_DIR/tst-sender"; make install; cd -
cd "$SCRIPT_DIR/tst-qr"; make install; cd -

if [ -n "$GOOGLE_DRIVE_FOLDER" ]; then
  # Download pdf report(s) to input folder
  ./tr-report-loader/venv/bin/python -m \
  "tr-report-loader.load_report" \
  --app-credentials $CREDENTIALS_FILE \
  --tr-drive-folder $GOOGLE_DRIVE_FOLDER \
  --tr-output-path $INPUT_DIR \
  --tr-delete
fi

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
    data=$(./tr-report-parser/venv/bin/python -m tr-report-parser.extract_report "$src_file")

    echo "$data"

    if stat "$qr_code" &> /dev/null; then true; else
        # Generate qr code for payment
        echo "$data" | \
            ./tst-qr/venv/bin/python -m \
            tst-qr.create_qrcode \
            --tax-data - \
            --tax-person $PERSONAL_INFOS_FILE \
            "$qr_code"
        
        if [ "$CLEANUP" = false ]
        then
          # open qr code only if cleanup is disabled
          xdg-open "$qr_code"
        fi
    fi

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

        qr_code_param=()
        if [[ $CLEANUP == true ]]; then
            # if input and output folders cleanup flag is set
            qr_code_param=(--tst-qr $qr_code --qr-export $EXPORT_QR)
        fi

        # Prepare draft email and potentially send qr code
        echo "$data" | \
            ./tst-sender/venv/bin/python -m \
            tst-sender.send_tst \
            --app-credentials $CREDENTIALS_FILE \
            --tax-data - \
            --tax-person $PERSONAL_INFOS_FILE \
            "${qr_code_param[@]}" \
            "$dst_file"
        
        # `|| true` allows you to run on headless (e.g. container) without crashing
        notify-send tst-sender "Created draft email for $dst_file" || true 
    fi
done

if [ "$CLEANUP" = true ]
then  
  rm "$INPUT_DIR"/*
  rm "$OUTPUT_DIR"/*
fi
