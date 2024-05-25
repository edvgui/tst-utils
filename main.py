import click
import pathlib
from art import tprint
from typing import Optional
from PIL import Image
from tst_filler import fill_tob
from tr_report_loader import load_report
from tr_report_parser import extract_report
from tst_qr import create_qrcode
from tst_sender import send_tst
from helpers.utils import TaxPerson


def process_tst(
    input_folder: str,
    output_folder: str = "output",
    tax_signature: str = "data/signature.jpg",
    tax_person: str = "data/citizen.json",
    app_credentials: str = "data/credentials.json",
    tr_drive_folder: Optional[str] = None,
    tr_delete: bool = False,
    qr_export: Optional[str] = None,
) -> None:
    tprint("tst-utils", font="rnd-medium")

    input_dir = pathlib.Path(input_folder)
    # Create input directory if it does not already exist
    output_dir = pathlib.Path(output_folder)
    output_dir.mkdir(exist_ok=True)

    person = TaxPerson.from_file(tax_person)

    if tr_delete and not qr_export:
        raise RuntimeError(
            "Please provide a way (with -q option) to export the QR "
            "when cleaning up input and output folders. Possible values are [mail, photo]."
        )

    if tr_drive_folder:
        load_report.load_report(
            app_credentials, tr_drive_folder, input_folder, tr_delete
        )

    for src_file in input_dir.glob("*.pdf"):
        dst_file = output_dir / src_file.name
        qr_code = output_dir / f"{src_file.name.removesuffix(".pdf")}.png"

        if dst_file.exists() and qr_code.exists():
            print(f"{str(dst_file)} and {str(qr_code)} already exist.")
            continue

        tax_data = extract_report.parse_doc(str(src_file))

        if not qr_code.exists():
            create_qrcode.create_qrcode(tax_data, person, qr_code)
            if not tr_delete:
                img = Image.open(qr_code)
                img.show()

        if not dst_file.exists():
            fill_tob.fill_tob(tax_data, dst_file, person, tax_signature)
            send_tst.send_tst(
                app_credentials, tax_data, person, dst_file, qr_code, qr_export
            )

    if tr_delete:
        for file in input_dir.iterdir():
            file.unlink()
        for file in output_dir.iterdir():
            file.unlink()


@click.command(
    name="tst-utils",
    help="Tool to fill in belgian TST file from trade republic monthly report. "
    "This tool also creates a draft mail with the generated document and a qr code to pay the tax.",
)
@click.argument(
    "input_folder",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=True,
)
@click.argument(
    "output_folder",
    default=pathlib.Path("output"),
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
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
    "--tax-person",
    help="Path to a file containing the data on the person filling in the form.",
    default=pathlib.Path("data/citizen.json"),
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--app-credentials",
    help="Path to the credentials file that can be used to interact with google drive api.",
    default=pathlib.Path("data/credentials.json"),
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True,
)
@click.option(
    "--tr-drive-folder",
    help="Folder containing trade republic report(s) in google drive.",
    type=click.STRING,
    required=False,
)
@click.option(
    "--tr-delete",
    help="Flag to indicate that the files in input and output folders should be cleaned." \
        " If loading pdf from drive, this will also cause the pdf to be cleaned there.",
    is_flag=True,
)
@click.option(
    "--qr-export",
    help="Way to export the QR code, either gmail or google photo.",
    type=click.Choice(["mail", "photo"]),
    required=False,
)
def main(
    input_folder: str,
    output_folder: str = "output",
    tax_signature: click.Path = "data/signature.jpg",
    tax_person: click.Path = "data/citizen.json",
    app_credentials: click.Path = "data/credentials.json",
    tr_drive_folder: Optional[str] = None,
    tr_delete: bool = False,
    qr_export: Optional[click.Choice] = None,
) -> None:
    process_tst(
        input_folder,
        output_folder,
        tax_signature,
        tax_person,
        app_credentials,
        tr_drive_folder,
        tr_delete,
        qr_export,
    )


if __name__ == "__main__":
    main()
