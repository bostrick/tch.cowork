
from plone import api
from zope import schema

from plone.app.portlets.portlets import base
from zope.interface import implements
from zope.formlib import form

from plone.portlets.interfaces import IPortletDataProvider
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from tch.cowork import MessageFactory as _

class IMembershipPortlet(IPortletDataProvider):

    member_info_path = schema.TextLine (
        title = _(u"Membership Information Item Path"),
        description = _(u"Path is relative to the portal url."),
        required=False,
    )

class Assignment(base.Assignment):

    implements(IMembershipPortlet)

    def __init__(self, member_info_path=None):
        self.member_info_path = member_info_path

    @property
    def title(self):
        return _(u"Membership Information")


class AddForm(base.AddForm):

    form_fields = form.Fields(IMembershipPortlet)
    label = _(u"Add Membership Portlet")
    description = _(u"This portlet displays membership information.")

    def create(self, data):
        return Assignment(data["member_info_path"])

class EditForm(base.EditForm):

    form_fields = form.Fields(IMembershipPortlet)
    label = _(u"Edit Membership Portlet")
    description = _(u"This portlet displays membership information.")

class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('templates/membership_portlet.pt')

    def __init__(self, *args):

        base.Renderer.__init__(self, *args)

        self.portal_url = api.portal.get().absolute_url()
        self.minfo_url = self.portal_url + "/" + self.data.member_info_path
        self.member_status = self.get_member_status()
        self.is_member = bool(self.member_status == "member")

    def render(self):
        return self._template()

    @property
    def available(self):
        return not self.is_member

    def get_member_status(self):

        if api.user.is_anonymous():
            return "unknown"

        user = api.user.get_current()
        if "Member" in api.user.get_roles(user=user):
            return "member"

        return "nonmember"

