# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Interface between mediamenu and external programs
# Copyright (C) 2018 Mennucc
#
# To activate
# plugin.activate('applications', level=45)
#
# Please see the file freevo/Docs/CREDITS for a complete list of authors.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------

# TODO:
#  scan freedesktop menus (using https://github.com/takluyver/pyxdg ?)
#  interface with autoshutdown
#  skins
#  disable autoshutdown while using external app

"""
Interface between media menu and games
"""
import logging
logger = logging.getLogger("freevo.applications")

# freevo modules
import config, menu, rc, plugin, skin, osd, util, childapp, event, sys
from item import Item
from gui.AlertBox import PopupBox

# system modules
import types, time, copy, subprocess, os



def which_p(exe):
    "returns true if exe is an executable, possibly in a  PATH"
    if os.path.isabs(exe):
        return os.access(exe, os.X_OK)
    ## FIXME may not work well in Windows systems
    return any(os.access(os.path.join(p, exe), os.X_OK)  \
               for p in os.environ["PATH"].split(os.pathsep))


class PluginInterface(plugin.MainMenuPlugin):
    """
    Plugin to handle all kinds of applications
    """

    def __init__(self):
        plugin.MainMenuPlugin.__init__(self)

    def config(self):
        return [('APPLICATIONS_LIST',
                 [
                     ("Terminal", "x-terminal-emulator", ()),
                     ("Firefox", "firefox", ()),
                     ("Google Chrome", "google-chrome", ()),
                 ],
                 'list of applications, each a triple (name,executable path,(tuple of extra arguments)) '),
                ('APPLICATIONS_FROM_FREEDESKTOP',False,"import freedesktop menus (not yet implemented)"),
                ('APPLICATIONS_NEED_WINDOW_MANAGER',False,"start window manager, can be False True or 'auto' (default)"),
                ('APPLICATIONS_WINDOW_MANAGER',"x-window-manager","window manager"),
               ]

    def items(self, parent):
        return [ ApplicationsMainMenuItem(parent) ]


class ApplicationsMainMenuItem(Item):
    """
    this is the item for the main menu and creates the list
    of  applications in a submenu.
    """
    def __init__(self, parent):
        Item.__init__(self, parent, skin_type='applications')
        self.name = _('Applications')
        self.window_manager_childapp = None

    def actions(self):
        """
        return a list of actions for this item
        """
        items = [ (self.create_locations_menu, _('Applications')) ]
        return items

    def create_locations_menu(self, arg=None, menuw=None):
        applications_sites = []
        k =0
        for name,path,args in config.APPLICATIONS_LIST:
            if (not path) or (not name): continue
            if not which_p(path):
                logger.warning('skipped '+repr(path)+', not available')
                continue
            myitem = ApplicationsItem(self)
            myitem.name = name
            myitem.path = path
            myitem.args = args
            myitem.location_index = k
            applications_sites.append( myitem)
            k += 1
        if (len(applications_sites) == 0):
            applications_sites += [menu.MenuItem(_('No applications found'),
                                              menuw.back_one_menu, 0)]
        mymenu = menu.Menu(_('Applications'), applications_sites)
        menuw.pushmenu(mymenu)
        menuw.refresh()


class ApplicationsItem(Item):
    """
    Item for the menu for external application
    """
    def __init__(self, parent):
        Item.__init__(self, parent)

    def launch(self,arg,menuw):
        c=config.APPLICATIONS_NEED_WINDOW_MANAGER
        if c == 'auto':
            c = 'XDG_SESSION_DESKTOP' not in os.environ
            if not c:
                logger.debug("Not starting window manager in desktop environment")
        if c and self.parent.window_manager_childapp:
            logger.debug("Not starting window manager, already running")
            c=False
        if c :
            popup=PopupBox(text=(_("Starting window manager")))
            popup.show()
            logger.debug("Starting window manger.")
            self.parent.window_manager_childapp=childapp.ChildApp2(config.APPLICATIONS_WINDOW_MANAGER)
            time.sleep(1) # give it time to settle before starting applications
            popup.destroy()

        popup=PopupBox(text=(_("Starting: ")+repr(self.name)))
        popup.show()
        logger.debug("Starting: "+repr(self.path))
        Application([self.path]+list(self.args))
        time.sleep(2)
        popup.destroy()

    def actions(self):
        """
        return a list of actions for this item
        """
        items = [ (self.launch, self.name) ]
        return items

class Application(childapp.ChildApp2):
    def stop_event(self):
        logger.log(9, 'stop_event()')
        return event.STOP
