import pathlib
import click
import uuid
import time
import sys
import signal
import subprocess
import queue
from dataclasses import dataclass
from typing import Optional
from time import strftime, localtime
from datetime import datetime
from urllib.parse import urljoin
from threading import Thread, Event
from flask import Flask, request, make_response

import googleapiclient.discovery
from googleapiclient.errors import HttpError
from helpers.google_api import load_credentials, get_tr_reports

"""
TODO 1) finish tr-report-watch (readme and maybe other files) + test it more
     2) make proper watch.sh tools (with arguments, ...)
     3) Figure out how to cleanup input and output after a run
     4) Check what happens with xdg-open when running in standard terminal (headless) and 
        figure out a way to easily get the qr code when running in containers (gmail, ...)
     5) Create dockerfile for the repo (with watch.sh as entrypoint)
     6) update global readme with new features
"""

@dataclass
class DriveWatcher:
    folder_name: str
    callback_url: str
    channel: Optional[dict] = None
    event: Event = False # Event triggered upon shutdown

app: Flask = Flask(__name__)

tasks_queue = queue.SimpleQueue()

def handle_tasks(service, drive_watcher: DriveWatcher):
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
                file_path = pathlib.Path(__file__)
                with open(file_path.parent / 'output.txt', 'w+') as fd:
                    try:
                        result = subprocess.run(["sh", "sync.sh", "-s", "data/signature.png" ,"-p" ,"data/citizen.json", "-d", "trade_republic", "input"], cwd=str(file_path.parent.parent), check=True, stdout=fd, stderr=fd, text = True)
                    except subprocess.CalledProcessError as e:
                        print(str(e))

@app.route("/drive_webhook", methods=['POST'])
def google_drive_webhook_callback():
    """
    Google drive change notifications webhook

    For more information about it see https://developers.google.com/drive/api/guides/push
    """

    resource_id = request.headers['X-Goog-Resource-Id']
    channel_id = request.headers['X-Goog-Channel-Id']
    resourceState = request.headers['X-Goog-Resource-State']
    resourceChange = request.headers.get('X-Goog-Changed', None)
    channelExpiration = request.headers['X-Goog-Channel-Expiration']

    if resourceState == "sync":
        # Time when the notification channel expires
        expiration_date = datetime.strptime(channelExpiration, '%a, %d %b %Y %H:%M:%S %Z')
        print("Drive sync")
        return make_response("sync", 200)
    
    if resourceState == "update" and resourceChange == "children":
        # Only trigger tst_utils script if a new file is added in folder
        tasks_queue.put(resource_id)

    print("Drive webhook handled")
    return make_response("Webhook received", 200)


def start_watching_folder(service, drive_watcher: DriveWatcher) -> dict:
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
        raise RuntimeError(
            f"The folder with name {drive_watcher.folder_name} does not exist on your google drive !"
        )

    folder_id = folderResult[0].get("id")

    # max expiration time for google drive file channel is 1 day
    date_now: datetime = datetime.now()
    new_date: datetime = date_now.replace(day=date_now.day + 1)
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

    channel_expiration_date = strftime('%Y-%m-%d %H:%M:%S', localtime(int(channel["expiration"])/1000))
    print(f"Channel {channel["id"]} used to watch folder {drive_watcher.folder_name} will expire at {channel_expiration_date}")

    return channel

def stop_watching_folder(service, drive_watcher: DriveWatcher):
    """
    Stop watching for changes, this function uses as input the channel dict returned during creation of the watch channel.
    """
    try:
        service.channels().stop(body={"id": drive_watcher.channel["id"], "resourceId": drive_watcher.channel["resourceId"]}).execute()
    except HttpError as e:
        if e.status_code != 404:
            raise e

def renew_google_watch(service, drive_watcher: DriveWatcher):
    """
    From Google documentation : Currently there is no automatic way to renew a notification channel. 
        When a channel is close to its expiration, you must create a new one by calling the watch method

    Google drive api has a maximum watch channel duration of 1 day (1 hour by default) 
    for google drive file so we need to recreate the watch channel every day.
    """

    while not drive_watcher.event.is_set():
        drive_watcher.channel = start_watching_folder(service, drive_watcher)

        # Wait 1 day or until stop event is triggered
        drive_watcher.event.wait(24*3600)

        # stop the channel to avoid having overlapping channels
        stop_watching_folder(service, drive_watcher)

@click.command()
@click.option(
    "--app-credentials",
    help="Path to the credentials file that can be used to interact with google drive api.",
    default=pathlib.Path("credentials.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    "--tr-drive-folder",
    help="Folder containing trade republic report(s) in google drive.",
    default=pathlib.Path("trade_republic"),
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    required=True,
)
@click.option(
    "--callback-url",
    help="Url used by google to send notifications to upon changes in folder.",
    type=click.STRING,
    required=True,
)
def main(
    app_credentials: click.Path,
    tr_drive_folder: click.Path,
    callback_url: str,
) -> None:
    """Retrieve input file from google drive.

    Arguments:

        TR_DRIVE_FOLDER : Path to the Trade Republic report in google drive.
        CALLBACK_URL :  Url used to reach the flask application, this will be 
            used by google to send notification upon changes in google drive folder. 

    """

    creds = load_credentials(pathlib.Path(app_credentials))

    # Call the Google Drive API
    service = googleapiclient.discovery.build("drive", "v3", credentials=creds)

    drive_watcher = DriveWatcher(folder_name=tr_drive_folder, callback_url=callback_url, event=Event())

    # Create thread that will start watching google drive and automatically renew the watch channel
    renew_google_watch_thread = Thread(target=renew_google_watch, args=(service, drive_watcher), daemon=True)
    renew_google_watch_thread.daemon = True
    renew_google_watch_thread.start()
    
    flask_app_thread = Thread(target=app.run, args=("0.0.0.0", 8000,), daemon=True) # run flask app
    flask_app_thread.start()

    queue_app_thread = Thread(target=handle_tasks, args=(service, drive_watcher), daemon=True) # run queue handling task
    queue_app_thread.start()

    def signal_handler(signal, frame):
        print("Cleaning, please wait ...")

        if drive_watcher.channel:
            stop_watching_folder(service, drive_watcher)
        
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("Initial setup done !")
        
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
