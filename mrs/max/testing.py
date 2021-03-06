from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class MrsmaxLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import mrs.max
        xmlconfig.file(
            'configure.zcml',
            mrs.max,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        #z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'mrs.max:default')

MRS_MAX_FIXTURE = MrsmaxLayer()
MRS_MAX_INTEGRATION_TESTING = IntegrationTesting(
    bases=(MRS_MAX_FIXTURE,),
    name="MrsmaxLayer:Integration"
)
MRS_MAX_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(MRS_MAX_FIXTURE, z2.ZSERVER_FIXTURE),
    name="MrsmaxLayer:Functional"
)
