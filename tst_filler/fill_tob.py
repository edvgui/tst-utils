import click
import pathlib
import pymupdf
import datetime
import geocoder
from helpers.utils import TaxData, TaxPerson
from typing import Optional
from geopy.geocoders import Nominatim
from tr_report_parser import extract_report


def get_current_city() -> str:
    myloc = geocoder.ip("me")
    geolocator = Nominatim(user_agent="tst_utils")
    location = geolocator.reverse(str(myloc.lat) + "," + str(myloc.lng))
    return location.raw["address"]["town"].split(" - ")[0]


def draw_tax_square_numbers(page, height: int, x: list[int], value: float) -> None:
    # digits from billion to million
    million_value = int(value / 1000000) % 1000
    if million_value > 0:
        page.insert_text(
            point=pymupdf.Point(x[0], height), text=f"{million_value}", fontsize=15
        )

    # digits from million to thousands
    thousand_value = int(value / 1000) % 1000
    if thousand_value > 0 or million_value > 0:
        if million_value > 0:
            thousand_value = f"{thousand_value:03d}"
        page.insert_text(
            point=pymupdf.Point(x[1], height), text=str(thousand_value), fontsize=15
        )

    # last 3 digit before cents
    unit_value = int(value) % 1000
    if thousand_value > 0 or million_value > 0:
        unit_value = f"{unit_value:03d}"
    page.insert_text(point=pymupdf.Point(x[2], height), text=str(unit_value), fontsize=15)

    # cents
    page.insert_text(
        point=pymupdf.Point(x[3], height), text=f"{round((value%1)*100):02d}", fontsize=15
    )


def draw_tax_basis(page, height: int, value: float) -> None:
    draw_tax_square_numbers(page, height, [277, 313, 345, 378], value)


def draw_tax_amount(page, height: int, value: float) -> None:
    draw_tax_square_numbers(page, height, [408, 443, 478, 510], value)


def draw_total_tax_amount(page, height: int, value: float) -> None:
    draw_tax_square_numbers(page, height, [335, 367, 399, 431], value)


def fill_tob(
    tax_data: TaxData,
    output_file: str,
    tax_person: TaxPerson,
    tax_signature: Optional[str] = "data/signature.jpg",
    form_file: Optional[str] = "data/form-original.pdf",
) -> None:
    # retrieve the first page of the PDF
    file_handle = pymupdf.open(form_file)
    first_page = file_handle[0]

    # Fill the date
    first_page.insert_text(
        point=pymupdf.Point(275, 118),
        text=str(tax_data.month),
        fontname="helvetica-bold",
        fontsize=10,
    )
    first_page.insert_text(
        point=pymupdf.Point(288, 118),
        text=str(tax_data.year % 100),
        fontname="helvetica-bold",
        fontsize=10,
    )

    # Fill user personal data
    first_page.insert_text(
        point=pymupdf.Point(305, 187), text=tax_person.nationalRegisterNumber, fontsize=10
    )
    first_page.insert_text(
        point=pymupdf.Point(305, 199), text=tax_person.fullName, fontsize=10
    )
    first_page.insert_text(
        point=pymupdf.Point(305, 222), text=tax_person.address, fontsize=10
    )

    tax_products_height = {0.12: 304, 0.35: 385, 1.32: 408}

    total_tax_amount = 0

    # Fill tax data
    for product_data in tax_data.products:
        height = tax_products_height[product_data.stockTax]
        tax_basis = product_data.taxBasis
        tax_amount = product_data.taxAmount

        # Number
        first_page.insert_text(
            point=pymupdf.Point(227, height),
            text=str(product_data.transactionCount),
            fontsize=15,
        )

        # Tax basis
        draw_tax_basis(first_page, height, tax_basis)

        # Tax amount
        draw_tax_amount(first_page, height, tax_amount)

        total_tax_amount += tax_amount

    draw_tax_amount(first_page, 513, total_tax_amount)

    second_page = file_handle[1]

    draw_total_tax_amount(second_page, 471, total_tax_amount)

    # location and date of signature
    second_page.insert_text(
        point=pymupdf.Point(81, 588), text=get_current_city(), fontsize=12
    )
    second_page.insert_text(
        point=pymupdf.Point(181, 588),
        text=datetime.datetime.now().strftime("%d/%m/%Y"),
        fontsize=12,
    )

    # add the signature
    second_page.insert_image(rect=pymupdf.Rect(300, 500, 450, 650), filename=tax_signature)

    file_handle.save(output_file)


@click.command()
@click.option(
    "--tax-data",
    help="Path to a file containing the data on the actual tax to pay to the state",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--output-file",
    help="Folder containing trade republic report(s) in google drive.",
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
    "--tax-signature",
    help="Path to a file image containing the signature.",
    default=pathlib.Path("data/signature.jpg"),
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
@click.option(
    "--form-file",
    help="Belgian tst  pdf template file to fill.",
    default=pathlib.Path("data/form-original.pdf"),
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, allow_dash=True
    ),
    required=True,
)
def main(
    tst_report: click.Path,
    output_file: click.Path,
    tax_person: Optional[click.Path] = "data/citizen.json",
    tax_signature: Optional[click.Path] = "data/signature.jpg",
    form_file: Optional[click.Path] = "data/form-original.pdf",
) -> None:
    """Fill in the TST form for a given citizen and tax data.

    Arguments:
        TAX_DATA : Data containing all the tax information required to fill the belgian tst pdf.

        TST_REPORT: Path to trade republic report.

        OUTPUT_FILE : File path where to save the resulting pdf.

        TAX_PERSON : Path to a file containing the data on the person filling in the form.

        TAX_SIGNATURE : Path to a file image containing the signature.

        SIGNATURE_LOCATION : Location (city) where the document has been signed.

        FORM_FILE : Belgian tst pdf template file to fill.
    """
    data = extract_report.parse_doc(tst_report)
    person = TaxPerson.from_file(tax_person)

    fill_tob(data, output_file, person, tax_signature, form_file)


if __name__ == "__main__":
    main()
