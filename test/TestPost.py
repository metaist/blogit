#!/usr/bin/python
# coding: utf-8

from datetime import datetime
import os
import unittest

from metautils import Namespace, interpolate
import blogit

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class TestPost(unittest.TestCase):
    def setUp(self):
        """Setup configuration."""
        self.config = Namespace(interpolate({
            'url': '//localhost',
            'blog_url': '{url}/blog',
            'img_url': '{url}/static/img',
            'img_dir': os.path.join(TEST_DIR, 'static', 'img')
        }))

    def test_init(self):
        """Expected to create post."""
        test = blogit.Post('')
        self.assertTrue(test is not None)

    def test_content(self):
        """Expected to parse string content."""
        lines = ['tags: ~', '...',
                 '${site.url}', '<!--more-->', '${post.url}']
        txt = '\n'.join(lines)

        meta = Namespace(year=2012, month=1, day=1, idx='', stub='test')
        test = blogit.Post(content=txt, config=self.config, defaults=meta)

        expected = []
        self.assertEqual(test.tags, expected)

        expected = '\n' + '\n'.join(lines[2:])
        self.assertEqual(test.markdown, expected)

        expected = '\n'.join([
            '<p>' + self.config.url, blogit.REPLACE_MORE,
            blogit.FORMAT_POST_URL.format(self.config.blog_url, meta) + '</p>'
        ])
        self.assertEqual(test.get_html(), expected)

        expected = '<p>' + self.config.url + '</p>'
        self.assertEqual(test.get_summary(), expected)

        self.assertTrue(test.is_rss_safe())
        self.assertFalse(test.is_future())
        self.assertFalse(test.is_updated())

        expected = 'Sunday, January 01, 2012'
        self.assertEqual(test.get_published(), expected)
        self.assertEqual(test.get_updated(), expected)

        test.updated = datetime(year=meta.year, month=meta.month,
                                day=meta.day + 1)
        self.assertNotEqual(test.get_updated(), expected)

    def test_load(self):
        """Expected to load post from file."""
        path = os.path.join(TEST_DIR, '_posts', '2012-01-01.01-test.markdown')
        test = blogit.Post(path, config=self.config)

        self.assertNotEqual(test.get_html(), '')
