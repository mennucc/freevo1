#if 0 /*
# -----------------------------------------------------------------------
# audiodiskitem.py - Item for CD Audio Disks
# -----------------------------------------------------------------------
# Freevo - A Home Theater PC framework
# Copyright (C) 2003 Krister Lagerstrom, et al. 
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
# ----------------------------------------------------------------------- */
#endif


import os
import traceback

import util
import config
import menu as menu_module
import copy
import rc
import string
import skin

from item import Item
from audioitem import AudioItem
from playlist import Playlist, RandomPlaylist

import video.interface
import audio.interface
import image.interface
import games.interface

# XML support
from xml.utils import qp_xml

# CDDB Stuff
try:
    import DiscID, CDDB
except:
    pass

            
class AudioDiskItem(Playlist):
    """
    class for handling audio disks
    """
    def __init__(self, disc_id, parent, name = '', devicename = None, display_type = None):

        Item.__init__(self, parent)
        self.type = 'dir'
        self.media = None
        self.disc_id = disc_id
        self.devicename = devicename
        
        # variables only for Playlist
        self.current_item = 0
        self.playlist = []
        self.autoplay = 0

        # variables only for DirItem
        self.dir          = dir
        self.display_type = display_type

        # set directory variables to default
        all_variables = ('DIRECTORY_AUTOPLAY_SINGLE_ITEM',
                         'AUDIO_RANDOM_PLAYLIST')
        for v in all_variables:
            setattr(self, v, eval('config.%s' % v))

        (query_stat, query_info) = CDDB.query(self.disc_id)
    
        if query_stat == 200:
            self.name = query_info['title']
        elif query_stat == 210 or query_stat == 211:
            self.name = query_info[0]['title']
        else:
            self.name = 'Unknown CD'

    def copy(self, obj):
        """
        Special copy value DirItem
        """
        Playlist.copy(self, obj)
        if obj.type == 'dir':
            self.dir          = obj.dir
            self.display_type = obj.display_type
            

    def actions(self):
        """
        return a list of actions for this item
        """
        items = [ ( self.cwd, 'Browse directory' ) ]
        return items
    

    def cwd(self, arg=None, menuw=None):
        """
        make a menu item for each file in the directory
        """
        # Problems with disc id:
        # [2114541066, 10, 150, 17220, 36170, 54412, 68800, 91162, 112110, 129230, 141320, 165100, 2392]
        # Returns multiple results
        print self.disc_id
        (query_stat, query_info) = CDDB.query(self.disc_id)
        
        if query_stat == 200:
            print ("success!\nQuerying CDDB for track info of `%s'... " % query_info['title']),
            (read_stat, read_info) = CDDB.read(query_info['category'], query_info['disc_id'])
            if read_stat != 210:
                print "failure getting track info, status: %i" % read_stat
        elif query_stat == 210 or query_stat == 211:
            print "multiple matches found! Matches are:"
            for i in query_info:
                 print "ID: %s Category: %s Title: %s" % \
                       (i['disc_id'], i['category'], i['title'])
            # We just pick the first one
            query_info = query_info[0]
            (read_stat, read_info) = CDDB.read(query_info['category'], query_info['disc_id'])
            query_stat = 200 # Good data, used below
            if read_stat != 210:
                print "failure getting track info, status: %i" % read_stat
        else:
            print "failure getting disc info, status %i" % query_stat

        play_items = []
        for i in range(0, self.disc_id[1]):
            if query_stat == 200 and read_stat == 210:
                title = read_info['TTITLE' + `i`]
            else:
                title = '(Track %s)' % (i+1)
            item = AudioItem('cdda://%d' % (i+1), self, None, title)
            item.set_info('', self.name, title, i+1, self.disc_id[1], '')
            item.mplayer_options = config.MPLAYER_ARGS_AUDIOCD
            if self.devicename:
                item.mplayer_options += ' -cdrom-device %s' % self.devicename
            play_items.append(item)

        # add all playable items to the playlist of the directory
        # to play one files after the other
        self.playlist = play_items

        # all items together
        items = []

        # random playlist (only active for audio)
        if len(play_items) > 1 and config.AUDIO_RANDOM_PLAYLIST == 1:
            pl = Playlist(play_items, self)
            pl.randomize()
            pl.autoplay = 1
            items += [ pl ]

        items += play_items

        self.play_items = play_items

        title = self.name
        if title[0] == '[' and title[-1] == ']':
            title = self.name[1:-1]

        # autoplay
        if len(items) == 1 and items[0].actions() and \
           self.DIRECTORY_AUTOPLAY_SINGLE_ITEM:
            items[0].actions()[0][0](menuw=menuw)
        else:
            item_menu = menu_module.Menu(title, items, reload_func=self.reload,
                                         item_types = self.display_type)
            if menuw:
                menuw.pushmenu(item_menu)


        return items

    def reload(self):
        """
        called when we return to this menu
        """
        # we changed the menu, don't build a new one
        return None

        
    def update(self, new_files, del_files, all_files):
        """
        update the current item set. Maybe this function can share some code
        with cwd in the future, but it's easier now the way it is
        """



