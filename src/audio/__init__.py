#if 0 /*
# -----------------------------------------------------------------------
# __init__.py - interface between mediamenu and audio
# -----------------------------------------------------------------------
# $Id$
#
# Notes:
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.9  2003/11/24 19:25:46  dischi
# use new fxditem
#
# Revision 1.8  2003/11/23 17:03:43  dischi
# Removed fxd handling from AudioItem and created a new FXDHandler class
# in __init__.py to let the directory handle the fxd files. The format
# of audio fxd files changed a bit to match the video fxd format. See
# __init__.py for details.
#
# Revision 1.7  2003/09/21 13:15:56  dischi
# handle audio fxd files correctly
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
# ----------------------------------------------------------------------- */
#endif

import config
import util

from audioitem import AudioItem
import fxditem


def cwd(parent, files):
    """
    return a list of items based on the files
    """
    items = []

    for file in util.find_matches(files, config.SUFFIX_AUDIO_FILES):
        a = AudioItem(file, parent)
        if a.valid:
            items.append(a)
            files.remove(file)

    return items



def update(parent, new_files, del_files, new_items, del_items, current_items):
    """
    update a directory. Add items to del_items if they had to be removed based on
    del_files or add them to new_items based on new_files
    """
    for item in current_items:
        for file in util.find_matches(del_files, config.SUFFIX_AUDIO_FILES):
            if item.type == 'audio' and item.filename == file:
                del_items += [ item ]
                del_files.remove(file)

    new_items += cwd(parent, new_files)




class FXDHandler(fxditem.FXDItem):
    """
    parse audio specific stuff from fxd files

    <?xml version="1.0" ?>
    <freevo>
      <audio title="Smoothjazz">
        <cover-img>foo.jpg</cover-img>
        <mplayer_options></mplayer_options>
        <url>http://64.236.34.141:80/stream/1005</url>
    
        <info>
          <genre>JAZZ</genre>
          <description>A nice description</description>
        </info>
    
      </audio>
    </freevo>
    """
    def __init__(self, parser, filename, parent, duplicate_check):
        self.items   = []
        self.parent  = parent
        self.dirname = vfs.dirname(vfs.normalize(filename))
        self.name    = vfs.splitext(vfs.basename(filename))[0]
        parser.set_handler('audio', self.parse)


    def parse(self, fxd, node):
        """
        Callback from the fxd parser. Create an AudioItem
        """
        a = AudioItem('', self.parent, scan=False)
        a.name = fxd.getattr(node, 'title', self.name)
        a.image = fxd.childcontent(node, 'cover-img')
        if a.image:
            a.image = vfs.join(self.dirname, a.image)

        a.mplayer_options = fxd.childcontent(node, 'mplayer_options')
        a.url = fxd.childcontent(node, 'url')

        fxd.parse_info(fxd.get_children(node, 'info', 1), a)
        self.items.append(a)


# register the audio fxd parser as parser to build items
fxditem.register(['audio'], FXDHandler)
