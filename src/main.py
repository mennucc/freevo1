# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# main.py - This is the Freevo main application code
# -----------------------------------------------------------------------
# $Id$
#
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


# Must do this here to make sure no os.system() calls generated by module init
# code gets LD_PRELOADed
import os
os.environ['LD_PRELOAD'] = ''

import sys, time
import traceback
import signal


# i18n support

# First load the xml module. It's not needed here but it will mess
# up with the domain we set (set it from freevo 4Suite). By loading it
# first, Freevo will override the 4Suite setting to freevo

try:
    from xml.utils import qp_xml
    from xml.dom import minidom

    # now load other modules to check if all requirements are installed
    import pygame
    import twisted
    import Numeric

    import config
    import kaa.metadata as mmpython
    import kaa.imlib2 as Image


except ImportError, i:
    print 'Can\'t find all Python dependencies:'
    print i
    if str(i)[-7:] == 'Numeric':
        print 'You need to recompile pygame after installing Numeric!'
    print
    print 'Not all requirements of Freevo are installed on your system.'
    print 'Please check the INSTALL file for more information.'
    print
    sys.exit(0)


# check if kaa.metadata is up to date to avoid bug reports
# for already fixed bugs
try:
    v = 'unknown'
    import kaa.metadata.version
    if kaa.metadata.version.VERSION < 0.6:
        v = kaa.metadata.version.VERSION
        raise ImportError
except ImportError:
    print 'Error: Installed kaa.metadata version (%s) is too old.' % v
    print 'Please update kaa.metadata to version 0.6 or higher or get it with subversion'
    print 'svn export svn://svn.freevo.org/kaa/trunk/metadata kaa/metadata'
    print
    sys.exit(0)

# check if kaa.imlib2 is up to date to avoid bug reports
# for already fixed bugs
try:
    v = 'unknown'
    import kaa.imlib2.version
    if kaa.imlib2.version.VERSION < 0.1:
        v = kaa.metadata.version.VERSION
        raise ImportError
except ImportError:
    print 'Error: Installed kaa.imlib2 version (%s) is too old.' % v
    print 'Please update kaa.imlib2 to version 0.1 or higher or get it with subversion'
    print 'svn export svn://svn.freevo.org/kaa/trunk/imlib2 kaa/imlib2'
    print
    sys.exit(0)

import util    # Various utilities
import osd     # The OSD class, used to communicate with the OSD daemon
import menu    # The menu widget class
import skin    # The skin class
import rc      # The RemoteControl class.

from item import Item
from event import *
from plugins.shutdown import shutdown


# Create the OSD object
osd = osd.get_singleton()


class SkinSelectItem(Item):
    """
    Item for the skin selector
    """
    def __init__(self, parent, name, image, skin):
        Item.__init__(self, parent)
        self.name  = name
        self.image = image
        self.skin  = skin

    def actions(self):
        return [ ( self.select, '' ) ]

    def select(self, arg=None, menuw=None):
        """
        Load the new skin and rebuild the main menu
        """
        import plugin
        skin.set_base_fxd(self.skin)
        pos = menuw.menustack[0].choices.index(menuw.menustack[0].selected)

        parent = menuw.menustack[0].choices[0].parent
        menuw.menustack[0].choices = []
        for p in plugin.get('mainmenu'):
            menuw.menustack[0].choices += p.items(parent)

        for i in menuw.menustack[0].choices:
            i.is_mainmenu_item = True

        menuw.menustack[0].selected = menuw.menustack[0].choices[pos]
        menuw.back_one_menu()



class MainMenu(Item):
    """
    this class handles the main menu
    """
    def getcmd(self):
        """
        Setup the main menu and handle events (remote control, etc)
        """
        import plugin
        menuw = menu.MenuWidget()
        items = []
        for p in plugin.get('mainmenu'):
            items += p.items(self)

        for i in items:
            i.is_mainmenu_item = True

        mainmenu = menu.Menu(_('Freevo Main Menu'), items, item_types='main', umount_all = 1)
        menuw.pushmenu(mainmenu)
        osd.add_app(menuw)


    def eventhandler(self, event=None, menuw=None, arg=None):
        """
        Automatically perform actions depending on the event, e.g. play DVD
        """
        # pressing DISPLAY on the main menu will open a skin selector
        # (only for the new skin code)
        if event == MENU_CHANGE_STYLE:
            items = []
            for name, image, skinfile in skin.get_skins():
                items += [ SkinSelectItem(self, name, image, skinfile) ]

            menuw.pushmenu(menu.Menu(_('Skin Selector'), items))
            return True

        # give the event to the next eventhandler in the list
        return Item.eventhandler(self, event, menuw)



class Splashscreen(skin.Area):
    """
    A simple splash screen for osd startup
    """
    def __init__(self, text):
        skin.Area.__init__(self, 'content')

        self.pos          = 0
        self.bar_border   = skin.Rectange(bgcolor=0xff000000L, size=2)
        self.bar_position = skin.Rectange(bgcolor=0xa0000000L)
        self.text         = text


    def update_content(self):
        """
        there is no content in this area
        """
        layout    = self.layout
        area      = self.area_val
        content   = self.calc_geometry(layout.content, copy_object=True)

        self.write_text(self.text, content.font, content, height=-1, align_h='center')

        pos = 0
        x0, x1 = content.x, content.x + content.width
        y = content.y + content.font.font.height + content.spacing
        if self.pos:
            pos = round(float((x1 - x0 - 4)) / (float(100) / self.pos))
        self.drawroundbox(x0, y, x1-x0, 20, self.bar_border)
        self.drawroundbox(x0+2, y+2, pos, 16, self.bar_position)


    def progress(self, pos):
        """
        set the progress position and refresh the screen
        """
        self.pos = pos
        skin.draw('splashscreen', None)



class MainTread:
    """
    The main thread or loop of freevo
    """
    def __init__(self):
        """
        get the list of plugins wanting events
        """
        self.eventhandler_plugins  = []
        self.eventlistener_plugins = []

        for p in plugin.get('daemon_eventhandler'):
            if hasattr(p, 'event_listener') and p.event_listener:
                self.eventlistener_plugins.append(p)
            else:
                self.eventhandler_plugins.append(p)


    def eventhandler(self, event):
        """
        event handling function for the main loop
        """
        if event == OS_EVENT_POPEN2:
            _debug_('popen2 %s' % event.arg[1])
            event.arg[0].child = util.popen3.Popen3(event.arg[1])
            return

        _debug_('handling event %s' % str(event), 2)

        for p in self.eventlistener_plugins:
            p.eventhandler(event=event)

        if event == FUNCTION_CALL:
            event.arg()

        elif event.handler:
            event.handler(event=event)

        # Send events to either the current app or the menu handler
        elif rc.app():
            if not rc.app()(event):
                for p in self.eventhandler_plugins:
                    if p.eventhandler(event=event):
                        break
                else:
                    _debug_('no eventhandler for event %s' % event, 2)

        else:
            app = osd.focused_app()
            if app:
                try:
                    if config.DEBUG_TIME:
                        t1 = time.clock()
                    app.eventhandler(event)
                    if config.DEBUG_TIME:
                        print time.clock() - t1

                except SystemExit:
                    raise SystemExit

                except:
                    if config.FREEVO_EVENTHANDLER_SANDBOX:
                        traceback.print_exc()
                        from gui import ConfirmBox
                        pop = ConfirmBox(text=_('Event \'%s\' crashed\n\nPlease take a ' \
                                                'look at the logfile and report the bug to ' \
                                                'the Freevo mailing list. The state of '\
                                                'Freevo may be corrupt now and this error '\
                                                'could cause more errors until you restart '\
                                                'Freevo.\n\nLogfile: %s\n\n') % \
                                         (event, sys.stdout.logfile),
                                         width=osd.width-(config.OSD_OVERSCAN_LEFT+config.OSD_OVERSCAN_RIGHT)-50,
                                         handler=shutdown,
                                         handler_message = _('shutting down...'))
                        pop.b0.set_text(_('Shutdown'))
                        pop.b0.toggle_selected()
                        pop.b1.set_text(_('Continue'))
                        pop.b1.toggle_selected()
                        pop.show()
                    else:
                        raise
            else:
                _debug_('no target for events given')


    def run(self):
        """
        the real main loop
        """
        while 1:
            self.eventhandler(rc.get_event(True))



def signal_handler(sig, frame):
    """
    the signal handler to shut down freevo
    """
    if sig in (signal.SIGTERM, signal.SIGINT):
        shutdown(exit=True)


def tracefunc(frame, event, arg, _indent=[0]):
    """
    function to trace everything inside freevo for debugging
    """
    if event == 'call':
        filename = frame.f_code.co_filename
        funcname = frame.f_code.co_name
        lineno = frame.f_code.co_firstlineno
        if 'self' in frame.f_locals:
            try:
                classinst = frame.f_locals['self']
                classname = repr(classinst).split()[0].split('(')[0][1:]
                funcname = '%s.%s' % (classname, funcname)
            except:
                pass
        here = '%s:%s:%s()' % (filename, lineno, funcname)
        _indent[0] += 1
        tracefd.write('%4s %s%s\n' % (_indent[0], ' ' * _indent[0], here))
        tracefd.flush()
    elif event == 'return':
        _indent[0] -= 1

    return tracefunc



#
# Freevo main function
#

# parse arguments
if len(sys.argv) >= 2:

    # force fullscreen mode
    # deactivate screen blanking and set osd to fullscreen
    if sys.argv[1] == '-force-fs':
        os.system('xset -dpms s off')
        config.START_FULLSCREEN_X = 1

    # activate a trace function
    if sys.argv[1] == '-trace':
        tracefd = open(os.path.join(config.FREEVO_LOGDIR, 'trace.txt'), 'w')
        sys.settrace(tracefunc)
        config.DEBUG = 2

    # create api doc for Freevo and move it to Docs/api
    if sys.argv[1] == '-doc':
        import pydoc
        import re
        for file in util.match_files_recursively('src/', ['py' ]):
            # doesn't work for everything :-(
            if file not in ( 'src/tv/record_server.py', ) and \
                   file.find('src/www') == -1 and \
                   file.find('src/helpers') == -1:
                file = re.sub('/', '.', file)
                try:
                    pydoc.writedoc(file[4:-3])
                except:
                    pass
        try:
            os.mkdir('Docs/api')
        except:
            pass
        for file in util.match_files('.', ['html', ]):
            print 'moving %s' % file
            os.rename(file, 'Docs/api/%s' % file)
        print
        print 'wrote api doc to \'Docs/api\''
        shutdown(exit=True)


try:
    # signal handler
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # load the fxditem to make sure it's the first in the
    # mimetypes list
    import fxditem

    # load all plugins
    import plugin

    # prepare the skin
    skin.prepare()

    try:
        try:
            import freevo.version as version
            import freevo.revision as revision
        except ImportError:
            import version
            import revision
        v = '%s' % version.__version__
        v = v.replace('-svn', ' r%s' % revision.__revision__)
    except ImportError:
        pass
    # Fire up splashscreen and load the plugins
    splash = Splashscreen(_('Starting Freevo-%s, please wait ...') % v)
    skin.register('splashscreen', ('screen', splash))
    plugin.init(splash.progress)
    skin.delete('splashscreen')

    # Fire up splashscreen and load the cache
    if config.MEDIAINFO_USE_MEMORY == 2:
        import util.mediainfo

        splash = Splashscreen(_('Reading cache, please wait ...'))
        skin.register('splashscreen', ('screen', splash))

        cachefiles = []
        for type in ('video', 'audio', 'image', 'games'):
            if plugin.is_active(type):
                n = 'config.%s_ITEMS' % type.upper()
                x = eval(n)
                for item in x:
                    if os.path.isdir(item[1]):
                        cachefiles += [ item[1] ] + util.get_subdirs_recursively(item[1])


        cachefiles = util.unique(cachefiles)

        for f in cachefiles:
            splash.progress(int((float((cachefiles.index(f)+1)) / len(cachefiles)) * 100))
            util.mediainfo.load_cache(f)
        skin.delete('splashscreen')

    # prepare again, now that all plugins are loaded
    skin.prepare()

    # start menu
    MainMenu().getcmd()

    # Kick off the main menu loop
    _debug_('Main loop starting...',2)
    MainTread().run()


except KeyboardInterrupt:
    print 'Shutdown by keyboard interrupt'
    # Shutdown the application
    shutdown()

except SystemExit:
    pass

except Exception, e:
    _debug_('Crash!: %s' % (e), config.DCRITICAL)
    try:
        tb = sys.exc_info()[2]
        fname, lineno, funcname, text = traceback.extract_tb(tb)[-1]

        if config.FREEVO_EVENTHANDLER_SANDBOX:
            secs = 5
        else:
            secs = 1
        for i in range(secs, 0, -1):
            osd.clearscreen(color=osd.COL_BLACK)
            osd.drawstring(_('Freevo crashed!'), 70, 70, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Filename: %s') % fname, 70, 130, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Lineno: %s') % lineno, 70, 160, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Function: %s') % funcname, 70, 190, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Text: %s') % text, 70, 220, fgcolor=osd.COL_ORANGE)
            osd.drawstring(str(sys.exc_info()[1]), 70, 280, fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Please see the logfiles for more info'), 70, 350,
                           fgcolor=osd.COL_ORANGE)
            osd.drawstring(_('Exit in %s seconds') % i, 70, 410, fgcolor=osd.COL_ORANGE)
            osd.update()
            time.sleep(1)

    except:
        pass
    traceback.print_exc()

    # Shutdown the application, but not the system even if that is
    # enabled
    shutdown()
