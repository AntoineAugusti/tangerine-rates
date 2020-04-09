from collections import OrderedDict
from decimal import Decimal
from typing import List, Tuple
import datetime

from xml.dom import minidom


class Parser(object):
    def __init__(self, xml):
        super(Parser, self).__init__()
        self.xml = xml

    def parse_rates(self, el):
        rates = OrderedDict()
        for rate in el.getElementsByTagName("rate"):
            raw_date = rate.getElementsByTagName("date")[0].firstChild.nodeValue
            date = datetime.datetime.strptime(raw_date, "%m/%d/%Y").date()
            raw_rate = rate.getElementsByTagName("value")[0].attributes["en"].value
            rate = Decimal(raw_rate.replace("%", ""))
            rates[date] = rate
        return rates

    def parse_product(self, el):
        return {
            "type": el.attributes["type"].value,
            "currency": el.attributes["currency"].value,
            "terms": el.attributes["terms"].value,
            "rates": self.parse_rates(el),
        }

    def parse_products(self):
        items = self.xml.getElementsByTagName("product")
        products = Products()
        for el in items:
            product = self.parse_product(el)
            products[(product["type"], product["terms"], product["currency"])] = product
        return products


class Products(dict):
    CATEGORIES = {
        "GIC": [
            "shorttermgic90days",
            "shorttermgic180days",
            "shorttermgic270days",
            "gic1yr",
            "gic18month",
            "gic2yr",
            "gic3yr",
            "gic4yr",
            "gic5yr",
        ]
    }
    CODES = {
        "shorttermgic90days": {
            "key": ("3504", "90", "CAD"),
            "name": "90 Day Guaranteed Investment",
        },
        "shorttermgic180days": {
            "key": ("3504", "180", "CAD"),
            "name": "180 Day Guaranteed Investment",
        },
        "shorttermgic270days": {
            "key": ("3504", "270", "CAD"),
            "name": "270 Day Guaranteed Investment",
        },
        "gic1yr": {"key": ("3500", "1", "CAD"), "name": "1 Year Guaranteed Investment"},
        "gic18month": {
            "key": ("3500", "1.5", "CAD"),
            "name": "1.5 Year Guaranteed Investment",
        },
        "gic2yr": {"key": ("3500", "2", "CAD"), "name": "2 Year Guaranteed Investment"},
        "gic3yr": {"key": ("3500", "3", "CAD"), "name": "3 Year Guaranteed Investment"},
        "gic4yr": {"key": ("3500", "4", "CAD"), "name": "4 Year Guaranteed Investment"},
        "gic5yr": {"key": ("3500", "5", "CAD"), "name": "5 Year Guaranteed Investment"},
    }

    def __init__(self, *args):
        dict.__init__(self, args)

    def for_code(self, code):
        return self[self.CODES[code]["key"]]

    def rate_on_day(self, code: str, day: datetime.date) -> Decimal:
        product = self.for_code(code)
        for rate_date, rate in product["rates"].items():
            if rate_date <= day:
                return rate
        raise NotImplementedError

    def has_rate_change_on_day(self, code: str, day: datetime.date) -> bool:
        return day in self.for_code(code)["rates"]

    def category_has_rate_change_on_day(
        self, category: str, day: datetime.date
    ) -> bool:
        res = []
        for code in self.CATEGORIES[category]:
            res.append(self.has_rate_change_on_day(code, day))
        return any(res)

    def category_details_on_day(self, category: str, day: datetime.date) -> List[Tuple]:
        res = []
        for code in self.CATEGORIES[category]:
            res.append((self.CODES[code]["name"], self.rate_on_day(code, day)))
        return res


xml = minidom.parse("RatesHistory.xml")
products = Parser(xml).parse_products()

print(products.for_code("gic1yr"))
print(products.rate_on_day("gic1yr", datetime.date(2020, 4, 9)))
print(products.rate_on_day("gic1yr", datetime.date(2020, 4, 2)))
print(products.has_rate_change_on_day("gic1yr", datetime.date(2020, 4, 2)))
print(products.has_rate_change_on_day("gic1yr", datetime.date(2020, 4, 1)))
print(products.has_rate_change_on_day("gic1yr", datetime.date(2020, 4, 1)))
print("Product change")
print(products.category_has_rate_change_on_day("GIC", datetime.date(2020, 4, 3)))
print(products.category_has_rate_change_on_day("GIC", datetime.date(2020, 4, 2)))
print(products.category_has_rate_change_on_day("GIC", datetime.date(2020, 4, 1)))

print(products.category_details_on_day("GIC", datetime.date(2020, 4, 1)))
print(products.category_details_on_day("GIC", datetime.date(2020, 4, 2)))
