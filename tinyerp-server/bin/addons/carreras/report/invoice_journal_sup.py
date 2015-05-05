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
  Fa el llistat del diari de compres
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

class invoice_journal_sup(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(invoice_journal_sup, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'per_iva': self.per_iva,
            'get_count': self.get_count,
            'get_tot_untaxed': self.get_tot_untaxed,
            'get_tot_tax': self.get_tot_tax,
            'get_tot_total': self.get_tot_total,
            'get_tot_base': self.get_tot_base,
            'get_base': self.get_base,
            'format_date': self.format_date,
            'lines': self.lines,
            'tax_lines': self.tax_lines,
        })
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        super(invoice_journal_sup, self).preprocess(objects, data, ids)
    
    def get_base(self,inv):
        base = 0.0
        for tax in inv.tax_line:
            base += tax.base
        return self.numf(base)

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
        
    def per_iva(self,inv):
        per = ""
        if inv.invoice_line and inv.invoice_line[0].id:
           per = inv.invoice_line[0].invoice_line_tax_id[0].amount
        per = "%0.f" % (per * 100)
        return per
    
    def lines(self):
        i_obj = self.pool.get('account.invoice')
        c_id = self.datas['form']['company_id']
        start = self.datas['form']['date_start']
        end = self.datas['form']['date_end']

        s = [('company_id','=',c_id)]
        s.append(('date_invoice','>=',start))
        s.append(('date_invoice','<=',end))
        s.append(('state','in',('open','paid')))
        s.append(('type','=','in_invoice'))
        ids = i_obj.search(self.cr,self.uid,s,order='reference')
        # calculo alguns totals
        self.tax = 0.0
        self.untaxed = 0.0
        self.total = 0.0
        self.base = 0.0
        self.count = len(ids)
        self.taxes = {}
        self.taxes[0] = [0.0,0.0,0]
        for inv in i_obj.browse(self.cr,self.uid,ids):
            self.tax = self.tax + inv.amount_tax
            self.untaxed = self.untaxed + inv.amount_untaxed
            self.total = self.total + inv.amount_total
            base = 0.0
            # dades per a resum per tipus de IVA
            for tax in inv.tax_line:
                self.base += tax.base
                base += tax.base
                group = False
                for l in inv.invoice_line:
                    if l.invoice_line_tax_id and \
                    l.invoice_line_tax_id[0].tax_code_id.id == tax.tax_code_id.id:
                        group = l.invoice_line_tax_id[0].id
                if not group:
                    continue
                if group not in self.taxes:
                    self.taxes[group] = [0.0,0.0,0]
                self.taxes[group][0] += tax.base
                self.taxes[group][1] += tax.amount
                self.taxes[group][2] += 1
            if base != inv.amount_untaxed:
                self.taxes[0][0] += (inv.amount_untaxed - base)
                self.taxes[0][2] += 1
            
        return i_obj.browse(self.cr,self.uid,ids)

    def tax_lines(self):
        lines = []
        for k,v in self.taxes.items():
            if k == 0:
                continue
            tax = self.pool.get('account.tax').browse(self.cr,self.uid,k)
            item = {}
            item['name'] = tax.name
            item['base'] = self.numf(v[0])
            item['tax'] = self.numf(v[1])
            item['total'] = self.numf(v[0] + v[1])
            item['count'] = v[2]
            lines.append(item)
        item = {
            'name':'Exempt',
            'base': self.numf(self.taxes[0][0]),
            'tax': '0.00',
            'total': self.numf(self.taxes[0][0]),
            'count':self.taxes[0][2],
        }
        lines.append(item)
        return lines
    
report_sxw.report_sxw('report.account.invoice.journal_sup', 'account.invoice', 'addons/carreras/report/invoice_journal_sup.rml',parser=invoice_journal_sup)

