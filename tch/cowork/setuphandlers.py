#!/usr/bin/python
#
#  Copyright (c) 2014 Red Hat, Inc.  <bowe@redhat.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""See http://docs.plone.org/develop/addons/components/genericsetup.html
"""

__author__  = 'Bowe Strickland <bowe@redhat.com>'
__docformat__ = 'restructuredtext'

def runCustomCode(site):

    """ Run custom add-on product installation code 
        @param site: Plone site
    """

    print "tch.cowork setup"


def setupVarious(context):

    """
    @param context: 
        Products.GenericSetup.context.DirectoryImportContext instance
    """

    if context.readDataFile('tch.cowork.marker.txt') is None:
        return

    portal = context.getSite()

    runCustomCode(portal)

# vi: ts=4 expandtab


