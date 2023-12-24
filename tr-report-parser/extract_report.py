import pypdf
import re
import json
import click


MONTHS = {
    "JANUARY": 1,
    "FEBRUARY": 2,
    "MARCH": 3,
    "APRIL": 4,
    "MAY": 5,
    "JUNE": 6,
    "JULY": 7,
    "AUGUST": 8,
    "SEPTEMBER": 9,
    "OCTOBER": 10,
    "NOVEMBER": 11,
    "DECEMBER": 12,
}

time = re.compile(f"(?P<month>{'|'.join(MONTHS)}) " + r"(?P<year>20[\d]{2})")
transaction_type = re.compile(r"TAX ON STOCK-EXCHANGE TRANSACTIONS FOR (?P<type>[A-Z]+) \((?P<tax>[\d\.]+)\%\)")
total_tax_basis = re.compile(r"TOTAL TAX BASIS IN EUR: (?P<amount>[\d\.]+)")
total_tax_amount = re.compile(r"TOTAL TAX AMOUNT IN EUR: (?P<amount>[\d\.]+)")
total_transactions = re.compile(r"TOTAL TRANSACTIONS: (?P<amount>[\d\.]+)")


def parse_doc(file: str) -> list[dict]:
    """
    Parse a trade republic tax report for belgian citizen and extract a report
    of the fiven form:

    .. code-block:: json

        {
            "month": 11,
            "year": 2023,
            "products": [
                {
                    "stockType": "ETFS",
                    "stockTax": 0.12,
                    "taxBasis": 80.0,
                    "taxAmount": 0.08,
                    "transactionCount": 8
                },
                {
                    "stockType": "STOCKS",
                    "stockTax": 0.35,
                    "taxBasis": 80.0,
                    "taxAmount": 0.32,
                    "transactionCount": 16
                }
            ]
        }

    """
    reader = pypdf.PdfReader(file)
    content = "\n".join(page.extract_text() for page in reader.pages)

    time_match = time.search(content)
    month = time_match.group("month")
    year = int(time_match.group("year"))

    parsed = {
        "month": MONTHS[month],
        "year": year,
        "products": [],
    }

    for section_match, tax_basis_match, tax_amount_match, transactions_match in zip(
        transaction_type.finditer(content),
        total_tax_basis.finditer(content),
        total_tax_amount.finditer(content),
        total_transactions.finditer(content),
        strict=True,
    ):
        parsed["products"].append({
            "stockType": section_match.group("type"),
            "stockTax": float(section_match.group("tax")),
            "taxBasis": float(tax_basis_match.group("amount")),
            "taxAmount": float(tax_amount_match.group("amount")),
            "transactionCount": int(transactions_match.group("amount")),
        })

    return parsed


@click.command()
@click.argument(
    "tst_report",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
)
def main(tst_report: click.Path) -> None:
    """Extract relevant information from a trade republic tst report document
    
    Arguments:

        TST_REPORT: Path to a tax report document that should be parsed.
    """
    print(json.dumps(parse_doc(str(tst_report)), indent=2))


if __name__ == "__main__":
    main()
