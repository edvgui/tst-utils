import pathlib
import click
import uuid
import time
import sys
import signal
import queue
from main import process_tst
from dataclasses import dataclass
from typing import Optional
from time import strftime, localtime
from datetime import datetime, timedelta
from urllib.parse import urljoin
from threading import Thread, Event
from flask import Flask, request, make_response

import googleapiclient.discovery
from googleapiclient.errors import HttpError
from helpers.google_api import load_credentials, get_tr_reports


@dataclass
class DriveWatcher:
    folder_name: Optional[str] = None
    callback_url: Optional[str] = None
    channel: Optional[dict] = None
    event: Event = False  # Event triggered upon shutdown


drive_watcher = DriveWatcher(event=Event())

app: Flask = Flask(__name__)

tasks_queue = queue.SimpleQueue()


def handle_tasks(
    service,
    tax_person: str,
    tax_signature: str,
    credentials_file: str,
    qr_export: str,
) -> None:
    while not drive_watcher.event.is_set():
        try:
            resource_id = tasks_queue.get(timeout=1)
        except queue.Empty:
            # we block for only 1 second in to be able to interrupt the thread.
            pass
        else:
            # consume task
            files = get_tr_reports(service, drive_watcher.folder_name)
            if len(files) > 0:
                # Only run the script if there are remaining pdf report(s) to process
                process_tst(
                    input_folder="input",
                    tax_signature=tax_signature,
                    tax_person=tax_person,
                    app_credentials=credentials_file,
                    tr_drive_folder=drive_watcher.folder_name,
                    tr_delete=True,
                    qr_export=qr_export,
                )


@app.route("/drive_webhook", methods=["POST"])
def google_drive_webhook_callback():
    """
    Google drive change notifications webhook

    For more information about it see https://developers.google.com/drive/api/guides/push
    """

    resource_id = request.headers.get("X-Goog-Resource-Id", None)
    channel_id = request.headers.get("X-Goog-Channel-Id", None)
    resourceState = request.headers.get("X-Goog-Resource-State", None)
    resourceChange = request.headers.get("X-Goog-Changed", None)
    channelExpiration = request.headers.get("X-Goog-Channel-Expiration", None)

    if resourceState == "sync":
        # Time when the notification channel expires
        expiration_date = datetime.strptime(
            channelExpiration, "%a, %d %b %Y %H:%M:%S %Z"
        )
        print("Drive sync")
        return make_response("sync", 200)

    if (
        resourceState == "update"
        and resourceChange in ["children", "properties"]
        and channel_id == drive_watcher.channel["id"]
    ):
        # Only trigger tst_utils script if a new file is added in folder
        # And if the notification channel id matches with ours
        tasks_queue.put(resource_id)

    print("Drive webhook handled")
    return make_response("Webhook received", 200)


def start_watching_folder(service) -> dict:
    """
    Start watching for changes in a specific folder, here we are looking for files creation.
    Return a dict containing information about the watch channel of the folder.
    """
    folder_dict = (
        service.files()
        .list(
            q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{drive_watcher.folder_name}'",
            fields="files(id, name)",
        )
        .execute()
    )
    folderResult = folder_dict.get("files", [])
    if len(folderResult) == 0:
        folder = (
            service.files()
            .create(
                body={
                    "name": drive_watcher.folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                },
                fields="id",
            )
            .execute()
        )
        folder_id = folder.get("id")
    else:
        folder_id = folderResult[0].get("id")

    # max expiration time for google drive file channel is 1 day
    date_now: datetime = datetime.now()
    new_date: datetime = date_now + timedelta(days=1)
    channel = (
        service.files()
        .watch(
            fileId=folder_id,
            body={
                "id": str(uuid.uuid1()),
                "type": "web_hook",
                "address": urljoin(drive_watcher.callback_url, "/drive_webhook"),
                "expiration": int(new_date.timestamp() * 1000),
            },
        )
        .execute()
    )

    channel_expiration_date = strftime(
        "%Y-%m-%d %H:%M:%S", localtime(int(channel["expiration"]) / 1000)
    )
    print(
        f"Channel {channel['id']} used to watch folder {drive_watcher.folder_name} will expire at {channel_expiration_date}"
    )

    return channel


def stop_watching_folder(service):
    """
    Stop watching for changes, this function uses as input the channel dict returned during creation of the watch channel.
    """
    try:
        service.channels().stop(
            body={
                "id": drive_watcher.channel["id"],
                "resourceId": drive_watcher.channel["resourceId"],
            }
        ).execute()
    except HttpError as e:
        if e.status_code != 404:
            raise e


def renew_google_watch(service):
    """
    From Google documentation : Currently there is no automatic way to renew a notification channel.
        When a channel is close to its expiration, you must create a new one by calling the watch method

    Google drive api has a maximum watch channel duration of 1 day (1 hour by default)
    for google drive file so we need to recreate the watch channel every day.
    """

    while not drive_watcher.event.is_set():
        drive_watcher.channel = start_watching_folder(service)

        # Wait 1 day or until stop event is triggered
        drive_watcher.event.wait(24 * 3600)

        # stop the channel to avoid having overlapping channels
        stop_watching_folder(service)


@click.command(
    name="tst-watch",
    help="Watch for trade republics reports in a specific google drive folder and process them as they are uploaded.",
)
@click.option(
    "--app-credentials",
    help="Path to the credentials file that can be used to interact with google drive api.",
    default=pathlib.Path("data/credentials.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    "--tax-person",
    help="Path to a file containing the data on the person filling in the form.",
    default=pathlib.Path("data/citizen.json"),
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--tax-signature",
    help="Path to a file image containing the signature.",
    default=pathlib.Path("data/signature.jpg"),
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--qr-export",
    help="Way to export the QR code, either gmail or google photo.",
    default="mail",
    type=click.Choice(["mail", "photo"]),
    required=False,
)
@click.option(
    "--tr-drive-folder",
    help="Folder containing trade republic report(s) in google drive.",
    default="trade_republic",
    type=click.STRING,
    required=True,
)
@click.option(
    "--callback-url",
    help="Url used by google to send notifications to upon changes in folder.",
    type=click.STRING,
    required=True,
)
def main(
    tr_drive_folder: str,
    callback_url: str,
    app_credentials: Optional[click.Path] = "data/credentials.json",
    tax_person: Optional[click.Path] = "data/citizen.json",
    tax_signature: Optional[click.Path] = "data/signature.jpg",
    qr_export: Optional[click.Choice] = "mail",
) -> None:
    """Watch for trade republics reports in a specific google drive folder and process them as they are uploaded.

    Arguments:

        TR_DRIVE_FOLDER : Folder containing trade republic report(s) in google drive.

        CALLBACK_URL :  Url used to reach the flask application, this will be
            used by google to send notification upon changes in google drive folder.

        APP_CREDENTIALS : Path to the credentials file that can be used to interact with google drive api.

        TAX_PERSON : Path to a file containing the data on the person filling in the form.

        TAX_SIGNATURE : Path to a file image containing the signature.

        QR_EXPORT : Way to export the QR code, either gmail or google photo.

    """

    # Create input directory if it does not already exist
    input_dir = pathlib.Path("input/")
    input_dir.mkdir(exist_ok=True)

    creds = load_credentials(pathlib.Path(app_credentials))

    # Call the Google Drive API
    service = googleapiclient.discovery.build("drive", "v3", credentials=creds)

    drive_watcher.folder_name = tr_drive_folder
    drive_watcher.callback_url = callback_url

    # Create thread that will start watching google drive and automatically renew the watch channel
    renew_google_watch_thread = Thread(
        target=renew_google_watch, args=(service,), daemon=True
    )
    renew_google_watch_thread.daemon = True
    renew_google_watch_thread.start()

    # start flask
    flask_app_thread = Thread(
        target=app.run,
        args=(
            "0.0.0.0",
            8000,
        ),
        daemon=True,
    )  # run flask app
    flask_app_thread.start()

    # run queue handling task
    queue_app_thread = Thread(
        target=handle_tasks,
        args=(
            service,
            tax_person,
            tax_signature,
            app_credentials,
            qr_export,
        ),
        daemon=True,
    )
    queue_app_thread.start()

    def signal_handler(signal, frame):
        print("Cleaning, please wait ...")

        if drive_watcher.channel:
            stop_watching_folder(service)

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("Initial setup done !")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
