#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------
# Input helper to process LIRC and other input devices.
# -----------------------------------------------------------------------
# $Id: imdb.py 11565 2009-05-25 18:36:59Z duncan $
#
# Notes:
#
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

import fcntl
import os
import sys
import struct
import time

import kaa

import config

wire_format = struct.Struct('d30p')

# Put stdout in non-blocking mode
flag = fcntl.fcntl(sys.__stderr__, fcntl.F_GETFL)
fcntl.fcntl(sys.__stderr__, fcntl.F_SETFL, flag | os.O_NDELAY)

def post_key(key):
    """
    Send key to main process.
    """
    sys.__stderr__.write(wire_format.pack(time.time(), key))
    sys.__stderr__.flush()


class Lirc:
    """
    Class to handle lirc events
    """
    def __init__(self):
        _debug_('Lirc.__init__()', 2)
        try:
            global pylirc
            import pylirc
        except ImportError:
            _debug_('PyLirc not found, lirc remote control disabled!', DWARNING)
            raise

        try:
            if os.path.isfile(config.LIRCRC):
                self.resume()
            else:
                raise IOError
        except RuntimeError:
            _debug_('Could not initialize PyLirc!', DWARNING)
            raise
        except IOError:
            _debug_('%r not found!' % (config.LIRCRC), DWARNING)
            raise

        global PYLIRC
        PYLIRC = True
        self.last_code = [None, 0, False]


    def __process_key(self, code):
        now = time.time()

        if self.last_code[0] == code:
            diff = now - self.last_code[1]

            if diff > config.LIRC_KEY_REPEAT[0] and self.last_code[2]:
                post_key(code)
                self.last_code = [code, now, False]
                return

            if diff > config.LIRC_KEY_REPEAT[1] and not self.last_code[2]:
                post_key(code)
                self.last_code = [code, now, False]
                return
        else:
            post_key(code)
            self.last_code = [code, now, True]


    def resume(self):
        """
        (re-)initialize pylirc, e.g. after calling close()
        """
        _debug_('Lirc.resume()', 2)
        fd = pylirc.init('freevo', config.LIRCRC)

        self.dispatcher = kaa.IOMonitor(self._handle_lirc_input)
        self.dispatcher.register(fd)


    def _handle_lirc_input(self):
        codes = pylirc.nextcode()
        if codes:
            for code in codes:
                self.__process_key(code)


    def suspend(self):
        """
        cleanup pylirc, close devices
        """
        _debug_('Lirc.suspend()', 2)
        self.dispatcher.unregister()
        pylirc.exit()


class Evdev:
    """
    Class to handle evdev events
    """
    def __init__(self):
        """
        init all specified devices
        """
        _debug_('Evdev.__init__()', 2)
        import evdev
        self._devs = []

        for dev in config.EVENT_DEVS:
            e = None

            if os.path.exists(dev):
                try:
                    e = evdev.evdev(dev)
                except:
                    print "Problem opening event device '%s'" % dev
            else:
                names = []
                name = dev
                for dev in os.listdir('/dev/input'):
                    if not dev.startswith('event'):
                        continue

                    try:
                        dev = '/dev/input/' + dev
                        e = evdev.evdev(dev)
                    except:
                        continue

                    names.append(e.get_name())
                    if e.get_name() == name:
                        break
                else:
                    e = None
                    _debug_("Could not find device named '%s', possible are:\n  - %s" % \
                        (name, '\n  - '.join(names)), DWARNING)

            if e is not None:
                _debug_("Added input device '%s': %s" % (dev, e.get_name()), DINFO)
                m = kaa.IOMonitor(self.__handle_event, e)
                m.register(e._fd)
                self._devs.append(m)

        self._movements = {}


    def __handle_event(self, dev):
        """
        Handle evdev events
        """
        event = dev.read()
        if event is None:
            return

        time, type, code, value = event

        if type == 'EV_KEY':
            self._movements = {}

            if config.EVENTMAP.has_key(code):
                # 0 = release, 1 = press, 2 = repeat
                if value > 0:
                    post_key(config.EVENTMAP[code])

        elif type == 'EV_REL':
            if config.EVENTMAP.has_key(code):
                if self._movements.has_key(code):
                    self._movements[code] += value
                else:
                    self._movements[code] = value

                if self._movements[code] < -10:
                    self._movements = {}
                    post_key(config.EVENTMAP[code][0])
                elif self._movements[code] > 10:
                    self._movements = {}
                    post_key(config.EVENTMAP[code][1])


def handle_stdin():
    """
    Handle commands sent via stdin
    """
    cmd = sys.stdin.readline().strip()
    if cmd == 'suspend':
        for i in inputs:
            if hasattr(i, 'suspend'):
                i.suspend()

    elif cmd == 'resume':
        for i in inputs:
            if hasattr(i, 'resume'):
                i.resume()

    elif cmd == 'quit':
        sys.exit(0)


inputs = [Lirc()]

if config.EVENT_DEVS:
    try:
        inputs.append(Evdev())
    except:
        pass

stdin_dispatcher = kaa.IOMonitor(handle_stdin)
stdin_dispatcher.register(sys.stdin)

kaa.main.run()