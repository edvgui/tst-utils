import json
import click
import qrcode
import qrcode.image.pil


GIRO_TEMPLATE = """BCD
001
1
SCT
%(bic)s
%(name)s
%(iban)s
%(amount)s
CHAR

%(communication)s
Giro QR Code
"""


def prepare_qr_code(
    amount: float,
    national_register_number: str,
) -> qrcode.image.pil.PilImage:
    """
    Prepare a qr code to send the payment to the state.  The national register number of the user will
    be included in the communication.

    :param amount: The amount of money, in euro, to send.
    :param national_register_number: The national register number of the citizen doing the payment.
    """
    nrn = "".join(c for c in national_register_number if c in "0123456789")
    return qrcode.make(
        GIRO_TEMPLATE % dict(
            bic="PCHQBEBB",
            name="Centre de perception - section taxes diverses",
            iban="BE39679200229319",
            amount=f"EUR{amount}",
            communication=f"TOB/{nrn}",
        )
    )


@click.command()
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
    "output_file",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
def main(
    tax_data: click.Path,
    tax_person: click.Path,
    output_file: click.Path,
) -> None:
    """Create a QR Code containing all payment info for the tst.

    Arguments:

        OUTPUT_FILE: Path to the generated qr code image.

    """
    # Load the tax data and tax person
    with click.open_file(tax_data) as fd:
        data = json.load(fd)
    
    with click.open_file(tax_person) as fd:
        person = json.load(fd)

    total: float = sum(p["taxAmount"] for p in data["products"])
    encoded_message = prepare_qr_code(total, person["nationalRegisterNumber"])
    encoded_message.save(str(output_file))


if __name__ == "__main__":
    main()
