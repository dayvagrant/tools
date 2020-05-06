import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from retrying import retry
from textacy import preprocessing
from torrequest import TorRequest


class SimpleWebpageParser:
    """Merge two library."""

    def __init__(self, url):
        self.url = url
        ua = UserAgent()
        self.headers = {"User-Agent": str(ua.random)}
        self.proxies = {
            "http": "socks5://127.0.0.1:9050",
            "https": "socks5://127.0.0.1:9050",
        }

    def getHTML(self):
        r = requests.get(self.url, headers=self.headers, proxies=self.proxies,)
        data = r.text
        soup = BeautifulSoup(data, "lxml")
        return soup


def tor_ip_change():
    """change tor node"""
    with TorRequest(proxy_port=9050, ctrl_port=9051, password=None) as tr:
        logger.info("renew ip")
        tr.reset_identity()


class Visitors:
    """Load info abaout domain from be1.ru"""

    @retry(stop_max_attempt_number=5)
    def __init__(self, target):
        """Init params."""
        self.target = self.return_valid_netloc(target)
        swp = SimpleWebpageParser("https://be1.ru/stat/{}".format(self.target))
        self.html = swp.getHTML()
        if self.html.find_all(id="recaptcha"):
            logger.info("Captcha_error")
            tor_ip_change()
            raise Exception("Captcha_error")
        if not self.html.find_all(id="recaptcha"):
            self.data = self.load_similarweb(self.html)

    def return_valid_netloc(self, target):
        """Return valid domain name."""
        data = urlparse(target)
        if not data.netloc:
            return data.path
        else:
            return data.netloc

    def load_similarweb(self, html):
        """Filter elements by div id."""
        return html.find(id="set_similarweb").find_all(type="text/javascript")

    def prepeare_to_text(self, text):
        """Clean teatx."""
        clean_punctuation = (
            text.get_text()
            .replace("\n", "")
            .replace("\r", "")
            .replace("\t", "")
            .replace("'", "")
        )
        return preprocessing.normalize.normalize_whitespace(clean_punctuation)

    def return_visitors_count(self):
        """Extract visitors count info."""
        item_data = self.data[0]
        item_data = self.prepeare_to_text(item_data)
        return re.findall(r"\,\[(.+?)\]", item_data)

    def return_visitors_country(self):
        """Extract visitors country info."""
        item_data = self.data[2]
        item_data = self.prepeare_to_text(item_data)
        list_of_country = re.findall(
            r"(?:[A-Za-z]+|[A-Za-z]+(?:\s[A-Za-z]+){,3}),\s\d{1,3}\.\d{0,2}",
            item_data,
        )
        return [[i[0], float(i[1])] for i in [i.split(",")
                                              for i in list_of_country]]

    def return_visitors_source(self):
        """Extract visitors source channels info."""
        item_data = self.data[1]
        item_data = self.prepeare_to_text(item_data)
        list_of_sources = re.findall(r"\,\[(.+?)\]", item_data)
        return [[i[0], float(i[1])] for i in [i.split(",")
                                              for i in list_of_sources]]
