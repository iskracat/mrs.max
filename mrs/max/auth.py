from plone import api
from pas.plugins.preauth.interfaces import IPreauthTask
from pas.plugins.preauth.interfaces import IPreauthHelper

from zope.component import getUtility
from zope.interface import implements
from zope.component import adapts

from mrs.max.utilities import prettyResponse
from mrs.max.utilities import IMAXClient

import logging

logger = logging.getLogger('mrs.max')


def getToken(credentials, grant_type=None):
    user = credentials.get('login').lower()
    password = credentials.get('password')

    maxclient, settings = getUtility(IMAXClient)()

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
        pm = api.portal.get_tool(name='portal_membership')
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

        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        try:
            maxclient.people[user].post()

            if maxclient.last_response_code == 201:
                logger.info('MAX user created for user: %s' % user)
            elif maxclient.last_response_code == 200:
                logger.info('MAX user already created for user: {}'.format(user))
            else:
                logger.error('Error creating MAX user for user: {}. '.format(user))
                logger.error(prettyResponse(maxclient.last_response))

            # Temporarily subscribe always the user to the default context
            # July2014 - Victor: Disable automatic subscription to the default
            # context as it was proven to not be used anymore.
            # maxclient.setActor(user)
            # portal_url = api.portal.get().absolute_url()
            # maxclient.people[user].subscriptions.post(object_url=portal_url)

        except:
            logger.error('Could not contact with MAX server.')
            logger.error(prettyResponse(maxclient.last_response))
