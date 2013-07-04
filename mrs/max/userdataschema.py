from zope import schema
from zope.interface import implements
from plone.app.users.userdataschema import IUserDataSchema
from plone.app.users.userdataschema import IUserDataSchemaProvider
from plone.app.users.browser.personalpreferences import UserDataPanelAdapter

from mrs.max import MRSMAXMessageFactory as _


class IEnhancedUserDataSchema(IUserDataSchema):
    """ Use all the fields from the default user data schema, and add various
    extra fields.
    """
    twitter_username = schema.TextLine(
        title=_(u'label_twitter', default=u'Twitter username'),
        description=_(u'help_twitter',
                      default=u"Fill in your Twitter username."),
        required=False,
    )


class UserDataSchemaProvider(object):
    implements(IUserDataSchemaProvider)

    def getSchema(self):
        """
        """
        return IEnhancedUserDataSchema


class EnhancedUserDataPanelAdapter(UserDataPanelAdapter):
    def get_twitter_username(self):
        return self.context.getProperty('twitter_username', '')

    def set_twitter_username(self, value):
        return self.context.setMemberProperties({'twitter_username': value})
    twitter_username = property(get_twitter_username, set_twitter_username)
