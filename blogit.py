#!/usr/bin/python
# coding: utf-8

"""Static blog generator.

Blogit is static blog generator similar to Jekyll and Hyde.
"""

from datetime import datetime
from glob import glob
import hashlib
import logging
import os
import re

#from mako.template import Template
from markdown import markdown
import yaml

__author__ = 'The Metaist'
__copyright__ = 'Copyright 2012, Metaist'
__email__ = 'metaist@metaist.com'
__license__ = 'MIT'
__maintainer__ = 'The Metaist'
__status__ = 'Prototype'
__version_info__ = ('0', '0', '1')
__version__ = '.'.join(__version_info__)

DEFAULT_ENV = 'default'  # default target environment

# Date/Time Formats
DATETIME_HUMAN = '%A, %B %d, %Y'
DATETIME_ISO = '%Y-%m-%dT%H:%M:%S+00:00'

# Format Strings
FORMAT_UID = '{0.year}-{0.month}-{0.day}{0.idx}-{0.stub}'
FORMAT_URL = '{0.year}/{0.month}/{0.stub}.html'

# Search Strings
FIND_EOH = '...'  # end-of-header indicator
FIND_MORE = '<!--more-->'  # end-of-summary indicator

# Regular Expressions
REGEX_FILE_NAME = re.compile(r"(\d{4})-(\d\d)-(\d\d)(\.\d\d)?-(.*)\.markdown")
REGEX_RSS_CHECK = re.compile(r"<(iframe|script|object|embed)", re.I)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# pylint: disable=C0103,W0142
metaformat = lambda d: dict([(k, v.format(**d)) for k, v in d.items()])
# pylint: enable=C0103,W0142


class Site(object):
    """Site configuration."""
    # pylint: disable=R0903

    posts = []
    tags = []
    archive = []

    def __init__(self, url='', blog_url='', blog_dir='',
                 img_url='', img_dir=''):
        """Construct a site configuration."""
        # pylint: disable=R0913
        self.url = url
        self.blog_url, self.blog_dir = blog_url, blog_dir
        self.img_url, self.img_dir = img_url, img_dir


class Post(object):
    """Single blog post."""
    # pylint: disable=R0902

    uid, url = '', ''
    published, updated = None, None
    year, month, day, idx, stub = '', '', '', '', ''
    layout, title, author = '', '', ''
    tags = []
    html = ''
    warn_rss = False
    thumbnail = ''

    def __init__(self, site, defaults=None, path=None):
        """Construct a post."""
        self.site = site
        if defaults:
            self.__dict__.update(defaults)

        if path:
            self.parse(path)

    def _set_metadata(self):
        """Set metadata from post attributes."""
        post_id = FORMAT_UID.format(self)
        self.uid = hashlib.sha1(post_id).hexdigest()
        self.url = self.site.blog_url + '/' + FORMAT_URL.format(self)

        self.published = \
            datetime(int(self.year), int(self.month), int(self.day))
        if not self.updated:
            self.updated = self.published

        thumbnail = glob(os.path.join(self.site.img_dir, post_id + '.*'))
        if thumbnail:
            self.thumbnail = (self.site.img_url + '/'
                              + os.path.basename(thumbnail[0]))

    def parse(self, path):
        """Parse a post from a file."""
        if not os.path.isfile(path):
            return  # not a valid file

        self.updated = datetime.utcfromtimestamp(os.path.getmtime(path))

        filename = os.path.basename(path)
        match = REGEX_FILE_NAME.match(filename)
        if match:
            self.year, self.month, self.day, self.idx, self.stub = \
                match.groups('')
            self.render(open(path).read())   # only parse files that match

    def render(self, raw):
        """Render the contents of a post."""
        self._set_metadata()  # for non-file-based metadata

        eoh = raw.find(FIND_EOH)
        yaml_header, markdown_body = {}, raw
        if -1 != eoh:
            yaml_header, markdown_body = \
                yaml.load(raw[0:eoh]), raw[eoh + len(FIND_EOH):]
        self.__dict__.update(yaml_header)

        content = ''
        try:
            content = markdown_body.format(site=self.site, post=self)
        except AttributeError as err:
            logger.error(err)

        self.html = markdown(content, ['extra'], output_format='html5')
        self.warn_rss = REGEX_RSS_CHECK.search(content) is not None

    def is_future(self):
        """Return True if the post is published in the future."""
        return self.published > datetime.now()

    def is_updated(self):
        """Return True if the post has been updated since being published."""
        return self.updated > self.published

    def get_published(self, frmt=DATETIME_HUMAN):
        """Return the date published."""
        result = None
        if self.published:
            result = self.published.strftime(frmt)
        return result

    def get_updated(self, frmt=DATETIME_HUMAN):
        """Return the date updated."""
        result = None
        if self.is_updated():
            result = self.updated.strftime(frmt)
        else:
            result = self.get_published(frmt)
        return result
