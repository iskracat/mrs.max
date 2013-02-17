from five import grok
from plone.directives import form

from zope import schema
from z3c.form import button

from Products.CMFCore.interfaces import ISiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from mrs.max import MRSMAXMessageFactory as _

grok.templatedir('views_templates')


class ICredentials(form.Schema):

    username = schema.ASCIILine(
            title=_(u"The username."),
        )

    password = schema.Password(
            title=_(u"Password"),
            description=_(u"The provided username account password."),
        )


class getTokenForm(form.SchemaForm):
    grok.name('getToken')
    grok.require('cmf.ManagePortal')
    grok.context(ISiteRoot)

    schema = ICredentials
    ignoreContext = True

    label = _(u"Get a valid token")
    description = _(u"Give the credentials of a valid account.")

    def update(self):
        # disable Plone's editable border
        self.request.set('disable_border', True)

        # call the base class version - this is very important!
        super(getTokenForm, self).update()

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

        # Redirect back to the front page with a status message

        IStatusMessage(self.request).addStatusMessage(
                _(u"Thank you for your order. We will contact you shortly"),
                "info"
            )

        contextURL = self.context.absolute_url()
        self.request.response.redirect(contextURL)
