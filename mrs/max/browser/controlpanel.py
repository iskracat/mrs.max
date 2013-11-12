# -*- coding: utf-8 -*-
from zope import schema
from z3c.form import button
from zope.interface import Interface
from zope.component import queryUtility

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.registry.browser import controlpanel
from plone.registry.interfaces import IRegistry

from mrs.max import MRSMAXMessageFactory as _

import logging
from maxclient import MaxClient

from plone.directives import form


DEFAULT_OAUTH_TOKEN_ENDPOINT = u'https://oauth.upc.edu'
DEFAULT_OAUTH_GRANT_TYPE = u'password'
DEFAULT_MAX_SERVER = u'https://max.upc.edu'
DEFAULT_MAX_APP_USERNAME = u'appusername'
DEFAULT_MAX_RESTRICTED_USERNAME = u'restricted'


class IMAXUISettings(form.Schema):
    """Global oAuth settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    oauth_server = schema.TextLine(
        title=_(u'label_oauth_server', default=u'OAuth token endpoint'),
        description=_(u'help_oauth_server',
                        default=u"Please, specify the URI for the oAuth server."),
        required=True,
        default=DEFAULT_OAUTH_TOKEN_ENDPOINT
        )

    oauth_grant_type = schema.TextLine(
        title=_(u'label_oauth_grant_type', default=u'OAuth grant type'),
        description=_(u'help_oauth_grant_type',
                        default=u"Please, specify the oAuth grant type."),
        required=True,
        default=DEFAULT_OAUTH_GRANT_TYPE
        )

    max_server = schema.TextLine(
        title=_(u'label_max_server', default=u'MAX Server URL'),
        description=_(u'help_max_server',
                        default=u"Please, specify the MAX Server URL."),
        required=True,
        default=DEFAULT_MAX_SERVER
        )

    max_server_alias = schema.TextLine(
        title=_(u'label_max_server_alias', default=u'MAX Server URL Alias (Fallback when no CORS available)'),
        description=_(u'help_max_server_alias',
                        default=u"Please, specify the MAX Server URL Alias."),
        required=False,
        default=DEFAULT_MAX_SERVER
        )

    form.mode(max_app_username='hidden')
    max_app_username = schema.TextLine(
        title=_(u'label_max_app_username', default=u'MAX application agent username'),
        description=_(u'help_max_app_username',
                        default=u"Please, specify the MAX application agent username."),
        required=False,
        default=DEFAULT_MAX_APP_USERNAME
        )

    form.mode(max_app_token='hidden')
    max_app_token = schema.Password(
        title=_(u'label_max_app_token', default=u'MAX application token'),
        description=_(u'help_max_app_token',
                        default=u"Please, specify the MAX application token."),
        required=False,
        )

    form.mode(max_restricted_username='hidden')
    max_restricted_username = schema.TextLine(
        title=_(u'label_max_restricted_username', default=u'MAX restricted username'),
        description=_(u'help_max_restricted_username',
                        default=u"Please, specify the MAX restricted username."),
        required=False,
        default=DEFAULT_MAX_RESTRICTED_USERNAME
        )

    form.mode(max_restricted_token='hidden')
    max_restricted_token = schema.Password(
        title=_(u'label_max_restricted_token', default=u'MAX restricted user token'),
        description=_(u'help_max_restricted_token',
                        default=u"Please, specify the MAX restricted user token."),
        required=False,
        )


class MAXUISettingsEditForm(controlpanel.RegistryEditForm):
    """MAXUI settings form.
    """
    schema = IMAXUISettings
    id = "MAXUISettingsEditForm"
    label = _(u"MAX UI settings")
    description = _(u"help_maxui_settings_editform",
                    default=u"Settings related to MAX, including OAuth server "
                             "endpoint and grant method.")

    def updateFields(self):
        super(MAXUISettingsEditForm, self).updateFields()
        #self.fields = self.fields.omit('max_app_token')

    def updateWidgets(self):
        super(MAXUISettingsEditForm, self).updateWidgets()

    @button.buttonAndHandler(_('Save'), name=None)
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@maxui-settings")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"),
                                                      "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(),
                                                  self.control_panel_view))

    # @button.buttonAndHandler(_(u'Get token'), name='getToken')
    # def handleGetToken(self, action):
    #     data, errors = self.extractData()
    #     credentials = dict(login=data.get('max_app_username'),
    #                        password=data.get('max_app_password'))
    #     from upc.maxui.max import getToken
    #     logger = logging.getLogger('upc.maxui')

    #     #Authenticat to max as operations user
    #     maxcli = MaxClient(data.get('max_server'), auth_method="basic")
    #     maxcli.setBasicAuth(data.get('max_ops_username'), data.get('max_ops_password'))

    #     #Add App user to max
    #     result = maxcli.addUser(credentials['login'], displayName=data.get('max_app_displayname'))
    #     if not result:
    #         logger.info('Error creating MAX user for user: %s' % credentials['login'])
    #         IStatusMessage(self.request).addStatusMessage(_(u"An error occurred during creation of max user"), "info")
    #     else:
    #         logger.info('MAX Agent user %s created' % credentials['login'])
    #         # Request token for app user
    #         oauth_token = getToken(credentials)
    #         registry = queryUtility(IRegistry)
    #         settings = registry.forInterface(IMAXUISettings, check=False)
    #         settings.max_app_token = str(oauth_token)

    #         #Subscribe app user to max
    #         club_url = getToolByName(self.context, "portal_url").getPortalObject().absolute_url()
    #         maxcli.setActor(credentials['login'])
    #         maxcli.subscribe(club_url)

    #         logger.info('MAX user %s subscribed to %s' % (credentials['login'], club_url))
    #         IStatusMessage(self.request).addStatusMessage(_(u"Token for MAX application user saved"), "info")


class MAXUISettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    """MAXUI settings control panel.
    """
    form = MAXUISettingsEditForm
    index = ViewPageTemplateFile('controlpanel.pt')

    def update(self):
        registry = queryUtility(IRegistry)
        self.maxui_settings = registry.forInterface(IMAXUISettings)
        super(MAXUISettingsControlPanel, self).update()

    def restricted_token_class(self):
        return self.maxui_settings.max_restricted_token and 'info' or 'warning'

    def app_token_class(self):
        return self.maxui_settings.max_app_token and 'info' or 'warning'
