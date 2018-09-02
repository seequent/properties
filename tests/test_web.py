from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

import properties
from properties.extras import URL

BASE = 'https://someurl.com'
PATH = '/my/path'
QUERY = '?one=1&two=2'
PARAM = ';/three;four=4'
FRAGMENT = '#fragment'

class TestURL(unittest.TestCase):

    def test_anyurl(self):

        class HasURL(properties.HasProperties):
            url = URL('any url')

        hurl = HasURL()
        hurl.url = BASE
        assert hurl.url == BASE

        full_url = BASE + PATH + QUERY + PARAM + FRAGMENT
        hurl = HasURL()
        hurl.url = full_url
        assert hurl.url == full_url

    def test_no_params(self):

        class HasURL(properties.HasProperties):
            url = URL('any url', remove_parameters=True)

        full_url = BASE + PATH + QUERY + PARAM + FRAGMENT
        expected_url = BASE + PATH + FRAGMENT
        hurl = HasURL()
        hurl.url = full_url
        assert hurl.url == expected_url

    def test_no_fragment(self):

        class HasURL(properties.HasProperties):
            url = URL('any url', remove_fragment=True)

        full_url = BASE + PATH + QUERY + PARAM + FRAGMENT
        expected_url = BASE + PATH + QUERY + PARAM
        hurl = HasURL()
        hurl.url = full_url
        assert hurl.url == expected_url

    def test_bad_urls(self):

        class HasURL(properties.HasProperties):
            url = URL('any url')

        hurl = HasURL()
        for item in (PATH, QUERY, PARAM, FRAGMENT, 'someurl.com', 'https://'):
            with self.assertRaises(properties.ValidationError):
                hurl.url = item


if __name__ == '__main__':
    unittest.main()
