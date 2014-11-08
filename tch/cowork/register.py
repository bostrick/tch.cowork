
from datetime import datetime

from contextlib import contextmanager

from Acquisition import aq_inner
from zope.component import getMultiAdapter

from five import grok
from zope.interface import Interface
from zope.interface import invariant, Invalid
from plone import api
from plone.dexterity.utils import createContentInContainer

from plone.directives import form
from zope import schema

from z3c.form import button
from z3c.form import field
from z3c.relationfield.relation import create_relation

from Products.CMFCore.interfaces import ISiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from Products.PlonePAS.interfaces.browser import IPASSearchView

from tch.cowork import MessageFactory as _
from totav.stripe.card import months_vocab, years_vocab

######################################################################
# helpers
######################################################################

#class INullInterface(Interface): pass
#
#class SessionValueProvider(grok.Adapter):
#    
#    grok.context(ISiteRoot)
#    grok.provides(INullInterface)  # subclass responsibility 
#
#    def __init__(self, context):
#
#        super(SessionValueProvider, self).__init__(context)
#
#        self.session = \
#            self.context.session_data_manager.getSessionData(create=True)
#
#        self.update()
#
#    def update(self): pass

#@contextmanager
#def elevated_privliges(username=None, role="Site Administrator"):
#
#    if not username:
#        user = api.user.get_current()
#        username = user.getId()
#
#    api.user.grant_roles(username=username, roles=[role, ])
#    yield
#    api.user.revoke_roles(username=username, roles=[role, ])


######################################################################
# hello form
######################################################################

class IRegisterForm(form.Schema):

    nickname = schema.TextLine(
                  title=u"Credit Card Nickname",
                  default=u"My Card",
               )

    number = schema.TextLine(
                  title=u"Credit Card Number",
                  default=u"4242424242424242",
               )

    name_on_card = schema.TextLine(
                  title=u"Name On Card",
               )

    exp_month = schema._field.Choice(
        title=_(u"Expiration Month"),
        default=1,
        vocabulary=months_vocab,
    )

    exp_year = schema._field.Choice(
        title=_(u"Expiration Year"),
        default=17,
        vocabulary=years_vocab,
    )

    cvc = schema.Int(
        title=_(u"CVC Code"),
        required = False
    )

class RegisterForm(form.SchemaForm):

    grok.context(ISiteRoot)
    grok.require('zope2.View')
    grok.name('tch_register')

    schema = IRegisterForm
    ignoreContext = True
    enable_unload_protection = False
    #enableCSRFProtection = True

    label = u"Enter Credit or Debit Card Information"

    def update(self):

        self.session = \
            self.context.session_data_manager.getSessionData(create=True)

        plan_id = self.request.form.get('plan')
        if plan_id:
            self.session.set("tch_register_plan", plan_id)

        return super(RegisterForm, self).update()

    def is_anonymous(self):
        return api.user.is_anonymous()

    def plans(self):
        cat = api.portal.get_tool("portal_catalog")
        return cat(portal_type="totav.stripe.plan")

    def selected_plan(self):
        plan_id = self.request.form.get("plan")
        if plan_id:
            cat = api.portal.get_tool("portal_catalog")
            hits = cat(portal_type="totav.stripe.plan", id=plan_id)
            if hits:
                return hits[0]


    @button.buttonAndHandler(u'Become a Member')
    def handleApply(self, action):

        data, errors = self.extractData()
        add_status_msg = IStatusMessage(self.request).add

        if errors:
            self.status = self.formErrorsMessage
            return

        cat = api.portal.get_tool("portal_catalog")

        user = api.user.get_current()
        username = user.getId()

        self.session = \
            self.context.session_data_manager.getSessionData(create=True)
        plan_id = self.session.get("tch_register_plan")

        plan_brain = cat(portal_type="totav.stripe.plan", id=plan_id)
        if not plan_brain:
            self.status = "could not locate plan."
            return
        plan_brain = plan_brain[0]
            
        domain_brain = cat(portal_type="totav.stripe.domain")
        if not domain_brain:
            self.status = "could not locate stripe domain"
            return 
        domain = domain_brain[0].getObject()

        customer_brain = cat(
            portal_type="totav.stripe.customer",
            id=username,
        )
        if customer_brain:
            customer = customer_brain.getObject()
        else:
            customer = createContentInContainer(
                domain,
                "totav.stripe.customer",
                id=username,
                title=username,
                email=user.getProperty("email"),
                checkConstraints=False,
            )
    
        api.user.grant_roles(
            username=username,
            obj=customer,
            roles=["Reader",]
        )

        add_status_msg("created customer %s" % username)
    
        card = createContentInContainer(
            customer,
            "totav.stripe.card",
            title=data["nickname"],
            number=data["number"],
            name_on_card=data["name_on_card"],
            exp_month=data["exp_month"],
            exp_year=data["exp_year"],
            cvc=data["cvc"],
            checkConstraints=False,
        )
        add_status_msg("added card %s" % data["nickname"])
    
        subscription = createContentInContainer(
                customer,
                "totav.stripe.subscription",
                plan=create_relation(plan_brain.getPath()),
            )
        add_status_msg("subscribed to plan %s" % plan_brain.Title)
    
        api.group.add_user(groupname="members", username=username)
    
        url = api.portal.get().absolute_url()
        self.request.response.redirect(url)


