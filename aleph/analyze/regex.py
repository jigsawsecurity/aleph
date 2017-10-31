import re
import logging
from dalet import parse_phone

from aleph.analyze.analyzer import Analyzer
from aleph.model import DocumentTag, DocumentTagCollector

log = logging.getLogger(__name__)

# URLs:
# https://gist.github.com/uogbuji/705383
# REGEX = ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))'  # noqa


class RegexAnalyzer(Analyzer):

    def extract_match(self, document, match):
        return match.group(0)

    def analyze(self, document):
        collector = DocumentTagCollector(document, self.ORIGIN)
        for match in self.RE.finditer(document.text):
            text = self.extract_match(document, match)
            if text is not None:
                collector.emit(text, self.TYPE)
        collector.save()


class EMailAnalyzer(RegexAnalyzer):
    REGEX = '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}'
    RE = re.compile(REGEX, re.IGNORECASE)
    ORIGIN = 'regex:email'
    TYPE = DocumentTag.TYPE_EMAIL


class PhoneNumberAnalyzer(RegexAnalyzer):
    REGEX = r'(\+?[\d\-\(\)\/\s]{5,})'
    RE = re.compile(REGEX, re.IGNORECASE)
    CHARS = '+0123456789'
    ORIGIN = 'regex:phones'
    TYPE = DocumentTag.TYPE_PHONE

    def extract_match(self, document, match):
        text = match.group(0)
        text = ''.join([m for m in text if m in self.CHARS])
        if len(text) < 5:
            return
        for country in [None] + document.countries:
            num = parse_phone(text, country=country)
            if num is None:
                continue
            return num
