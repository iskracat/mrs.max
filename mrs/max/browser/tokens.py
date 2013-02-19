from five import grok
from plone.directives import form

from zope import schema
from z3c.form import button
from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from Products.CMFCore.interfaces import ISiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from mrs.max import MRSMAXMessageFactory as _
from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

grok.templatedir('views_templates')


class ICredentials(form.Schema):

    username = schema.TextLine(
            title=_(u"The username."),
        )

    password = schema.Password(
            title=_(u"Password"),
            description=_(u"The provided username account password."),
        )


class getTokenForm(form.SchemaForm):
    grok.baseclass()

    schema = ICredentials
    ignoreContext = True

    label = _(u"Get a valid token")
    description = _(u"Give the credentials of a valid account.")

    def update(self):
        # disable Plone's editable border
        self.request.set('disable_border', True)

        registry = queryUtility(IRegistry)
        self.maxui_settings = registry.forInterface(IMAXUISettings)

        # call the base class version - this is very important!
        super(getTokenForm, self).update()


class getRestrictedTokenForm(getTokenForm):
    grok.name('getRestrictedToken')
    grok.require('cmf.ManagePortal')
    grok.template('gettokenform')
    grok.context(ISiteRoot)

    @button.buttonAndHandler(_(u'Get token'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Handle order here. For now, just print it to the console. A more
        # realistic action would be to send the order to another system, send
        # an email, or similar

        username = data['username']
        password = data['password']

        maxclient = MaxClient(self.maxui_settings.max_server, self.maxui_settings.oauth_server)
        self.maxui_settings.max_restricted_username = username

        try:
            self.maxui_settings.max_restricted_token = maxclient.getToken(username, password)
            IStatusMessage(self.request).addStatusMessage(
                "Restricted token issued for user: {}".format(username),
                "info")
        except AttributeError, error:
            IStatusMessage(self.request).addStatusMessage(
                error,
                "error")

        # Redirect back to the front page with a status message
        self.request.response.redirect("{}/{}".format(self.context.absolute_url(), '@@maxui-settings'))


class getAppTokenForm(getTokenForm):
    grok.name('getAppToken')
    grok.require('cmf.ManagePortal')
    grok.template('gettokenform')
    grok.context(ISiteRoot)

    @button.buttonAndHandler(_(u'Get token'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Handle order here. For now, just print it to the console. A more
        # realistic action would be to send the order to another system, send
        # an email, or similar

        username = data['username']
        password = data['password']

        maxclient = MaxClient(self.maxui_settings.max_server, self.maxui_settings.oauth_server)
        self.maxui_settings.max_app_username = username

        try:
            self.maxui_settings.max_app_token = maxclient.getToken(username, password)
            IStatusMessage(self.request).addStatusMessage(
                "App token issued for user: {}".format(username),
                "info")
        except AttributeError, error:
            IStatusMessage(self.request).addStatusMessage(
                error,
                "error")

        # Redirect back to the front page with a status message
        self.request.response.redirect("{}/{}".format(self.context.absolute_url(), '@@maxui-settings'))
