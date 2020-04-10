import os
from collections import OrderedDict
from decimal import Decimal
from typing import List, Tuple
import datetime

from xml.dom import minidom
import tweepy


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
        "GICs": [
            "shorttermgic90days",
            "shorttermgic180days",
            "shorttermgic270days",
            "gic1yr",
            "gic18month",
            "gic2yr",
            "gic3yr",
            "gic4yr",
            "gic5yr",
        ],
        "Savings": ["isacad", "isausd", "rspisacad", "tfsaisacad", "rifisacad",],
    }
    CODES = {
        "shorttermgic90days": {"key": ("3504", "90", "CAD"), "name": "90 Day GIC",},
        "shorttermgic180days": {"key": ("3504", "180", "CAD"), "name": "180 Day GIC",},
        "shorttermgic270days": {"key": ("3504", "270", "CAD"), "name": "270 Day GIC",},
        "gic1yr": {"key": ("3500", "1", "CAD"), "name": "1 Year GIC"},
        "gic18month": {"key": ("3500", "1.5", "CAD"), "name": "1.5 Year GIC",},
        "gic2yr": {"key": ("3500", "2", "CAD"), "name": "2 Year GIC"},
        "gic3yr": {"key": ("3500", "3", "CAD"), "name": "3 Year GIC"},
        "gic4yr": {"key": ("3500", "4", "CAD"), "name": "4 Year GIC"},
        "gic5yr": {"key": ("3500", "5", "CAD"), "name": "5 Year GIC"},
        "isacad": {"key": ("3000", "", "CAD"), "name": "Savings Account"},
        "isausd": {"key": ("3010", "", "USD"), "name": "Tax-Free Savings"},
        "rspisacad": {"key": ("3100", "", "CAD"), "name": "RSP Savings"},
        "tfsaisacad": {"key": ("3200", "", "CAD"), "name": "US$ Savings"},
        "rifisacad": {"key": ("3400", "", "CAD"), "name": "RIF Savings"},
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


class Twitter(object):
    def __init__(self):
        super(Twitter, self).__init__()
        auth = tweepy.OAuthHandler(
            os.environ["TWITTER_API_KEY"], os.environ["TWITTER_API_SECRET"]
        )
        auth.set_access_token(
            os.environ["TWITTER_ACCESS_TOKEN"],
            os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
        )

        self.api = tweepy.API(auth)
        self.api.verify_credentials()

    def tweet(self, text):
        self.api.update_status(text)


xml = minidom.parse("RatesHistory.xml")
products = Parser(xml).parse_products()

today = datetime.date.today()
for category in Products.CATEGORIES:
    if products.category_has_rate_change_on_day(category, today):
        rates = products.category_details_on_day(category, today)
        details = "\n".join([f"{name}: {rate}%" for name, rate in rates])
        message = f"New rates for {category}!\n\n{details}"

        print(message)
        Twitter().tweet(message)
