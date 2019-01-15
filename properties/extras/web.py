"""Property classes for web-related concepts"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from six.moves.urllib.parse import ParseResult, urlparse                       #pylint: disable=import-error

from .. import basic

class URL(basic.String):
    """String property that only accepts valid URLs

    This property type uses :code:`urllib.parse` to validate
    input URLs and possibly remove fragments and query params.

    **Available keywords** (in addition to those inherited from
    :class:`String <properties.String>`):

    * **remove_parameters** - Query params are stripped from input URL (default
      is False).
    * **remove_fragment** - Fragment is stripped from input URL (default
      is False).
    """

    class_info = 'a URL'

    @property
    def remove_parameters(self):
        """Should path and query parameters be stripped"""
        return getattr(self, '_remove_parameters', False)

    @remove_parameters.setter
    def remove_parameters(self, value):
        self._remove_parameters = bool(value)

    @property
    def remove_fragment(self):
        """Should fragment be stripped"""
        return getattr(self, '_remove_fragment', False)

    @remove_fragment.setter
    def remove_fragment(self, value):
        self._remove_fragment = bool(value)

    def validate(self, instance, value):
        """Check if input is valid URL"""
        value = super(URL, self).validate(instance, value)
        parsed_url = urlparse(value)
        if not parsed_url.scheme or not parsed_url.netloc:
            self.error(instance, value, extra='URL needs scheme and netloc.')
        parse_result = ParseResult(
            scheme=parsed_url.scheme,
            netloc=parsed_url.netloc,
            path=parsed_url.path,
            params='' if self.remove_parameters else parsed_url.params,
            query='' if self.remove_parameters else parsed_url.query,
            fragment='' if self.remove_fragment else parsed_url.fragment,
        )
        parse_result = parse_result.geturl()
        return parse_result

    @property
    def info(self):
        info = 'a URL string'
        if self.remove_parameters:
            info += ', path or query params removed'
        if self.remove_fragment:
            info += ', fragment removed'
