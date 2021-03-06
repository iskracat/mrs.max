from five import grok
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

import logging

logger = logging.getLogger('mrs.max')


class IMAXClient(Interface):
    """ Marker for MaxClient global utility """

class max_client_utility(object):
    """ The utility will return a tuple with the settins and an instance of a
        MaxClient object
    """
    grok.implements(IMAXClient)

    def __call__(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)
        return (MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=settings.oauth_grant_type),
                settings)

grok.global_utility(max_client_utility)
