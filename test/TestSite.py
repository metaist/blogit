#!/usr/bin/python
# coding: utf-8

import os
import unittest

from blogit import Site, metaformat

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = metaformat({
    'url': '//localhost',
    'blog_dir': TEST_DIR + '/blog',
    'blog_url': '{url}/blog',
    'img_dir': TEST_DIR + '/static/img',
    'img_url': '{url}/static/img'
})


class TestSite(unittest.TestCase):
    def test_init(self):
        """Expected to construct site."""
        test = Site(**CONFIG)

        for attr in CONFIG.keys():
            self.assertEqual(getattr(test, attr), CONFIG[attr])
