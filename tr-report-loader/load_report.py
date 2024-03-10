import pathlib
import click
import re
import io
import os
import shutil

import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import google.auth.exceptions
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google_api import load_credentials

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

def download_file(service, file_metadata: dict, output_folder: pathlib.Path) -> None:
    """
    Download files to output_folder, the file metadata must be a dict of format {"id": <str>, "name": <str>}
    """
    try:
        request = service.files().get_media(fileId=file_metadata["id"])
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None

    file.seek(0)
    with open(output_folder / file_metadata["name"], "wb") as f:
        shutil.copyfileobj(file, f, length=131072)


def get_tr_reports(service, folder_name: str) -> list[dict]:
    """
    Get the Trade republic reports that are in a specific folder using google drive service object.

    The return type is a list of files metadata as dicts of the format {"id": <str>, "name": <str>}
    """

    folder_dict = (
        service.files()
        .list(
            q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}'",
            fields="files(id, name)",
        )
        .execute()
    )
    folderResult = folder_dict.get("files", [])
    if len(folderResult) == 0:
        return []
    folder_id = folderResult[0].get("id")

    results = (
        service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
    )
    files = results.get("files", [])

    pattern = re.compile(r"pb[0-9]+[.]pdf$")
    return [file for file in files if pattern.match(file["name"])]


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
    "--tr-output-path",
    help="Folder path to download the pdf file(s) to.",
    default=pathlib.Path("input"),
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
)
@click.option(
    "--tr-delete",
    help="Flag to indicate that the trade republic report(s) should be deleted from drive after download.",
    is_flag=True,
)
def main(
    app_credentials: click.Path,
    tr_drive_folder: click.Path,
    tr_output_path: click.Path,
    tr_delete: bool,
) -> None:
    """Retrieve input file from google drive.

    Arguments:

        TR_DRIVE_FOLDER : Path to the Trade Republic report in google drive.
        TR_OUTPUT_PATH: Path to the folder where the trade republic report should be downloaded.
        TR_DELETE: Boolean indicating if the report should be deleted in google drive after download.

    """

    creds = load_credentials(pathlib.Path(app_credentials), SCOPES)

    # Call the Google Drive API
    service = googleapiclient.discovery.build("drive", "v3", credentials=creds)
    tr_reports = get_tr_reports(service, folder_name=tr_drive_folder)

    for report in tr_reports:
        download_file(
            service, file_metadata=report, output_folder=pathlib.Path(tr_output_path)
        )
        if tr_delete:
            # Caution, this will permanently delete the file without moving it to trash
            service.files().delete(fileId=report["id"]).execute()


if __name__ == "__main__":
    main()
