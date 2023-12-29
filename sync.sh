#!/bin/sh

set -e

# Read input arguments
INPUT_DIR=$( cd -- "$1" &> /dev/null && pwd )
OUTPUT_DIR=$( cd -- "$2" &> /dev/null && pwd )

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
    else
        # Parse tst report
        data=$(./tr-report-parser/venv/bin/python tr-report-parser/extract_report.py "$src_file")

        echo "$data"

        # Fill in tst form
        echo "$data" | \
            ./tst-filler/run \
            --form-file data/form-original.pdf \
            --signature-file data/signature.jpg \
            --tax-person data/citizen.json \
            --tax-data - \
            data/$(basename -- "$src_file")
        mv data/$(basename -- "$src_file") "$dst_file"

        # Prepare draft email
        echo "$data" | \
            ./tst-sender/venv/bin/python \
            tst-sender/send_tst.py \
            --app-credentials data/credentials.json \
            --tax-data - \
            --tax-person data/citizen.json \
            "$dst_file"
        
        # Generate qr code for payment
        echo "$data" | \
            ./tst-qr/venv/bin/python \
            tst-qr/create_qrcode.py \
            --tax-data - \
            --tax-person data/citizen.json \
            "$qr_code"
    fi
done
