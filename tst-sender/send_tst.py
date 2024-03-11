import base64
import json
import pathlib
import click

import email.message
import googleapiclient.discovery
from helpers.google_api import load_credentials

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
        CONTENT % dict(
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
    help="Path to a file containing the data on the actual tax to pay to the state",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True),
    required=True,
)
@click.option(
    "--tax-person",
    help="Path to a file containing the data on the person filling in the form",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True),
    required=True,
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
) -> None:
    """Prepare a draft email with the given tst file for the belgian finance administration.

    Arguments:

        TST_FORM: Path to the filled in tax report to send to the administration.

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


if __name__ == "__main__":
    main()
