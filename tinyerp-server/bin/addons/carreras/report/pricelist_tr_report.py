##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
"""
  Llistat de Tarifes de Tractaments
"""
import pooler
import time
import locale
locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

locale.localeconv = localeconv

from report import report_sxw

class pricelist_tr_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(pricelist_tr_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'format_date': self.format_date,
            'lines':self.lines,
        })
    def preprocess(self, objects, data, ids):
        super(pricelist_tr_report, self).preprocess(objects, data, ids)
    
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
        
    def lines(self,objects):
        lines = []
        for o in objects:
            for l in o.line_ids:
                lin = {
                    'name':o.name,
                    'product':o.product_id.name,
                    'depth':o.depth,
                    'units':o.product_uom.name,
                    'minimum':o.apply_minimum and self.numf(o.minimum) or '---',
                    'quantity':l.quantity,
                    'price':self.numf(l.price),
                }
                lines.append(lin)    
            lin = {
                'name':'',
                'product':'',
                'depth':'',
                'units':'',
                'minimum':'',
                'quantity':'',
                'price':'',
            }
            lines.append(lin)    
        return lines
 
report_sxw.report_sxw('report.carreras.pricelist_tr_report', 'pricelist.kilo', 'addons/carreras/report/pricelist_tr_report.rml',parser=pricelist_tr_report)
                       
