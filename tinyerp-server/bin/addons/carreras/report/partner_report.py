# -*- coding: utf-8 -*-
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
  Fa el llistat de intervinents
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

class partner_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(partner_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_count': self.get_count,
            'format_date': self.format_date,
            'lines': self.lines,
        })
    def preprocess(self, objects, data, ids):
        super(partner_report, self).preprocess(objects, data, ids)
    
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
        
    def get_count(self):
        return self.count
    def lines(self):
        c_obj = self.pool.get('res.partner')
        #c_id = self.datas['form']['company_id']

        s = []
        if self.datas['form']['name']:
            s.append(('name','ilike',"%" + self.datas['form']['name'] + "%" ))
        if self.datas['form']['ref']:
            s.append(('ref','ilike',"%" + self.datas['form']['ref'] + "%" ))
        if self.datas['form']['category_id']:
            s.append(('category_id','=',[self.datas['form']['category_id']]))
        ids = c_obj.search(self.cr,self.uid,s,order='ref')
        self.count = len(ids)
        return c_obj.browse(self.cr,self.uid,ids)

    
report_sxw.report_sxw('report.carreras.partner_report', 'res.partner', 'addons/carreras/report/partner_report.rml',parser=partner_report)

