from urlparse import urljoin
from pprint import pprint  # noqa
import requests
import logging

from aleph.core import app, db
from aleph.model import Watchlist, Entity
from aleph.analyze import analyze_terms
from aleph.model.forms import PERSON, ORGANIZATION, COMPANY, OTHER
from aleph.crawlers.crawler import Crawler

log = logging.getLogger(__name__)

SCHEMATA = {
    'https://schema.occrp.org/generic/person.json#': PERSON,
    'https://schema.occrp.org/generic/company.json#': COMPANY,
    'https://schema.occrp.org/generic/organization.json#': ORGANIZATION
}


class SpindleCrawler(Crawler):

    URL = app.config.get('SPINDLE_URL')
    API_KEY = app.config.get('SPINDLE_API_KEY')
    HEADERS = {'Authorization': 'ApiKey %s' % API_KEY}

    def crawl_collection(self, collection):
        if not len(collection.get('subjects', [])):
            return
        url = urljoin(self.URL, '/api/collections/%s' % collection.get('id'))
        watchlist = Watchlist.by_foreign_id(url, {
            'label': collection.get('title'),
            'public': False,
            'users': []
        })
        log.info(" > Spindle collection: %s", watchlist.label)
        db.session.flush()
        res = requests.get('%s/entities' % url, headers=self.HEADERS)
        terms = watchlist.terms
        watchlist.delete_entities()
        for entity in res.json().get('results', []):
            if entity.get('name') is None:
                continue
            aliases = [on.get('alias') for on in entity.get('other_names', [])]
            ent = Entity.create({
                'name': entity.get('name'),
                'watchlist': watchlist,
                'category': SCHEMATA.get(entity.get('$schema'), OTHER),
                'data': entity,
                'selectors': aliases
            })
            log.info("  # %s (%s)", ent.name, ent.category)
        terms.update(watchlist.terms)
        db.session.commit()
        analyze_terms.delay(list(terms))

    def crawl(self):
        url = urljoin(self.URL, '/api/collections')
        while True:
            res = requests.get(url, headers=self.HEADERS)
            data = res.json()
            for coll in data.get('results', []):
                self.crawl_collection(coll)
            url = data.get('next_url')
            if url is None:
                break
            url = urljoin(self.URL, url)