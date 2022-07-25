from kitconcept import api
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.multilingual.testing import PLONE_APP_MULTILINGUAL_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.testing.zope import WSGI_SERVER_FIXTURE

import kitconcept.contentcreator


class ContentcreatorCoreLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_MULTILINGUAL_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=kitconcept.contentcreator)

    def setUpPloneSite(self, portal):
        setRoles(portal, TEST_USER_ID, ["Manager"])
        login(portal, TEST_USER_NAME)
        api.content.create(
            type="Document", id="front-page", title="Welcome", container=portal
        )
        applyProfile(portal, "plone.restapi:blocks")
        logout()


CONTENTCREATOR_CORE_FIXTURE = ContentcreatorCoreLayer()


CONTENTCREATOR_CORE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CONTENTCREATOR_CORE_FIXTURE,),
    name="ContentcreatorCoreLayer:IntegrationTesting",
)


CONTENTCREATOR_CORE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CONTENTCREATOR_CORE_FIXTURE, WSGI_SERVER_FIXTURE),
    name="ContentcreatorCoreLayer:FunctionalTesting",
)


CONTENTCREATOR_CORE_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        CONTENTCREATOR_CORE_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        WSGI_SERVER_FIXTURE,
    ),
    name="ContentcreatorCoreLayer:AcceptanceTesting",
)
