from OFS.Image import Image
from AccessControl import Unauthorized
from zope.component import getUtility
from Products.PlonePAS.utils import scale_image
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import ManageUsers

from mrs.max.utilities import IMAXClient

from PIL import Image as PILImage
from cStringIO import StringIO


def changeMemberPortrait(self, portrait, id=None):
    """update the portait of a member.

    We URL-quote the member id if needed.

    Note that this method might be called by an anonymous user who
    is getting registered.  This method will then be called from
    plone.app.users and this is fine.  When called from restricted
    python code or with a curl command by a hacker, the
    declareProtected line will kick in and prevent use of this
    method.
    """
    authenticated_id = self.getAuthenticatedMember().getId()
    if not id:
        id = authenticated_id
    safe_id = self._getSafeMemberId(id)
    if authenticated_id and id != authenticated_id:
        # Only Managers can change portraits of others.
        if not _checkPermission(ManageUsers, self):
            raise Unauthorized
    if portrait and portrait.filename:
        #scaled, mimetype = scale_image(portrait, max_size=(250, 250))
        scaled, mimetype = convertSquareImage(portrait)
        portrait = Image(id=safe_id, file=scaled, title='')
        membertool = getToolByName(self, 'portal_memberdata')
        membertool._setPortrait(portrait, safe_id)

        # Update the user's avatar on MAX
        memberdata = self.getMemberById(authenticated_id)
        oauth_token = memberdata.getProperty('oauth_token', '')
        scaled.seek(0)

        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(authenticated_id)
        maxclient.setToken(oauth_token)
        maxclient.postAvatar(authenticated_id, scaled)


def convertSquareImage(image_file):
    image = PILImage.open(image_file)
    format = image.format
    mimetype = 'image/%s' % format.lower()

    if image.size[0] > 250 or image.size[1] > 250:
        image.thumbnail((250, 9800), PILImage.ANTIALIAS)
        image = image.transform((250, 250), PILImage.EXTENT, (0, 0, 250, 250), PILImage.BICUBIC)

    new_file = StringIO()
    image.save(new_file, format, quality=88)
    new_file.seek(0)

    return new_file, mimetype
