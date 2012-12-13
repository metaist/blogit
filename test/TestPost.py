#!/usr/bin/python
# coding: utf-8

import os
import logging
import unittest

from blogit import Site, Post, metaformat

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = metaformat({
    'url': '//localhost',
    'blog_dir': TEST_DIR + '/blog',
    'blog_url': '{url}/blog',
    'img_dir': TEST_DIR + '/static/img',
    'img_url': '{url}/static/img'
})


class TestPost(unittest.TestCase):
    def setUp(self):
        """Define the global site."""
        self.site = Site(**CONFIG)

    def test_init(self):
        """Expected to create post."""
        test = Post(self.site)
        self.assertTrue(test is not None)

    def test_content(self):
        """Expected to parse markdown."""
        markd = '{post.url}'
        metadata = {'year': '2012', 'month': '01', 'day': '01', 'stub': 'test'}
        test = Post(self.site, defaults=metadata)
        test.render(markd)

        expected = '<p>//localhost/blog/2012/01/test.html</p>'
        self.assertEqual(test.html, expected)

    def test_bad_content(self):
        """Expected to fail to parse markdown."""
        markd = '{post.xurl}'
        metadata = {'year': '2012', 'month': '01', 'day': '01', 'stub': 'test'}
        test = Post(self.site, defaults=metadata)

        logging.disable(logging.CRITICAL)
        test.render(markd)
        logging.disable(logging.NOTSET)

        expected = ''
        self.assertEqual(test.html, expected)

    def test_path(self):
        """Expected to parse basic post."""
        path = os.path.join(TEST_DIR, '_posts', '2012-01-01.01-test.markdown')
        test = Post(self.site, path=path)
        self.assertFalse(test.is_future())
        self.assertTrue(test.is_updated())

        expected = 'Sunday, January 01, 2012'
        self.assertEqual(test.get_published(), expected)
        self.assertNotEqual(test.get_updated(), expected)

    def test_invalid_path(self):
        """Expected to return empty post."""
        path = os.path.join(TEST_DIR, '_posts', 'badregex')
        test = Post(self.site, path=path)
        self.assertEqual(test.html, '')
        self.assertIsNone(test.get_published())
        self.assertIsNone(test.get_updated())

        path = os.path.join(TEST_DIR, '_posts', '2012-01-01.01-nop.markdown')
        test = Post(self.site, path=path)
        self.assertEqual(test.html, '')
