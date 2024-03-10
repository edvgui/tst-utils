SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR/tr-report-watch"; make install; cd -

CREDENTIALS_FILE="data/credentials.json"
GOOGLE_DRIVE_FOLDER="trade_republic"

./tr-report-watch/venv/bin/python \
 "tr-report-watch/watch_report.py" \
 --app-credentials $CREDENTIALS_FILE \
 --tr-drive-folder $GOOGLE_DRIVE_FOLDER \
 --callback-url "https://probable-ultimately-heron.ngrok-free.app"
