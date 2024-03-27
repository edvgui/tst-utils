import base64
import json
import pathlib
import click
import typing

import email.message
import googleapiclient.discovery
from requests import HTTPError
from email.message import EmailMessage
import google.oauth2.credentials
from helpers.google_api import load_credentials
from google.auth.transport.requests import AuthorizedSession

MONTHS = {
    1: "JANUARY",
    2: "FEBRUARY",
    3: "MARCH",
    4: "APRIL",
    5: "MAY",
    6: "JUNE",
    7: "JULY",
    8: "AUGUST",
    9: "SEPTEMBER",
    10: "OCTOBER",
    11: "NOVEMBER",
    12: "DECEMBER",
}

# Mail recipient (tax administration)
RECIPIENT = "CPIC.TAXDIV@minfin.fed.be"

# Mail content
CONTENT = """Hi,

Please find here attached my stock-exchange transactions form for the month of %(month)s %(year)s.

Regards,

%(full_name)s
%(national_register_number)s
"""


def prepare_mail(
    sender: str,
    month: int,
    year: int,
    full_name: str,
    national_register_number: str,
    tst_form: pathlib.Path,
) -> str:
    """
    Prepare an email for the belgian administration, containing as attachment, the filled in form.

    https://finance.belgium.be/en/faq/taks-op-de-beursverrichtingen-en

    :param sender: The email address used to send to form
    :param month: The month this form as been filled for
    :param year: The year this form as been filled for
    :param full_name: The full name of the citizen sending this form
    :param national_register_number: The number of the citizen, in the national registry
    :param tst_form: The path the form to send to the administration
    """
    message = email.message.EmailMessage()

    # Create a short version of the nrn, removing anything that is not a number
    nrn = "".join(c for c in national_register_number if c in "0123456789")
    message.set_content(
        CONTENT
        % dict(
            month=MONTHS[month].capitalize(),
            year=year,
            full_name=full_name,
            national_register_number=national_register_number,
        )
    )

    message["To"] = RECIPIENT
    message["From"] = sender
    message["Subject"] = f"TST {full_name} ({nrn}): {month}/{year}"

    message.add_attachment(
        tst_form.read_bytes(),
        maintype="application",
        subtype="pdf",
        filename=f"tst-{nrn}-{year}-{month}.pdf",
    )

    return base64.urlsafe_b64encode(message.as_bytes()).decode()


def send_qr_by_mail(service, tst_qr: pathlib.Path, mail: str) -> None:
    message = EmailMessage()
    message["to"] = mail
    message["subject"] = "TST tax payment qr code"

    with open(tst_qr, "rb") as content_file:
        content = content_file.read()
        message.add_attachment(
            content, maintype="application", subtype="png", filename=str(tst_qr)
        )

    create_message = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
        print(f'sent message to {message} Message Id: {message["id"]}')
    except HTTPError as error:
        print(f"An error occurred: {error}")
        message = None


def upload_qr_to_google_photo(
    tst_qr: pathlib.Path, credentials: google.oauth2.credentials.Credentials
) -> None:
    authed_session = AuthorizedSession(credentials)

    with open(tst_qr, "rb") as f:
        image_contents = f.read()

    # upload photo and get upload token
    response = authed_session.post(
        "https://photoslibrary.googleapis.com/v1/uploads",
        headers={},
        data=image_contents,
    )
    upload_token = response.text

    service = googleapiclient.discovery.build(
        "photoslibrary", "v1", credentials=credentials, static_discovery=False
    )
    service.mediaItems().batchCreate(
        body={
            "newMediaItems": [
                {
                    "description": "QR code to pay TOB",
                    "simpleMediaItem": {
                        "fileName": "tst_qr.png",
                        "uploadToken": upload_token,
                    },
                }
            ]
        }
    ).execute()


@click.command()
@click.option(
    "--app-credentials",
    help="Path to the credentials file that can be used to interact with gmail api.",
    default=pathlib.Path("credentials.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    "--tax-data",
    help="Path to a file containing the data on the actual tax to pay to the state.",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--tax-person",
    help="Path to a file containing the data on the person filling in the form.",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--tst-qr",
    help="Path to a file containing the QR code to pay the tax.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=False,
)
@click.option(
    "--qr-export",
    help="Way to export the QR code, either by mail or google photo. Default value is mail.",
    default="mail",
    type=click.Choice(["mail", "photo"]),
    required=False,
)
@click.argument(
    "tst_form",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
def main(
    app_credentials: click.Path,
    tax_data: click.Path,
    tax_person: click.Path,
    tst_form: click.Path,
    tst_qr: typing.Optional[click.Path] = None,
    qr_export: typing.Optional[click.Choice] = "mail",
) -> None:
    """Prepare a draft email with the given tst file for the belgian finance administration.

    Arguments:

        TST_FORM: Path to the filled in tax report to send to the administration.

        TAX_DATA: Path to a file containing the data on the actual tax to pay to the state.

        TAX_PERSON: Path to a file containing the data on the person filling in the form.

        TST_QR: Path to a file containing the QR code to pay the tax.

        QR_EXPORT: Way to export the QR code, either gmail or google photo.
    """
    creds = load_credentials(pathlib.Path(app_credentials))

    # Call the Gmail API
    service = googleapiclient.discovery.build("gmail", "v1", credentials=creds)

    # Discover the email address of the authenticated user
    sender = service.users().getProfile(userId="me").execute()["emailAddress"]

    # Load the tax data and tax person
    with click.open_file(tax_data) as fd:
        data = json.load(fd)

    with click.open_file(tax_person) as fd:
        person = json.load(fd)

    encoded_message = prepare_mail(
        sender=sender,
        month=data["month"],
        year=data["year"],
        full_name=person["fullName"],
        national_register_number=person["nationalRegisterNumber"],
        tst_form=pathlib.Path(tst_form),
    )

    create_message = {"message": {"raw": encoded_message}}
    service.users().drafts().create(userId="me", body=create_message).execute()

    if not tst_qr:
        return

    match qr_export:
        case "mail":
            send_qr_by_mail(service, tst_qr=tst_qr, mail=sender)
        case "photo":
            upload_qr_to_google_photo(tst_qr, creds)


if __name__ == "__main__":
    main()
