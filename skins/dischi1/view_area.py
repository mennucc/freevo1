#if 0
# -----------------------------------------------------------------------
# view_area.py - A view area for the Freevo skin
# -----------------------------------------------------------------------
# $Id$
#
# Notes: WIP
# Todo:        
#
# -----------------------------------------------------------------------
# $Log$
# Revision 1.1  2003/02/27 22:39:50  dischi
# The view area is working, still no extended menu/info area. The
# blue_round1 skin looks like with the old skin, blue_round2 is the
# beginning of recreating aubin_round1. tv and music player aren't
# implemented yet.
#
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
#endif

from area import Skin_Area
from skin_utils import *

TRUE  = 1
FALSE = 0

class View_Area(Skin_Area):
    """
    this call defines the view area
    """

    def __init__(self, parent, screen):
        Skin_Area.__init__(self, 'view', screen)
        self.image = None


    def update_content_needed(self, settings, menuw):
        """
        check if the content needs an update
        """
        menu = menuw.menustack[-1]
        image = None

        if hasattr(menu.selected, 'image') and menu.selected.image:
            image = menu.selected.image

        return image != self.image
    

    def update_content(self, settings, menuw):
        """
        update the view area
        """
        menu = menuw.menustack[-1]
        item = menu.selected
        
        layout    = self.layout
        area      = self.area_val
        content   = self.calc_geometry(layout.content, copy_object=TRUE)

        if content.types.has_key(menu.selected.type):
            val = content.types[menu.selected.type]
        else:
            val = content.types['default']

        if hasattr(menu.selected, 'image') and item.image:
            self.image = item.image
        else:
            self.image = None
            return

        x0 = 0
        y0 = 0

        width  = content.width - 2*content.spacing
        height = content.height - 2*content.spacing

        
        if val.rectangle:
            x, y, r = self.get_item_rectangle(val.rectangle, width, height)

            if r.x < 0:
                x0 -= r.x
                r.x = 0
            
            if r.y < 0:
                y0 -= r.y
                r.y = 0
            
            if r.x + r.width > x0 + width:
                r.width, width = width, width - (r.width - width)

            if r.y + r.height > y0 + height:
                r.height, height = height, height - (r.height - height)

        addx = content.x + content.spacing
        addy = content.y + content.spacing

        image = format_image(item, width, height)
        i_w, i_h = image.get_size()

        if content.align == 'center' and i_w < width:
            addx += (width - i_w) / 2

        if content.align == 'right' and i_w < width:
            addx += width - i_w
            
        if content.valign == 'center' and i_h < height:
            addy += (height - i_h) / 2

        if content.valign == 'bottom' and i_h < height:
            addy += height - i_h

        x0 += addx
        y0 += addy

        self.draw_image(image, (x0, y0))

        if val.rectangle:
            r.width -= width - i_w
            r.height -= height - i_h
            self.drawroundbox(r.x + addx, r.y + addy, r.width, r.height, r)
