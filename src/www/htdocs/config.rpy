# -*- coding: iso-8859-1 -*-
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

# Displays a webpages to allow the user to edit settings in the local_conf.py  !
#
# config.rpy?expAll=True - Will Expand all the settings.
#
# Required configedit.rpy - To write the settings to the local_conf.py
#
# Edit Date - Oct. 1, 8:30pm  2007

import sys
import os.path
import config
import string
import types
import time
import urllib
from www.web_types import HTMLResource, FreevoResource

def ReadConfig(cfile):
    lconf = cfile
    lconf_hld = open(lconf, 'r')
    fconf = lconf_hld.readlines()
    return fconf


def ParseConfigFile(rconf):
    cnt = 0
    fconfig = []
    while cnt < len(rconf):
        startline = cnt
        ln = rconf[cnt]
        if ln.find('[') <> -1:
            if ln.find(']') <> -1:
                fln = ln
            else:
                fln = ln
                while ln.find(']') == -1:
                    cnt += 1
                    ln = rconf[cnt]
                    ln = ln.strip('#')
                    ln = ln.strip()
                    fln += ln

        elif ln.find('{') <> -1:
            if ln.find('}') <> -1:
                fln = ln
            else:
                fln = ln
                while ln.find('}') == -1:
                    cnt += 1
                    ln = rconf[cnt]
                    ln = ln.strip('#')
                    ln = ln.split('#')[0]
                    ln = ln.strip()
                    fln += ln
                fln = fln.replace('\n', '')
        else:
            fln = ln
        pln = ParseLine(fln)
        if pln['type']:
            pln['startline'] = startline
            pln['endline'] = cnt
            fconfig.append(pln)
        cnt += 1
    fconfig.sort()
    return fconfig


def ParseLine(cline):
    lparsed = {'ctrlname': '',
               'ctrlvalue': '',
               'checked': True,
               'type' : '',
               'comments' : '',
               'level':'',
               'group' :'',
               'startline':'',
               'endline':'',
               'fileline':cline,
               'vartype':''}

    tln = cline.strip()
    tln = tln.replace('\n', '')
    if tln.startswith('#'):
        lparsed['checked'] = False
        tln = tln.lstrip('#')
        tln = tln.lstrip()

    if len(tln) > 1:
        fsplit = tln.split('=')
        if len(fsplit) == 2:
            lparsed['type'] = 'textbox'
            lparsed['ctrlname'] = fsplit[0].strip()
            lparsed['group'] = lparsed['ctrlname'].split('_')[0].capitalize()
            if lparsed['ctrlname'].endswith('_VOLUME'):
                lparsed['group'] = 'Volume'
            if lparsed['ctrlname'] == "PERSONAL_WWW_PAGE":
                lparsed['group'] = "Www"
            if not lparsed['ctrlname'].isupper():
                lparsed['type'] = ''
            if (not config.__dict__.has_key(lparsed['ctrlname'])):
                try:
                    fvvalue = eval('config.' + lparsed['ctrlname'])
                except Exception, e:
                    fvvalue = ''

            ctrlvalue = fsplit[1].split('#')
            if len(ctrlvalue) == 2:
                lparsed['comments'] = ctrlvalue[1]
            lparsed['ctrlvalue'] = ctrlvalue[0].strip()
    lparsed['vartype'] = VarType(lparsed['ctrlvalue'])
    lparsed['ctrlvalue'] = lparsed['ctrlvalue'].replace('"', "'")

    if lparsed['ctrlname'].startswith('"'):
        lparsed['type'] = ""
    return lparsed



def CheckSyntax(fvsetting):
    status = False
    try :
        exec fvsetting
        status = True
    except :
        status = False
    return status


def GetItemsArray(cvalue):
    itemlist = None
    cmd = 'itemlist = ' + cvalue
    if CheckSyntax(cmd):
        exec cmd
    return itemlist


def GetGroupList(cfgvars):
    grps = ['Other']
    agrps = []
    for vrs in cfgvars:
        grp = vrs['group']
        agrps.append(grp)
        if not grp in grps:
            grps.append(grp)

    for vrs in cfgvars:
        ngrp = agrps.count(vrs['group'])
        if ngrp == 1:
            grps.remove(vrs['group'])
            vrs['group'] = 'Other'

    grps.sort()
    return grps


def getCtrlType(cname, cvalue, vtype):
    if vtype == 'boolean':
        return 'boolean'
    if cname == 'TV_CHANNELS':
        return 'tv_channels'
    if FileTypeVarArray(cname):
        return 'fileitemlist'
    if cvalue.startswith('{'):
        return 'itemlist'
    if cvalue.startswith('['):
        return 'itemlist'
    if vtype == 'list':
        return 'itemlist'
    return 'textbox'

def isNumber(s):
    try:
        i = int(s)
        return True
    except ValueError:
        return False


def FileTypeVarArray(cname):
    filevars = ['VIDEO_ITEMS', 'AUDIO_ITEMS', 'IMAGE_ITEMS', 'GAME_ITEMS']

    if cname in filevars:
        return True
    return False


def FileTypeVar(cname):
    vtype = cname.split('_')[-1]
    filetypes = ['PATH', 'DIR', 'FILE', 'DEV', 'DEVICE']
    filevars = ['XMLTV_GRABBER', 'RSS_AUDIO', 'RSS_VIDEO', 'RSS_FEEDS', 'XMLTV_SORT', 'LIRCRC']

    if vtype in filetypes:
        return True
    if cname in filevars:
        return True
    return False


def VarType(cvalue):
    if cvalue.startswith("'") and cvalue.endswith("'"):
        return 'string'
    if isNumber(cvalue):
        return "number"
    if cvalue.startswith('[') and cvalue.endswith(']'):
        return "list"
    if cvalue.startswith('(') and cvalue.endswith(')'):
        return "list"
    if cvalue.startswith('{') and cvalue.endswith('}'):
        return "list"
    if cvalue.startswith('True') or cvalue.startswith('False'):
        return 'boolean'
    return 'Unknow'


def CreateNewLineControl():
    ctrl = '<div align="left">'
    ctrl += '<input  id="newname" name="newname" size="4"> ='
    ctrl += '<input  id="newvalue" name="newvalue" size="40">'
    ctrl += '<input type="button" onclick="AddNewLine()" value="New Setting">'
    ctrl += '<br><br>\n'
    ctrl += '</div>'
    return ctrl


def CreateTV_Channels_ctrl(cname, cvalue, cenabled):
    ctrl = '<span class="Tv_Channels">'
    btnUp =  ''
    btnDown = ''
    btnMove =  '<input type="button" value="%s" '
    btnMove += 'onclick=MoveTVChannel("%s", %i, %i)>'
    vitems = GetItemsArray(cvalue)

    spDisable_open = ''
    spDisable_close = ''
    if not cenabled:
        spDisable_open = '<span class="disablecontrol">'
        spDisable_close = '</span>'

    if vitems:
        txtbox =  '<input type="textbox" style={background:00BFFF} '
        txtbox += 'id="%s_item%i"value = "%s" size=30>'
        for r, e in enumerate(vitems):
            ctrl += '<li>%s' % spDisable_open
            ctrl += btnMove % ('Up', cname, r, -1)
            ctrl +=  txtbox % (cname, r, e)
            if r <>  (len(vitems) -1):
                ctrl += btnMove % ('Down', cname, r, 1)
            ctrl += '%s</li>' % spDisable_close
            btnUp = '<input type="button" value="UP">'
    ctrl += '</span>'
    return ctrl


def CreateFileItemList(cname, cvalue, cenabled):
    ctrl = '<span class="FileList">'
    vitems = GetItemsArray(cvalue)

    spDisable_open = ''
    spDisable_close = ''
    if not cenabled:
        spDisable_open = '<span class="disablecontrol">'
        spDisable_close = '</span>'

    maxcols = 1
    if vitems:
        txtops = ''
        for r, e in enumerate(vitems):

            ctrl += '<li>'
            if type(e) == types.StringType or type(e) ==  types.IntType:
                ctrl +=  '%s<input type="textbox" %s id="%s_label%i"value="%s">%s' % (spDisable_open, txtops, cname, r, e, spDisable_close)
            else:
                txtLabelBox = '%s<input type="textbox" id="%s_label%i" "value="%s">%s' % (spDisable_open, cname, r, e[0], spDisable_close)
                jsCheckFile = 'onchange=CheckValue("%s", "fileitemlist", "%i")' % (cname, r)
                txtFolderBox = '%s<input type="textbox" id="%s_file%i" value="%s" %s>%s' % (spDisable_open, cname, r, e[1], jsCheckFile, spDisable_close)
                ctrl += txtLabelBox + txtFolderBox

                filecheck = ''
                chkClass = ''
                if not os.path.exists(e[1]):
                    filecheck = 'Missing File'
                    chkClass = 'CheckWarning'
                ctrl += '%s<span class="%s" id="%s_check_%i">%s</span>%s' % (spDisable_open, chkClass, cname, r, filecheck, spDisable_close)
            ctrl += '</li>'

        r += 1;
        txtLabelBox = '<input type="textbox" id="%s_label%i" "value="%s">' % (cname, r, "")
        jsCheckFile = 'onchange=CheckValue("%s", "fileitemlist", "%i")' % (cname, r)
        txtFolderBox = '<input type="textbox" id="%s_file%i" value="%s" %s>' % (cname, r, "", jsCheckFile)
        ctrl += '<li>'
        ctrl += txtLabelBox + txtFolderBox
        ctrl += '<span class="" id="%s_check_%i"></span' % (cname, r)
        ctrl += '</li>'

    ctrl += '</span>\n'
    return ctrl


def CreateDictionaryControl(cname, cvalue, cenabled):
    ctrl2type = 'textbox'
    if cname =='WWW_USERS':
        ctrl2type = 'password'
    vitems = GetItemsArray(cvalue)
    ctrl = ""
    spDisable_open = ''
    spDisable_close = ''
    if not cenabled:
        spDisable_open = '<span class="disablecontrol">'
        spDisable_close = '</span>'

    ctrl += '<span class="ItemList">{'
    ctrl += '<ul class="ItemList">'
    if vitems:
        txtbox = '%s<input type="%s" id="%s_item%i%i" size=10 value="%s">%s'
        for r, e in enumerate(vitems):
            pword =  vitems[e]
            ctrl += '<li>' +  txtbox % (spDisable_open, 'textbox', cname, r, 0, e, spDisable_close)
            ctrl +=  txtbox % (spDisable_open,  ctrl2type, cname, r, 0, vitems[e], spDisable_close) + '</li>\n'
        ctrl += '<li>' + txtbox % (spDisable_open, 'textbox', cname, r+1, 0, '""', spDisable_close)
        ctrl += txtbox % (spDisable_open, ctrl2type, cname, r+1, 1, '""', spDisable_close) + '</li>'
        ctrl += '</ul>'
        ctrl += '}</span>'

        if cenabled:
            ctrl += '</span>'

    return ctrl



def CreateListControl(cname, cvalue, cenable):

    spDisable_open = ''
    spDisable_close = ''
    print "List Conftrol %s  " % cname
    print cenable
    if not cenable:
        print 'DISPABLED CONNTROL !!! %' + cname
        spDisable_open = '<span class="disablecontrol">'
        spDisable_close = '</span>'

    print spDisable_open + spDisable_close

    ctrl = '<span class="ItemList">['
    ctrl += '<ul class="ItemList">'
    vitems = GetItemsArray(cvalue)
    maxcols = 1
    if vitems:
        txtops = ''

        txtbox = '%s<input type="textbox" onchange=CheckValue("' + cname + '", "itemlist", 0)  %s id="%s_item%i%i"value="%s">%s'
        for r, e in enumerate(vitems):
            vtype = type(e)
            if vtype == types.StringType or vtype == types.FloatType or vtype == types.IntType:
                ctrl +=  '<li>' +  txtbox % (spDisable_open, txtops, cname, r, 0, e, spDisable_close) + '</li>'
            else:
                ctrl += '<li>'
                cols = 0
                for c, e2 in enumerate(e):
                    cols += 1;
                    ctrl +=  txtbox % (spDisable_open, '', cname, r, c, e2, spDisable_close)

                if cols > maxcols:
                    maxcols = cols

                ctrl += '</li>\n'
        ctrl += '<li>\n'

        r+= 1;
        for c in range(0, maxcols):
            ctrl +=  txtbox % (spDisable_open, '', cname, r, c, '', spDisable_close)
        ctrl += "</li>\n"
        ctrl += '</ul>\n'
        ctrl += "%s]%s</span>\n" % (spDisable_open, spDisable_close)
        return ctrl

    ctrl = CreateTextArea(cname, cvalue)
    return ctrl


def CreateTextArea(cname, cvalue):
    elemsep = ')'
    rows = cvalue.count(elemsep) + 1
    if rows > 5:
        rows = 5
    cvalue = cvalue.replace(elemsep, elemsep + "\n")
    ctrl = ''
    ctrl += '<textarea  id= "%s" rows = %s cols=35 wrap="SOFT" name=%s onchange=CheckValue("%s", "textbox", 0) >%s</textarea>'  % (cname, str(rows), cname, cname, cvalue)
    return ctrl


def CreateListBoxControl(cname, grps, cvalue, opts=""):
    ctrl = '\n<select name="%s" value="%s"  id="%s" %s >' % (cname,  cvalue, cname, opts)
    for grp in grps:
        if grp == cvalue:
            ctrl  += '\n    <option value="%s" selected="yes">%s</option>' % (grp, grp)
        else:
            ctrl  += '\n    <option value="%s">%s</option>' % (grp, grp)
    ctrl += '\n</select>'
    return ctrl


def CreateConfigLine(nctrl, expALL, plugin_group):
    htmlctrl = HTMLResource()

    cname = nctrl['ctrlname']
    cvalue = nctrl['ctrlvalue']
    sline = nctrl['startline']
    eline = nctrl['endline']
    vtype = nctrl['type']

    checked = ''
    displayvars = 'none'
    if nctrl['checked']:
        checked = 'checked'
        displayvars = ''

    if expALL:
        displayvars = ''

    chkline = cname + ' = ' + cvalue
    lcheck = '<span class="checkOK">OK</span>'

    if not CheckSyntax(chkline):
        lcheck = '<span class="checkError">Error</span>'

    else:
        if FileTypeVar(cname):
            filename = cvalue.replace("'", '').strip()
            if not os.path.exists(filename):
                lcheck = '<span class = "CheckWarning">Missing File</span>'

    disable_span_open = ""
    disable_span_close = ""
    if not nctrl['checked']:
        disable_span_open =  '<span class="disablecontrol">'
        disable_span_close =  '</span>'


    htmlctrl.res += '%s<span id="%s_check" class="check">%s</span>%s' % (disable_span_open, cname, lcheck, disable_span_close)
    ctrltype = getCtrlType(cname, cvalue, vtype)
    jsonChange = 'onchange=CheckValue("%s", "%s", 0) '  % (cname, ctrltype)
    chkbox = '%s<input type="checkbox" id = "%s_chk" %s  %s>%s\n' % (disable_span_open, cname, checked, jsonChange, disable_span_close)
    delbtn = '%s<input type="button" class="configbutton" onclick=DeleteLines("%s", %i, %i) value="Delete">%s\n' % (disable_span_open, cname, sline, eline, disable_span_close)
    htmlctrl.res += delbtn
    htmlctrl.res += chkbox

    htmlctrl.res += '<a onclick=ShowList("%s_list")>%s</a>' % (cname, cname)
    htmlctrl.res += '<ul style= display:%s id="%s_list">' % (displayvars, cname)
    htmlctrl.res += '<input type="hidden" id="%s_startline" value="%i">\n' % (cname, sline)
    htmlctrl.res += '<input type="hidden" id="%s_endline" value="%i">\n' % (cname, eline)

    jsSave =  'onclick=SaveValue("%s", "%s")' % (cname, ctrltype)

    btnupdate = '<input type="button" style="display:none;" id="%s_btn_update" class="button.config" value="Update" %s >\n' % (cname, jsSave)
    htmlctrl.res += btnupdate

    if nctrl['type'] == 'textbox':
        inputbox = CreateTextBox(cname, cvalue, nctrl['vartype'], plugin_group, nctrl['checked'])
        htmlctrl.res += "<li>%s %s %s</li>"  % (disable_span_open, inputbox, disable_span_close)

    htmlctrl.res += '</ul>'
    return htmlctrl.res


def CreateTextBox(cname, cvalue, vtype, plugin_group, cenabled):
    cvalue = cvalue.replace(' ', '')
    cvalue = cvalue.strip()
    bllist = ['True', 'False']

    ctrl = ""
    if vtype == 'boolean':
        ctrl = CreateListBoxControl(cname, bllist, cvalue, 'onchange=CheckValue("%s", "textbox", 0)')
        return ctrl

    if cname == 'TV_CHANNELS':
        ctrl = CreateTV_Channels_ctrl(cname, cvalue, cenabled)
        return ctrl

    if plugin_group == "Enable":
        if cvalue == 1:
            cvalue = "True"
        else :
            cvalue = "False"
        ctrl = CreateListBoxControl(cname, bllist, cvalue, 'onchange=CheckValue("%s", "textbox", 0)')
        return ctrl

    if FileTypeVarArray(cname):
        ctrl = CreateFileItemList(cname, cvalue, cenabled)
        return ctrl

    if cvalue.startswith('{'):
        ctrl = CreateDictionaryControl(cname, cvalue, cenabled)
        return ctrl

    if cvalue.startswith('['):
        ctrl = CreateListControl(cname, cvalue, cenabled)
        return ctrl

    if vtype == 'list':
        ctrl = CreateListControl(cname, cvalue, cenabled)
        return ctrl

    if vtype == 'number':
        ctrl = CreateNumberControl(cname, cvalue)
        return ctrl

    jscheck = '"=makeCheckSyntaxRequest(%s);"' % cname
    ctrl = '<span class="%s">' % jscheck
    ctrl += '<input type=textbox id="%s" name="%s" value="%s" onchange=CheckValue("%s", "textbox", 0) size="50" >' \
        % (cname, cname, cvalue, cname)
    ctrl += '</span>'
    return ctrl


def CreateNumberControl(cname, cvalue):
    tbClass = 'VarInputInt'
    ctrl = '<span class="%s">' % tbClass
    ctrl += '<input type=textbox  id="%s" name="%s" value="%s" onchange=CheckValue("%s", "textbox", 0) size="50" >' \
        % (cname, cname, cvalue, cname)
    ctrl += '</span>'
    return ctrl


def DisplayGroups(fconfig, expALL):
    fv = HTMLResource()
    groups = GetGroupList(fconfig)

    displayStyle = 'none'
    if expALL:
        displayStyle = ''

    fv.res +=  '<ul class="GroupHeader">'

    for grp in groups:
        dopts = 'class="GroupHeader"'
        aopts = ''

        fv.res += '<li>'
        fv.res += '<a %s onclick=ShowList("%s")>%s</a>\n'  % (aopts, grp, grp)
        fv.res += '   <ul id="%s" style= display:%s>\n' % (grp, displayStyle)
        for cctrl in fconfig:
            if cctrl['group'] == grp:
                lctrl = CreateConfigLine(cctrl, expALL, grp)
                fv.res += '        <li>' + lctrl + '</li>'
        fv.res += '    </ul>\n'
        fv.res += '</li>'
     #   </div>\n'
    fv.res += '</ul>'

    return fv.res


class ConfigResource(FreevoResource):

    def _render(self, request):
        fv = HTMLResource()
        form = request.args
        fv.printHeader(_('Config'), 'styles/main.css', 'scripts/config.js', selected=_('Config'))

        configfile = fv.formValue(form, 'configfile')
        if configfile:
            if not os.path.exists(configfile):
                configfile = None

        if not configfile:
            if (not config.__dict__.has_key('CONFIG_EDIT_FILE')):
                fv.printMessages(['Unable to find local_conf.py setting CONFIG_EDIT_FILE'])
                return String (fv.res)
            else:
                configfile = config.CONFIG_EDIT_FILE

        if not os.path.exists(configfile):
            fv.printMessages(['Unable to find file - ' + configfile])
            return String (fv.res)

        rconf = ReadConfig(configfile)
        fconfig = ParseConfigFile(rconf)

        expAll = fv.formValue(form, 'expAll')
        expandAll = False
        if expAll:
            expandAll = True

        fv.res += '<link rel="stylesheet" href="styles/config.css" type="text/css" />\n'
        fv.res += '<input type="hidden" id="configfile" value="%s"\n>' % configfile
        fv.res += '<div class="VarGroups">\n'
        fv.res += '\n<form id="config" class="searchform" action="config.rpy" method="get">\n'
        fv.res += DisplayGroups(str(fconfig), expandAll)
        fv.res + '</div>\n'
        fv.res += '\n</form><br>\n'
        return String(fv.res)

resource = ConfigResource()