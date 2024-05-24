from dataclasses import dataclass
import click
import json


@dataclass
class TaxProduct:
    stockType: str
    stockTax: float
    taxBasis: float
    taxAmount: float
    transactionCount: int


@dataclass
class TaxData:
    month: int
    year: int
    products: list[TaxProduct]


@dataclass
class TaxPerson:
    nationalRegisterNumber: str
    fullName: str
    address: str

    def from_file(tax_person: str) -> "TaxPerson":
        with click.open_file(tax_person) as fd:
            return TaxPerson(**json.load(fd))
