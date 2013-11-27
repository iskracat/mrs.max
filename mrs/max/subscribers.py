from five import grok
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite

from plone.registry.interfaces import IRegistry
from plone.app.controlpanel.interfaces import IConfigurationChangedEvent

from Products.CMFCore.utils import getToolByName
from Products.PluggableAuthService.interfaces.authservice import IPropertiedUser
from Products.PluggableAuthService.interfaces.events \
    import IPrincipalCreatedEvent

from maxclient import MaxClient
from mrs.max.utilities import IMAXClient
from mrs.max.browser.controlpanel import IMAXUISettings

import logging

logger = logging.getLogger('mrs.max')


@grok.subscribe(IConfigurationChangedEvent)
def updateMAXUserInfo(event):
    """This subscriber will trigger when a user change his/her profile data."""

    # Only execute if the event triggers on user profile data change
    if 'fullname' in event.data:
        site = getSite()
        pm = getToolByName(site, "portal_membership")
        if pm.isAnonymousUser():  # the user has not logged in
            username = ''
            return
        else:
            member = pm.getAuthenticatedMember()

        username = member.getUserName()
        memberdata = pm.getMemberById(username)
        properties = dict(displayName=memberdata.getProperty('fullname', ''),
                          twitterUsername=memberdata.getProperty('twitter_username', '')
                          )

        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)
        effective_grant_type = settings.oauth_grant_type
        oauth_token = memberdata.getProperty('oauth_token', '')

        maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)
        maxclient.setActor(username)
        maxclient.setToken(oauth_token)

        maxclient.modifyUser(username, properties)


@grok.subscribe(IConfigurationChangedEvent)
def updateOauthServerOnOsirisPASPlugin(event):
    """This subscriber will trigger when an admin updates the MAX settings."""

    if 'oauth_server' in event.data:
        portal = getSite()
        portal.acl_users.pasosiris.oauth_server = event.data['oauth_server']


@grok.subscribe(IPropertiedUser, IPrincipalCreatedEvent)
def createMAXUser(principal, event):
    """This subscriber will trigger when a user is created."""

    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(settings.max_restricted_username)
    maxclient.setToken(settings.max_restricted_token)

    user = principal.getId()

    try:
        result = maxclient.addUser(user)

        if result[0]:
            if result[1] == 201:
                logger.info('MAX user created for user: %s' % user)
            if result[1] == 200:
                logger.info('MAX user already created for user: %s' % user)
        else:
            logger.error('Error creating MAX user for user: %s' % user)
    except:
        logger.error('Could not contact with MAX server.')
