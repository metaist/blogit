#!/usr/bin/python
# coding: utf-8

"""Static blog generator.

Blogit is a static blog generator similar to Jekyll and Hyde, but simpler.
"""

#from cgi import escape
from datetime import datetime
from glob import glob
import argparse
import hashlib
import os
import re

from mako.lookup import TemplateLookup
from mako.template import Template
from markdown import markdown
import yaml

from metautils import interpolate, Namespace

__author__ = 'The Metaist'
__copyright__ = 'Copyright 2013, Metaist'
__email__ = 'metaist@metaist.com'
__license__ = 'MIT'
__maintainer__ = 'The Metaist'
__status__ = 'Prototype'
__version_info__ = ('0', '0', '2')
__version__ = '.'.join(__version_info__)

TODAY = datetime.today()

# Default Environment
ENV_DEFAULT = 'default'
ENV_FILE = '_config.yml'
ENV_CONFIG = Namespace(interpolate({
    # URLs
    'url': '/',
    'blog_url': '{url}/blog',
    'img_url': '{url}/img',

    # Directories
    'blog_dir': 'blog',
    'img_dir': 'img',
    'layouts_dir': '_layouts',
    'posts_dir': '_posts',
    'temp_dir': '_tmp',

    # Post Defaults
    'default_layout': 'post',
    'default_title': 'Untitled',
}))

DEFAULT_PREFIX = 'default_'

# Date/Time Formats
DATETIME_HUMAN = '%A, %B %d, %Y'
DATETIME_ISO = '%Y-%m-%dT%H:%M:%S+00:00'
DATETIME_MONTH_YEAR = '%b %Y'

# Format Strings
FORMAT_POST_UID = '{0.year:04}-{0.month:02}-{0.day:02}{0.idx}-{0.stub}'
FORMAT_POST_URL = '{0}/{1.year:04}/{1.month:02}/{1.stub}.html'

# Search Strings
FIND_EOH = '...'  # end-of-header indicator
FIND_MORE = '<!--more-->'  # end-of-summary indicator
REPLACE_MORE = '<a id="more">&nbsp;</a>'

# Regular Expressions
REGEX_FILE_NAME = re.compile(r"(\d{4})-(\d\d)-(\d\d)(\.\d\d)?-(.*)\.markdown")
REGEX_RSS_CHECK = re.compile(r"<(iframe|script|object|embed)", re.I)


def render_markdown(content):
    """Returns rendered markdown.

    >>> render_markdown('foo') == '<p>foo</p>'
    True
    """
    return markdown(content, ['extra'], output_format='html5')


def render_mako(content, **data):
    """Returns rendered mako.

    >>> render_mako('${foo}', foo='bar') == 'bar'
    True
    """
    return Template(content).render(**data)


class Post(object):
    """Single blog post."""
    # pylint: disable=R0902

    layout, updated, published = '', None, None
    year, month, day, idx, stub = TODAY.year, TODAY.month, TODAY.day, '', ''
    post_id, uid, url, markdown = '', '', '', ''
    title, author, thumbnail, tags = '', '', '', []

    def __init__(self, content, config=None, defaults=None):
        """Construct a post."""
        self._config = config or ENV_CONFIG
        self.__dict__.update(dict([
            (key[len(DEFAULT_PREFIX):], val)
            for key, val in self._config.items()
            if key.startswith(DEFAULT_PREFIX)
        ]))

        self.__dict__.update(defaults or {})

        assert type(content) is str, 'content must be a str'
        if os.path.isfile(content):
            self.load(content)
        else:
            self.parse(content)

    def load(self, path):
        """Create a post from a file."""
        assert os.path.isfile(path), "path not found: %s" % path

        match = REGEX_FILE_NAME.match(os.path.basename(path))
        if match:
            self.updated = datetime.utcfromtimestamp(os.path.getmtime(path))
            self.year, self.month, self.day, self.idx, self.stub = \
                match.groups('')

            for part in ['year', 'month', 'day']:  # convert to int
                setattr(self, part, int(getattr(self, part)))

            self.parse(open(path).read())  # only parse valid files

    def parse(self, raw):
        """Parse the contents of a post."""
        self.post_id = FORMAT_POST_UID.format(self)
        self.uid = hashlib.sha1(self.post_id).hexdigest()
        self.url = FORMAT_POST_URL.format(self._config.blog_url or '', self)

        self.published = datetime(self.year, self.month, self.day)
        if not self.updated:
            self.updated = self.published

        self.thumbnail = self.get_thumbnail_url()
        self.markdown = raw
        eoh = raw.find(FIND_EOH)
        if -1 != eoh:
            self.markdown = raw[eoh + len(FIND_EOH):]
            self.__dict__.update(yaml.load(raw[0:eoh]))

        if not self.tags:
            self.tags = []
        elif type(self.tags) is not list:
            self.tags = [self.tags]

    def get_html(self):
        """Return HTML rendering of the post."""
        site = self._config
        content = self.markdown.replace(FIND_MORE, REPLACE_MORE)
        return render_mako(render_markdown(content), site=site, post=self)

    def get_summary(self):
        """Return HTML of the post summary."""
        site = self._config
        content = self.markdown
        pos = self.markdown.find(FIND_MORE)
        if -1 != pos:
            content = self.markdown[:pos]
        return render_mako(render_markdown(content), site=site, post=self)

    def get_thumbnail_url(self, img_dir=None, img_url=None):
        """Return the url to the thumbnail."""
        img_dir = img_dir or self._config.img_dir
        img_url = img_url or self._config.img_url

        result = glob(os.path.join(img_dir, self.post_id + '.*'))
        if result:
            result = '{0}/{1}'.format(img_url, os.path.basename(result[0]))
        else:
            result = None
        return result

    def is_rss_safe(self):
        """Return True if the post does not contain invalid tags for RSS."""
        return REGEX_RSS_CHECK.search(self.markdown) is None

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


class Blogit(object):
    """Site generator."""
    def __init__(self, config=None):
        """Constructs a new Blogit generator.

        >>> x = Blogit(config='test/_config.yml')
        >>> x is not None
        True
        """
        if type(config) is str:  # load the config
            self._config = Blogit.parse_config(path=config)
        else:  # use the supplied config
            self._config = config

        self.posts = self.parse_posts()

        self.tlookup = TemplateLookup(
            directories=[self._config.layouts_dir],
            module_directory=self._config.temp_dir
        )

    @staticmethod
    def parse_config(path=ENV_FILE, env=ENV_DEFAULT):
        """Parse a configuration file.

        >>> Blogit.parse_config('test/_config.yml') is not None
        True
        """
        result = {}
        assert os.path.isfile(path), 'path not found: {0}'.format(path)

        configs = yaml.load(open(path))
        assert type(configs) is dict, 'configuration must be a valid dict'

        if ENV_DEFAULT in configs:  # first use default environment
            result.update(configs[ENV_DEFAULT])
        if env in configs:  # next use provided environment
            result.update(configs[env])

        return Namespace(interpolate(result))

    def parse_posts(self, posts_dir=None):
        """Parse a directory full of posts."""
        posts_dir = posts_dir or self._config.posts_dir

        assert os.path.isdir(posts_dir), \
            'directory not found: {0}'.format(posts_dir)

        posts = []
        for file_name in sorted(os.listdir(posts_dir), reverse=True):
            path = os.path.join(posts_dir, file_name)
            post = Post(path, config=self._config)
            posts.append(post)

        for idx, post in enumerate(posts):
            if idx > 0:
                post.newer = posts[idx - 1]

            if idx < (len(posts) - 1):
                post.older = posts[idx + 1]

        return posts

    #def render(self, name, **kwargs):
    #    """Renders a Mako template."""
    #    return self.tlookup.get_template(name).render(**kwargs)


def main(args=None):  # pragma: no cover
    """Main entry point.

    >>> main(['--file=test/_config.yml']) is None
    True
    """
    parser = argparse.ArgumentParser(description=__doc__, prog='Blogit')
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-e', '--env', default=ENV_DEFAULT,
                        help='target environment (default: "%(default)s")')
    parser.add_argument('-f', '--file', default=ENV_FILE,
                        help='configuration file (default: "%(default)s")')
    opts = parser.parse_args(args)  # command-line args parsed

    config = Blogit.parse_config(opts.file, opts.env)
    Blogit(config)


if '__main__' == __name__:  # pragma: no cover
    main()
