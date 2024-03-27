import pathlib
import re

import google.auth.transport.requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import google.auth.exceptions

# If modifying these scopes, delete the file token.json.
SCOPES = [
    # used by tr-report-loader and tr-report-watch
    "https://www.googleapis.com/auth/drive",
    # used by tst-sender
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
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
        service.files()
        .list(q=f"'{folder_id}' in parents", fields="files(id, name)")
        .execute()
    )
    files = results.get("files", [])

    pattern = re.compile(r"pb[0-9]+[.]pdf$")
    return [file for file in files if pattern.match(file["name"])]
