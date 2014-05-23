from Products.CMFCore.utils import getToolByName
from pas.plugins.preauth.interfaces import IPreauthTask, IPreauthHelper
from plone.registry.interfaces import IRegistry
from zope.component import queryUtility
from zope.interface import implements
from zope.component import adapts

from maxclient.rest import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings
from mrs.max.utilities import prettyResponse

import logging

logger = logging.getLogger('mrs.max')


def getToken(credentials, grant_type=None):
    user = credentials.get('login').lower()
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
        user = credentials.get('login').lower()
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
        user = credentials.get('login').lower()

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
            maxclient.people['user'].post()

            # Temporarily subscribe always the user to the default context
            maxclient.setActor(user)
            portal_url = getToolByName(self.context, "portal_url").getPortalObject().absolute_url()
            maxclient.people[user].subscriptions.post(object_url=portal_url)

            if maxclient.last_response_code == 201:
                logger.info('MAX user created for user: %s' % user)
            elif maxclient.last_response_code == 200:
                logger.info('MAX user already created for user: {}'.format(user))
            else:
                logger.error('Error creating MAX user for user: {}. '.format(user))
                logger.error(prettyResponse(maxclient.last_response))
        except:
            logger.error('Could not contact with MAX server.')
            logger.error(prettyResponse(maxclient.last_response))
