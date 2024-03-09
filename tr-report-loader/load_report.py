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


# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/drive",
]


def load_token(token_file: pathlib.Path) -> google.oauth2.credentials.Credentials:
    """
    Load the token from the given file, if it expired, refresh it.
    Always write the token back to the file (even if it is not refreshed).

    :param token_file: The file that should contain the token to authenticate
        the user of the mail box.
    """
    creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
        str(token_file),
        SCOPES,
    )

    if creds.expired and creds.refresh_token:
        # If the credentials expired, refresh them
        creds.refresh(google.auth.transport.requests.Request())

    if not creds.valid:
        # If at this point the credentials are still not valid, raise an error.
        # Also remove the token file, as it is not valid anymore.
        raise RuntimeError("Unauthorized: failed to refresh to the credentials")

    # Save the token in the token file, so that it can be reused next time
    token_file.write_text(creds.to_json())

    return creds


def load_credentials(
    credentials: pathlib.Path,
) -> google.oauth2.credentials.Credentials:
    """
    Load google credentials for the app.  This will require manual authorization from the
    user on the first attempt.

    :param credentials: The credentials file to load.
    """
    token_file = credentials.parent / "token.json"
    if token_file.exists():
        try:
            return load_token(token_file)
        except (RuntimeError, google.auth.exceptions.GoogleAuthError):
            token_file.unlink(missing_ok=True)

    # Token file doesn't exist, or isn't valid anymore.
    # This is the original authorization, we need to ask the user to authenticate to its account
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        str(credentials), SCOPES
    )
    creds = flow.run_local_server(port=0)
    token_file.write_text(creds.to_json())

    return load_token(token_file)


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


def get_tr_reports(service, folder: str) -> list[dict]:
    """
    Get the Trade republic reports that are in a specific folder

    The return type is a list of files metadata as dicts of the format {"id": <str>, "name": <str>}
    """

    folderId = (
        service.files()
        .list(
            q=f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder}'",
            fields="files(id, name)",
        )
        .execute()
    )
    folderIdResult = folderId.get("files", [])
    if len(folderIdResult) == 0:
        return []
    id = folderIdResult[0].get("id")

    results = (
        service.files().list(q=f"'{id}' in parents", fields="files(id, name)").execute()
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

        TR_PATH: Path to the Trade Republic report in google drive.

    """

    creds = load_credentials(pathlib.Path(app_credentials))

    # Call the Google Drive API
    service = googleapiclient.discovery.build("drive", "v3", credentials=creds)
    tr_reports = get_tr_reports(service, folder=tr_drive_folder)

    for report in tr_reports:
        download_file(
            service, file_metadata=report, output_folder=pathlib.Path(tr_output_path)
        )
        if tr_delete:
            # Caution, this will permanently delete the file without moving it to trash
            service.files().delete(fileId=report["id"]).execute()


if __name__ == "__main__":
    main()
