# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueorles.cat>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import os, time
import netsvc

from report.interface import report_int
import StringIO
class report_raw(report_int):
    pairs= [("ç","c"),("Ç","C"),("ñ","n"),("Ñ","N"),
            ("à","a"),("À","A"),("á","a"),("Á","A"),
            ("ò","o"),("Ò","O"),("ó","o"),("Ó","O"),
            ("è","e"),("È","E"),("é","e"),("É","E"),
            ("í","i"),("Í","I"),("ú","u"),("Ú","U"),
            ("º","o"),("ª","a"),
            ]

    printers={
        'epson': {
            'start': "%c%c" % (chr(27),chr(80)),
            'end': "%c%c" % (chr(27),chr(80)),
            'start_compress': "%c%c%c" % (chr(27),chr(80),chr(15)),
            'end_compress': "%c%c%c" % (chr(18),chr(27),chr(80)),
            'start_expand': "%c%c" % (chr(27),chr(14)),
            'end_expand': chr(20),
            '': "",
        },
        'panasonic': {
            'start': "%c%c%c%c" % (chr(27),chr(58),chr(27),chr(80)),
            'start_compress': chr(15),
            'start_expand': "%c%c%c" % (chr(27),chr(87),chr(49)),
            'end': "",
            'end_compress': "",
            'end_expand': "%c%c%c" % (chr(27),chr(87),chr(48)),
            '': "",
        },
    }
    
    def __init__(self, name, format='txt'):
        report_int.__init__(self, name,)
        self.format = format
        self.printer=self.printers['epson']
    
    def set_printer(self,printer):
        if printer not in self.printers:
            return
        self.printer=self.printers[printer]
    
    def get_chars(self,mark):
        return self.printer[mark]

    def create(self, cr, uid, ids, datas, context=None):
        if not context:
            context={}
        self.raw = StringIO.StringIO()
        self.create_raw(cr, uid, ids, datas, context)
        return (self.raw.getvalue(), self.format)
    
    def convert_raw(self,raw):
        if type(raw) == type(unicode()):
            raw= raw.encode('utf-8')
        for old,new in self.pairs:
            raw= raw.replace(old,new)
        return raw.decode('utf-8').encode('ascii','replace')

    def write_raw(self,raw,start='start',end='end'):
        self.raw.write(self.printer[start] + self.convert_raw(raw)+self.printer[end])

    def create_raw(self, cr, uid, ids, datas, context=None):
        raise "Not Implemented"

