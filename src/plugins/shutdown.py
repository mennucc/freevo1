# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# shutdown plug-in and handling
# -----------------------------------------------------------------------
# $Id$
#
# Author:
# Notes:
# Todo:
#
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2002 Krister Lagerstrom, et al.
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
import logging
logger = logging.getLogger("freevo.plugins.shutdown")


import os
import time
import sys

import config

import skin
from gui import ConfirmBox
from item import Item
from plugin import MainMenuPlugin

from dialog.dialogs import ButtonDialog, WidgetDialog
from dialog.widgets import ButtonModel

class ShutdownModes:
    FREEVO_SHUTDOWN = 'freevo_shutdown'
    SYSTEM_SHUTDOWN = 'system_shutdown'
    SYSTEM_RESTART = 'system_restart'
    shutdown_in_progress = False


def shutdown(menuw=None, mode=None, exit=False):
    """
    Function to shut down freevo or the whole system. This system will be
    shut down when argshutdown is True, restarted when argrestart is true,
    else only Freevo will be stopped.
    """
    logger.debug('shutdown(menuw=%r, mode=%r, exit=%r)', menuw, mode, exit)
    if ShutdownModes.shutdown_in_progress:
        logger.debug('shutdown in progress')
        return
    ShutdownModes.shutdown_in_progress = True
    import osd
    import plugin
    import rc
    import util.mediainfo
    osd = osd.get_singleton()
    util.mediainfo.sync()
    if not osd.active:
        # this function is called from the signal handler, but we are dead
        # already.
        sys.exit(0)

    skin.get_singleton().suspend()
    osd.clearscreen(color=osd.COL_BLACK)
    if mode == ShutdownModes.SYSTEM_SHUTDOWN:
        msg = _('Shutting down...')
    elif mode == ShutdownModes.SYSTEM_RESTART:
        msg = _('Restarting...')
    else:
        msg = _('Exiting...')
    osd.drawstringframed(msg, 0, 0, osd.width, osd.height,
        osd.getfont(config.OSD_DEFAULT_FONTNAME, config.OSD_DEFAULT_FONTSIZE),
        fgcolor=osd.COL_ORANGE, align_h='center', align_v='center')
    osd.update()
    time.sleep(0.5)

    if mode == ShutdownModes.SYSTEM_SHUTDOWN or mode == ShutdownModes.SYSTEM_RESTART:
        # shutdown dual head for mga
        if config.CONF.display == 'mga':
            os.system('%s runapp matroxset -f /dev/fb1 -m 0' % os.environ['FREEVO_SCRIPT'])
            time.sleep(1)
            os.system('%s runapp matroxset -f /dev/fb0 -m 1' % os.environ['FREEVO_SCRIPT'])
            time.sleep(1)

        logger.debug('sys:plugin.shutdown()')
        plugin.shutdown()
        logger.debug('sys:rc.shutdown()')
        rc.shutdown()
        #if config.CONF.display == 'mga':
        logger.debug('sys:osd.shutdown()')
        osd.shutdown()

        if mode == ShutdownModes.SYSTEM_SHUTDOWN:
            logger.debug('os.system(%r)', config.SYS_SHUTDOWN_CMD)
            os.system(config.SYS_SHUTDOWN_CMD)
        elif ShutdownModes.SYSTEM_RESTART:
            logger.debug('os.system(%r)', config.SYS_RESTART_CMD)
            os.system(config.SYS_RESTART_CMD)

        # this closes the log
        logger.debug('sys:config.shutdown()')
        config.shutdown()

        # let freevo be killed by init, looks nicer for mga
        print 'Freevo shutdown'
        while True:
            time.sleep(1)

    #
    # Exit Freevo
    #

    # shutdown any daemon plugins that need it.
    logger.debug('plugin.shutdown()')
    plugin.shutdown()
    # shutdown registered callbacks
    logger.debug('rc.shutdown()')
    rc.shutdown()
    # SDL must be shutdown to restore video modes etc
    logger.log( 9, 'osd.clearscreen(color=osd.COL_BLACK)')
    osd.clearscreen(color=osd.COL_BLACK)
    logger.debug('osd.shutdown()')
    osd.shutdown()
    logger.debug('config.shutdown()')
    config.shutdown()

    if exit:
        # really exit, we are called by the signal handler
        logger.debug('raise SystemExit')
        raise SystemExit

    # We must use spawn instead of os.system here because the python interpreter
    # lock is held by os.system until the command returns, which prevents receiving
    # any signals.
    logger.log( 9, '%s --stop', os.environ['FREEVO_SCRIPT'])
    os.spawnlp(os.P_NOWAIT, os.environ['FREEVO_SCRIPT'], os.environ['FREEVO_SCRIPT'], '--stop')

    # Just wait until we're dead. SDL cannot be polled here anyway.
    while True:
        time.sleep(1)



class ShutdownItem(Item):
    """
    Item for shutdown
    """
    def __init__(self, parent=None):
        logger.log( 9, 'ShutdownItem.__init__(parent=%r)', parent)
        Item.__init__(self, parent, skin_type='shutdown')
        self.menuw = None


    def actions(self):
        """
        return a list of actions for this item
        """
        logger.log( 9, 'ShutdownItem.actions()')
        if config.SYS_SHUTDOWN_CONFIRM:
            if config.SHUTDOWN_NEW_STYLE_DIALOG:
                items = [ (self.new_confirm_exit, _('Shutdown Freevo'))]
            else:
                items = [ (self.confirm_freevo, _('Shutdown Freevo') ),
                          (self.confirm_system, _('Shutdown system') ),
                          (self.confirm_system_restart, _('Restart system') ) ]
        else:
            items = [ (self.shutdown_freevo, _('Shutdown Freevo') ),
                          (self.shutdown_system, _('Shutdown system') ),
                          (self.shutdown_system_restart, _('Restart system') ) ]
        if config.SYS_SHUTDOWN_ENABLE and not config.SHUTDOWN_NEW_STYLE_DIALOG:
            items = [ items[1], items[0], items[2] ]

        return items

    def new_confirm_exit(self, arg=None, menuw=None):
        """
        Pops up a ConfirmBox.
        """
        logger.log( 9, 'confirm_freevo(arg=%r, menuw=%r)', arg, menuw)
        self.menuw = menuw
        dialog = ShutdownDialog()
        dialog.show()

    def confirm_freevo(self, arg=None, menuw=None):
        """
        Pops up a ConfirmBox.
        """
        logger.log( 9, 'confirm_freevo(arg=%r, menuw=%r)', arg, menuw)
        self.menuw = menuw

        what = _('Do you really want to shut down Freevo?')
        dialog = ButtonDialog(((_('Shutdown'), self.shutdown_freevo), (_('Cancel'), None, True)),
                               what, ButtonDialog.QUESTION_TYPE)
        dialog.show()


    def confirm_system(self, arg=None, menuw=None):
        """
        Pops up a ConfirmBox.
        """
        logger.log( 9, 'confirm_system(arg=%r, menuw=%r)', arg, menuw)
        self.menuw = menuw
        what = _('Do you really want to shut down the system?')
        dialog = ButtonDialog(((_('Shutdown'), self.shutdown_system), (_('Cancel'), None, True)),
                               what, ButtonDialog.QUESTION_TYPE)
        dialog.show()


    def confirm_system_restart(self, arg=None, menuw=None):
        """
        Pops up a ConfirmBox.
        """
        logger.log( 9, 'confirm_system_restart(arg=%r, menuw=%r)', arg, menuw)
        self.menuw = menuw
        what = _('Do you really want to restart the system?')
        dialog = ButtonDialog(((_('Restart'), self.shutdown_system_restart), (_('Cancel'), None, True)),
                               what, ButtonDialog.QUESTION_TYPE)
        dialog.show()


    def shutdown_freevo(self, arg=None, menuw=None):
        """
        shutdown freevo, don't shutdown the system
        """
        logger.log( 9, 'shutdown_freevo(arg=%r, menuw=%r)', arg, menuw)
        shutdown(menuw=menuw, mode=ShutdownModes.FREEVO_SHUTDOWN)


    def shutdown_system(self, arg=None, menuw=None):
        """
        shutdown the complete system
        """
        logger.log( 9, 'shutdown_system(arg=%r, menuw=%r)', arg, menuw)
        shutdown(menuw=menuw, mode=ShutdownModes.SYSTEM_SHUTDOWN)


    def shutdown_system_restart(self, arg=None, menuw=None):
        """
        restart the complete system
        """
        logger.log( 9, 'shutdown_system_restart(arg=%r, menuw=%r)', arg, menuw)
        shutdown(menuw=menuw, mode=ShutdownModes.SYSTEM_RESTART)


class ShutdownDialog(WidgetDialog):
    def __init__(self):
        self.exit_model = ButtonModel(_('Exit Freevo'))
        self.exit_model.signals['activated'].connect(self.button_activated)
        self.exit_model.signals['pressed'].connect(self.button_pressed)
        self.reboot_model = ButtonModel(_('Restart System'))
        self.reboot_model.signals['activated'].connect(self.button_activated)
        self.reboot_model.signals['pressed'].connect(self.button_pressed)
        self.shutdown_model = ButtonModel(_('Shutdown System'))
        self.shutdown_model.signals['activated'].connect(self.button_activated)
        self.shutdown_model.signals['pressed'].connect(self.button_pressed)
        self.cancel_model = ButtonModel(_('Cancel'))
        self.cancel_model.signals['activated'].connect(self.button_activated)
        self.cancel_model.signals['pressed'].connect(self.button_pressed)
        buttons = { 'exit'    : self.exit_model,
                    'reboot'  : self.reboot_model,
                    'shutdown': self.shutdown_model,
                    'cancel'  : self.cancel_model}
        super(ShutdownDialog, self).__init__('shutdown', buttons, {})
        if config.SYS_SHUTDOWN_ENABLE:
            self.shutdown_model.set_active(True)
        else:
            self.exit_model.set_active(True)

    def button_activated(self, button):
        self.info['message'] = button.text

    def button_pressed(self, button):
        self.hide()
        if self.exit_model == button:
            shutdown(mode=ShutdownModes.FREEVO_SHUTDOWN)
        elif self.reboot_model == button:
            shutdown(mode=ShutdownModes.SYSTEM_RESTART)
        elif self.shutdown_model == button:
            shutdown(mode=ShutdownModes.SYSTEM_SHUTDOWN)
        


class PluginInterface(MainMenuPlugin):
    """
    Plugin to shutdown Freevo from the main menu
    """

    def items(self, parent):
        logger.log( 9, 'items(parent=%r)', parent)
        return [ ShutdownItem(parent) ]
