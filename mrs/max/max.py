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


def getToken(credentials, grant_type=None):
    user = credentials.get('login')
    password = credentials.get('password')
    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    # Pick grant type from settings unless passed as optonal argument
    effective_grant_type = grant_type != None and grant_type or settings.oauth_grant_type

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

        if user == "admin":
            return

        oauth_token = getToken(credentials)

        pm = getToolByName(self.context, "portal_membership")
        member = pm.getMemberById(user)
        member.setMemberProperties({'oauth_token': oauth_token})

        logger.error('oAuth token set for user: %s ' % user)


class maxUserCreator(object):
    implements(IPreauthTask)
    adapts(IPreauthHelper)

    def __init__(self, context):
        self.context = context

    def execute(self, credentials):
        user = credentials.get('login')
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)
        # Pick grant type from settings unless passed as optonal argument
        effective_grant_type = settings.oauth_grant_type

        if user == "admin":
            return

        maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)
        result = maxclient.addUser(user)

        if not result:
            logger.error('Error creating MAX user for user: %s' % user)
        else:
            logger.error('MAX user created for user: %s' % user)
            maxclient.setActor(user)
            maxclient.subscribe(getToolByName(self.context, "portal_url").getPortalObject().absolute_url())
