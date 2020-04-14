import os
from collections import OrderedDict
from decimal import Decimal
from typing import List, Tuple
import datetime
import json

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
    def __init__(self, *args):
        dict.__init__(self, args)
        with open("data/codes.json") as f:
            self.codes = json.load(f)
        with open("data/categories.json") as f:
            self.categories = json.load(f)

    def for_code(self, code):
        return self[tuple(self.codes[code]["key"])]

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
        return any(
            [
                self.has_rate_change_on_day(code, day)
                for code in self.categories[category]
            ]
        )

    def category_details_on_day(self, category: str, day: datetime.date) -> List[Tuple]:
        return [
            (self.codes[code]["name"], self.rate_on_day(code, day))
            for code in self.categories[category]
        ]


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

    def tweet(self, text, in_reply_to_status_id=None):
        return self.api.update_status(text, in_reply_to_status_id=in_reply_to_status_id)


if __name__ == "__main__":
    xml = minidom.parse("RatesHistory.xml")
    products = Parser(xml).parse_products()

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    for category in [
        category
        for category in products.categories
        if products.category_has_rate_change_on_day(category, today)
    ]:
        rates = products.category_details_on_day(category, today)
        details = "\n".join([f"{name}: {rate}%" for name, rate in rates])
        message = f"New rates for {category}!\n\n{details}"
        status = Twitter().tweet(message)

        rates = products.category_details_on_day(category, yesterday)
        details = "\n".join([f"{name}: {rate}%" for name, rate in rates])
        message = f"Previous rates:\n\n{details}"
        Twitter().tweet(message, in_reply_to_status_id=status.id)
