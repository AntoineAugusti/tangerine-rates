from xml.dom import minidom
import datetime
from decimal import Decimal

from main import Parser

import pytest


class TestProducts(object):
    @pytest.fixture(scope="module")
    def products(self):
        xml = minidom.parse("RatesHistory.xml")
        return Parser(xml).parse_products()

    @pytest.mark.parametrize(
        "date,expected",
        [
            (datetime.date(2020, 4, 3), Decimal("2.3")),
            (datetime.date(2020, 4, 2), Decimal("2.3")),
            (datetime.date(2020, 4, 1), Decimal("2.8")),
            (datetime.date(2020, 3, 28), Decimal("2.8")),
            (datetime.date(2020, 3, 27), Decimal("2.8")),
        ],
    )
    def test_rate_on_day(self, products, date, expected):
        assert expected == products.rate_on_day("gic1yr", date)

    @pytest.mark.parametrize(
        "date,expected",
        [
            (datetime.date(2020, 4, 3), False),
            (datetime.date(2020, 4, 2), True),
            (datetime.date(2020, 4, 1), False),
            (datetime.date(2020, 3, 28), False),
            (datetime.date(2020, 3, 27), True),
        ],
    )
    def test_has_change_on_day(self, products, date, expected):
        assert expected == products.has_rate_change_on_day("gic1yr", date)
        assert expected == products.category_has_rate_change_on_day("GICs", date)

    def test_invalid_date_rate_on_day(
        self, products,
    ):
        assert Decimal("4.20") == products.rate_on_day(
            "gic1yr", datetime.date(2007, 5, 25)
        )
        with pytest.raises(NotImplementedError):
            products.rate_on_day("gic1yr", datetime.date(2007, 5, 24))

    def test_details(
        self, products,
    ):
        assert [
            ("90 Day GIC", Decimal("0.50")),
            ("180 Day GIC", Decimal("2.20")),
            ("270 Day GIC", Decimal("2.10")),
            ("1 Year GIC", Decimal("2.30")),
            ("1.5 Year GIC", Decimal("2.15")),
            ("2 Year GIC", Decimal("2.00")),
            ("3 Year GIC", Decimal("2.10")),
            ("4 Year GIC", Decimal("2.20")),
            ("5 Year GIC", Decimal("2.25")),
        ] == products.category_details_on_day("GICs", datetime.date(2020, 4, 9))

        assert [
            ("90 Day GIC", Decimal("0.50")),
            ("180 Day GIC", Decimal("2.80")),
            ("270 Day GIC", Decimal("2.60")),
            ("1 Year GIC", Decimal("2.80")),
            ("1.5 Year GIC", Decimal("2.85")),
            ("2 Year GIC", Decimal("2.90")),
            ("3 Year GIC", Decimal("3.00")),
            ("4 Year GIC", Decimal("3.10")),
            ("5 Year GIC", Decimal("3.20")),
        ] == products.category_details_on_day("GICs", datetime.date(2020, 4, 1))
