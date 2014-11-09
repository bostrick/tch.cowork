
from datetime import datetime

from Acquisition import aq_inner
from zope.component import getMultiAdapter

from five import grok
from zope.interface import Interface
from zope.interface import invariant, Invalid
from plone import api

from plone.app.layout.viewlets.interfaces import IAboveContent
from tch.cowork import MessageFactory as _
from tch.cowork.interfaces import IMembershipRelated

class RegisterTeaser(grok.Viewlet):

    """ 
    """

    grok.viewletmanager(IAboveContent)
    grok.context(IMembershipRelated)

    def available(self):

        cs = self.context.restrictedTraverse("@@plone_context_state")
        if not cs.is_view_template():
            return False

        if api.user.is_anonymous():
            return True

        current_user = api.user.get_current()
        return not 'Member' in api.user.get_roles(user=current_user)

