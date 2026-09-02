"""This module handles interactions with databases."""

from dataclasses import dataclass

import pyodbc


@dataclass
class Citizen:
    """A dataclass representing citizen data from the database."""
    cpr: str
    first_name: str


def get_citizens_from_sql() -> list[Citizen]:
    """Get citizens with unknown address from SQL database.

    Returns:
        List of citizen objects.
    """
    with pyodbc.connect("Driver={ODBC Driver 17 for SQL Server};Server=FaellesSQL;Trusted_Connection=yes;") as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT CPR, Fornavn FROM [DWH].[Mart].[AdresseAktuel] WHERE Vejkode = 9901 AND Myndighed = 751 AND Alder > 17")
            return [Citizen(row.CPR, row.Fornavn) for row in cursor]
