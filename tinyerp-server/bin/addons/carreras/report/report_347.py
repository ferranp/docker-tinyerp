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
  Fa el llistat del declaracio de 347
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

class report_347(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_347, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_count': self.get_count,
            'get_tot_untaxed': self.get_tot_untaxed,
            'get_tot_tax': self.get_tot_tax,
            'get_tot_total': self.get_tot_total,
            'get_tot_base': self.get_tot_base,
            'format_date': self.format_date,
            'lines': self.lines,
            'count': self.count,
        })
        self.c = 0
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        super(report_347, self).preprocess(objects, data, ids)
    
    def count(self):
        self.c += 1
        return self.c
    def get_count(self):
        return self.count
    def get_tot_untaxed(self):
        return self.numf(self.untaxed)
    def get_tot_tax(self):
        return self.numf(self.tax)
    def get_tot_total(self):
        return self.numf(self.total)
    def get_tot_base(self):
        return self.numf(self.base)
    
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
        
    def lines(self):
        i_obj = self.pool.get('account.invoice')
        
        c_id = self.datas['form']['company_id']
        start = self.datas['form']['date_start']
        end = self.datas['form']['date_end']
        type = self.datas['form']['type']

        s = [('company_id','=',c_id)]
        s.append(('date_invoice','>=',start))
        s.append(('date_invoice','<=',end))
        s.append(('state','in',('open','paid')))
        s.append(('type','=',type))
        ids = i_obj.search(self.cr,self.uid,s,order='number')
        
        partners = {}

        self.base = 0.0
        self.tax = 0.0
        self.untaxed = 0.0
        self.total = 0.0

        for inv in i_obj.browse(self.cr,self.uid,ids):

            if inv.partner_id.ref not in partners:
                partners[inv.partner_id.ref] = {}
                p = partners[inv.partner_id.ref]
                p['partner'] = inv.partner_id
                p['base'] = 0.0
                p['untaxed'] = 0.0
                p['tax'] = 0.0
                p['total'] = 0.0
                res = self.pool.get('res.partner').address_get(self.cr, self.uid,[inv.partner_id.id], ['invoice'])
                invoice_addr_id = res['invoice']
                if invoice_addr_id:
                    p['zip'] = self.pool.get('res.partner.address').browse(self.cr,self.uid,invoice_addr_id).zip
                else:
                    p['zip'] = ""
            
            p = partners[inv.partner_id.ref]
            p['total'] += inv.amount_total
            p['untaxed'] += inv.amount_untaxed
            
            for tax in inv.tax_line:
                p['base'] += tax.base
                p['tax'] += tax.amount

        order = self.datas['form']['order']
        codes = []
        
        limit=self.datas['form']['limit']
        for k,v in partners.items():
            if limit > 0 and partners[k]['total'] < limit:
                continue
            
            if order == 'ref':
                codes.append( (v['partner'].ref , k) )
            elif order == 'name':
                codes.append( (v['partner'].name , k) )
            elif order == 'amount':
                codes.append( (v['total'] , k) )
            else:
                codes.append( (v['partner'].ref , k) )
            
            self.base += partners[k]['base']
            self.untaxed += partners[k]['untaxed']
            self.tax += partners[k]['tax']
            self.total += partners[k]['total']

            partners[k]['base'] = self.numf(partners[k]['base'])
            partners[k]['untaxed'] = self.numf(partners[k]['untaxed'])
            partners[k]['tax'] = self.numf(partners[k]['tax'])
            partners[k]['total'] = self.numf(partners[k]['total'])
        
        codes.sort()
        if order == 'amount':
            codes.reverse()    
        
        self.count=len(codes)
        res = [partners[k[1]] for k in codes]
        return res

report_sxw.report_sxw('report.account.report_347', 'account.invoice', 'addons/carreras/report/report_347.rml',parser=report_347)

