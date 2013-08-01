from five import grok
from zope.interface import Interface
from Products.CMFCore.utils import getToolByName
from pas.plugins.preauth.interfaces import IPreauthTask, IPreauthHelper
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.interface import implements
from zope.component import adapts

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

import logging

logger = logging.getLogger('mrs.max')


class IMAXClient(Interface):
    """ Marker for MaxClient global utility """

class max_client_utility(object):
    grok.implements(IMAXClient)

    def __call__(self):
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)
        return (settings, MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=settings.oauth_grant_type))

grok.global_utility(en_GB, provides=ILanguage, name="en_GB", direct=True)

def getToken(credentials, grant_type=None):
    user = credentials.get('login')
    password = credentials.get('password')
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    # Pick grant type from settings unless passed as optonal argument
    effective_grant_type = grant_type is not None and grant_type or settings.oauth_grant_type

    ## TODO: Do we need to ask for a token always?
    # r = requests.post(settings.oauth_token_endpoint, data=payload, verify=False)
    maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)

    try:
        token = maxclient.getToken(user, password)
        return token
    except AttributeError, error:
        logger.error('oAuth token could not be retrieved for user: %s Reason: %s' % (user, error))
        return ''


class oauthTokenRetriever(object):
    implements(IPreauthTask)
    adapts(IPreauthHelper)

    def __init__(self, context):
        self.context = context

    def execute(self, credentials):
        user = credentials.get('login')
        pm = getToolByName(self.context, "portal_membership")
        member = pm.getMemberById(user)

        if user == "admin":
            return

        oauth_token = getToken(credentials)
        member.setMemberProperties({'oauth_token': oauth_token})
        logger.info('oAuth token set for user: %s ' % user)

        return


class maxUserCreator(object):
    implements(IPreauthTask)
    adapts(IPreauthHelper)

    def __init__(self, context):
        self.context = context

    def execute(self, credentials):
        user = credentials.get('login')

        if user == "admin":
            return

        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)
        # Pick grant type from settings unless passed as optonal argument
        effective_grant_type = settings.oauth_grant_type

        maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        try:
            result = maxclient.addUser(user)

            # Temporarily subscribe always the user to the default context
            maxclient.setActor(user)
            maxclient.subscribe(getToolByName(self.context, "portal_url").getPortalObject().absolute_url())

            if result[0]:
                if result[1] == 201:
                    logger.info('MAX user created for user: %s' % user)
                    maxclient.setActor(user)
                    maxclient.subscribe(getToolByName(self.context, "portal_url").getPortalObject().absolute_url())
                if result[1] == 200:
                    logger.info('MAX user already created for user: %s' % user)
            else:
                logger.error('Error creating MAX user for user: %s' % user)
        except:
            logger.error('Could not contact with MAX server.')
