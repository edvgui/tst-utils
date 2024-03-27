#!/bin/sh

set -e

# Define Help function

Help()
{
   # Display Help
   echo ""
   echo "This is the watch version of the TST script, it watches for pdf(s) file in google drive"
   echo "and automatically run the other sync script for them." 
   echo "For more information about the script, run 'sh sync.sh -h'."
   echo
   echo "Syntax: sh watch.sh [-h|s|p|c] input_folder [output_folder]"
   echo "options:"
   echo "h     Display this help and exit."
   echo "s     Set the signature image file path, default value is 'data/signature.jpg'."
   echo "p     Set the personal informations json file path, default value is 'data/citizen.json'."
   echo "c     Set the Gmail credentials json file path, default value is 'data/credentials.json'."
   echo "d     Set the Google drive folder to retrieve the pdf(s) from, default value is 'trade_republic'."
   echo "      This will download all the pdfs in the provided input_folder argument."
   echo "e     This is the endpoint url used by google to send the watch notification upon changes in drive."
   echo "q     Specify the way to export the QR code, either send an email by specifying 'mail'"
   echo "      or upload to google photo by specifying 'photo'."
   echo
   echo "Please make sure to provide options before arguments."
   echo
}

# Set default values for options
SIGNATURE_FILE=$(readlink -f data/signature.jpg)
PERSONAL_INFOS_FILE=$(readlink -f data/citizen.json)
CREDENTIALS_FILE=$(readlink -f data/credentials.json)
GOOGLE_DRIVE_FOLDER="trade_republic"

# Traverse arguments
while getopts ":hs:p:c:d:e:q:" option; do
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
      e) # Endpoint url
        ENDPOINT_URL=$OPTARG;;
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
        echo "Run 'sh watch.sh -h' to get more information about existing options."
        exit;;
   esac
done

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/tr-report-watch"; make install; cd -

./tr-report-watch/venv/bin/python -m \
 "tr-report-watch.watch_report" \
 --app-credentials $CREDENTIALS_FILE \
 --tax-person $PERSONAL_INFOS_FILE \
 --tax-signature $SIGNATURE_FILE \
 --tr-drive-folder $GOOGLE_DRIVE_FOLDER \
 --qr-export $EXPORT_QR \
 --callback-url $ENDPOINT_URL
