from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.publisher.browser import BrowserView

from Products.CMFCore.utils import getToolByName

from plone.registry.interfaces import IRegistry

from mrs.max.browser.controlpanel import IMAXUISettings

TEMPLATE = """\
if (!window._MAXUI) {window._MAXUI = {}; }
window._MAXUI.username = '%(username)s';
window._MAXUI.oauth_token = '%(oauth_token)s';
window._MAXUI.oauth_grant_type = '%(oauth_grant_type)s';
window._MAXUI.max_server = '%(max_server)s';
window._MAXUI.max_server_alias = '%(max_server_alias)s';
window._MAXUI.avatar_url = '%(avatar_url)s';
window._MAXUI.profile_url = '%(profile_url)s'
window._MAXUI.contexts = '%(contexts)s';
window._MAXUI.activitySource = '%(activitySource)s';
window._MAXUI.activitySortView = '%(activitySortView)s';
window._MAXUI.language = '%(language)s';
window._MAXUI.hidePostboxOnTimeline = true;
window._MAXUI.domain = '%(max_domain)s';
"""


class MAXJSVariables(BrowserView):

    def __call__(self, *args, **kwargs):
        context = self.context
        response = self.request.response
        portal_url = getSite().absolute_url()
        response.addHeader('content-type', 'text/javascript;;charset=utf-8')
        response.addHeader('Cache-Control', 'must-revalidate, max-age=0, no-cache, no-store')

        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)

        pm = getToolByName(context, "portal_membership")
        if pm.isAnonymousUser():  # the user has not logged in
            username = ''
            oauth_token = ''
        else:
            member = pm.getAuthenticatedMember()
            username = member.getUserName()
            member = pm.getMemberById(username)
            oauth_token = member.getProperty('oauth_token', None)

        # Use the restricted username and token in case we are admin.
        if username == 'admin':
            username = settings.max_restricted_username
            oauth_token = settings.max_restricted_token

        pl = getToolByName(self.context, "portal_languages")
        default_lang = pl.getDefaultLanguage()

        return TEMPLATE % dict(
            username=username,
            oauth_token=oauth_token,
            oauth_grant_type=settings.oauth_grant_type,
            max_server=settings.max_server,
            max_server_alias=settings.max_server_alias,
            avatar_url='%s/people/{0}/avatar/large' % (settings.max_server),
            profile_url='%s/profile/{0}' % (portal_url),
            contexts=self.context.absolute_url(),
            activitySource='timeline',
            activitySortView=self.context.activity_view,
            language=default_lang,
            max_domain=settings.max_domain
        )
