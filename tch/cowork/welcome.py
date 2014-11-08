
from datetime import datetime

from Acquisition import aq_inner
from zope.component import getMultiAdapter

from five import grok
from zope.interface import Interface
from zope.interface import invariant, Invalid
from plone import api

from plone.directives import form
from zope import schema

from z3c.form import button
from z3c.form import field

from Products.CMFCore.interfaces import ISiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from Products.PlonePAS.interfaces.browser import IPASSearchView

from tch.cowork import MessageFactory as _

######################################################################
# helpers
######################################################################

class INullInterface(Interface): pass

class SessionValueProvider(grok.Adapter):
    
    grok.context(ISiteRoot)
    grok.provides(INullInterface)  # subclass responsibility 

    def __init__(self, context):

        super(SessionValueProvider, self).__init__(context)

        self.session = \
            self.context.session_data_manager.getSessionData(create=True)

        self.update()

    def update(self): pass

class CleanBaseView(grok.View):

    grok.context(Interface)
    grok.require('zope2.View')
    grok.name('clean_base')


######################################################################
# hello form
######################################################################

class IHelloForm(form.Schema):

    email = schema.TextLine(
            title=u"Let's start with your email address...",
        )

class HelloForm(form.SchemaForm):

    grok.context(ISiteRoot)
    #grok.require('zope2.View')
    grok.name('hello')

    schema = IHelloForm
    ignoreContext = True
    enable_unload_protection = False
    #enableCSRFProtection = True

    label = u"Welcome to TheClubhou.se"
    #description = u"How can we help you?"

    @button.buttonAndHandler(u'Onward...')
    def handleApply(self, action):

        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        email = data.get("email")
        session = self.context.session_data_manager.getSessionData(create=True)

        search_view = getMultiAdapter(
            (aq_inner(self.context), self.request), name='pas_search')

        next_form = "@@join"
        hits = search_view.searchUsers(email=email)

        if len(hits) == 1:

            # clean hit
            session.set('hello_hits', hits[0]['login'])
            next_form = "@@welcome_back"

        elif hits:

            # if not a single email hit, broaden the search to login as well
            uu = search_view.searchUsers(login=email)
            hits = search_view.merge(hits+uu, 'userid')
            next_form = "@@which_sounds_like_you"

        session.set('hello_email', email)
        session.set('hello_hits', [ i['login'] for i in hits ])

        self.request.response.redirect(next_form)

######################################################################
# join form
######################################################################

def valid_username_constraint(username):

    u = api.user.get(username=username)
    if u:
        msg = _("That username is alredy taken.")
        raise Invalid(msg)

    pr = api.portal.get_tool('portal_registration')
    if not pr.isMemberIdAllowed(username):
        msg = _("That username cannot be used.")
        raise Invalid(msg)

    return True

def email_is_not_in_use_constraint(email):

    # FIXME: implement
    #u = api.user.get(username=username)
    #if u:
    #    msg = _("That username is alredy taken.")
    #    raise Invalid(msg)

    return True

def password_is_valid_constraint(password):

    if len(password) < 6:
        msg = _("passwords must be at least 6 characters")
        raise Invalid(msg)

    return True

class IJoinInfo(form.Schema):

    username = schema.TextLine(
                title=u"Username",
                constraint=valid_username_constraint,
               )

    email = schema.TextLine(
                title=u"Email Address",
                constraint=email_is_not_in_use_constraint,
            )

    password = schema.Password(
                title=u"Password",
                constraint=password_is_valid_constraint,
            )

    password_confirm = schema.Password(
                title=u"Confirm Password",
            )

#    @invariant
#    def vet_password(data):
#
#        import pdb; pdb.set_trace()
#
#        if data.password != data.password_confirm:
#            msg = _("password and password conrimation do not agree")
#            raise Invalid(msg)


class JoinDefaultProvider(SessionValueProvider):

    grok.provides(IJoinInfo)

    def update(self):
        self.email = self.session.get("hello_email")

class JoinForm(form.SchemaForm):

    grok.name('join')
    grok.require('zope2.View')
    grok.context(ISiteRoot)

    schema = IJoinInfo

    enable_unload_protection = False
    #enableCSRFProtection = True

    label = u"Create an Account"
    description = u"The first step is to create an account on our site."

    @button.buttonAndHandler(u'Onward...')
    def handleApply(self, action):

        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        if data["password"] != data["password_confirm"]:
            self.status = _(u"Passwords do not agree.")
            return

        username = data["username"]

        # create the new user
        try:
            new_user = api.user.create (
                email=data["email"],
                username=username,
                password=data["password"],
                roles=[],
                #properties={},
            )
        except ValueError, e:
            self.status = str(e)
            return

        msg = _("Created user %s" % username)
        IStatusMessage(self.request).add(msg)

        return

        # and log in as the new user

        request.response.redirect("login")

        #usess = self.context.acl_users.session
        #usess._setupSession(username, self.context.REQUEST.RESPONSE)
        #self.request.RESPONSE.redirect(self.portal_state.portal_url())
#
#        pm = api.portal.get_tool('portal_membership')
#        pm.loginUser(self.request)
#
#        msg = _("Logged in as user %s" % username)
#        IStatusMessage(self.request).add(msg)

class HelloAgainForm(form.SchemaForm):

    grok.name('helloagain')
    grok.require('zope2.View')
    grok.context(ISiteRoot)

    schema = IHelloForm
    ignoreContext = True
    #enable_unload_protection = False
    #enableCSRFProtection = True

    label = u"Welcome back!"
    #description = u"How can we help you?"

    @button.buttonAndHandler(u'Onward...')
    def handleApply(self, action):

        data, errors = self.extractData()

        if errors:
            self.status = self.formErrorsMessage
            return

        email = data.get("email")
        session = self.context.session_data_manager.getSessionData(create=True)
        session.set('hello_email', email)

        search_view = getMultiAdapter(
            (aq_inner(self.context), self.request), name='pas_search')

        ee = search_view.searchUsers(email=email)
        if len(ee) == 1:
            session.set('hello_hits', ee[0]['login'])
        else:
            # if not a single email hit, broaden the search to login as well
            uu = search_view.searchUsers(login=email)
            hits = search_view.merge(ee+uu, 'userid')
            session.set('hello_hits', [ i['login'] for i in hits ])


