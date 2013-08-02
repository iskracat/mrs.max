from five import grok
from zope.component import queryUtility
from zope.component.hooks import getSite

from plone.registry.interfaces import IRegistry
from plone.app.controlpanel.interfaces import IConfigurationChangedEvent

from Products.CMFCore.utils import getToolByName

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings


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
