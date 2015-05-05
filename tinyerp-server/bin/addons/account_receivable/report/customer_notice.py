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
  Avisos d'efectes vençuts
"""
import pooler
import time
from report import report_sxw

class customer_notice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(customer_notice, self).__init__(cr, uid, name, context)
        self.account_id=None
        self.localcontext.update( {
            'time': time,
            'format_date': self.format_date,
            'get_text_month': self.get_text_month,
            'get_amount': self.get_amount,
            'company_address': self.company_address,
            'partner_address': self.partner_address,
            'get_ccc': self.get_ccc,
        })

    def preprocess(self, objects, data, ids):
        super(customer_notice, self).preprocess(objects, data, ids)
        
        id=self.objects[0].company_id.id
        addr=self.pool.get('res.partner').address_get(self.cr,self.uid,[id])['default']
        fields=self.pool.get('res.partner.address').read(self.cr,self.uid,[addr])[0]
        self.company_addr={
            'street':fields['street'] or '',
            'phone':fields['phone'] or '',
            'fax':fields['fax'] or '',
            'zip_city':"%s %s" % (fields['zip'] or '',fields['city'] or ''),
            'zip_city_state':"%s %s %s" % (fields['zip'] or '',fields['city'] or '',
                        fields['state_id'] and fields['state_id'][1] or ''),
            }

        id=self.objects[0].partner_id.id
        addr=self.pool.get('res.partner').address_get(self.cr,self.uid,[id])['default']
        fields=self.pool.get('res.partner.address').read(self.cr,self.uid,[addr])[0]
        self.partner_addr={
            'street':fields['street'].decode('utf8')[0:45] or '',
            'phone':fields['phone'] or '',
            'fax':fields['fax'] or '',
            'zip_city': ("%s %s" % (fields['zip'] or '',fields['city'] or '')).decode('utf8')[0:45],
            'zip_city_state':"%s %s %s" % (fields['zip'] or '',fields['city'] or '',
                        fields['state_id'] and ("(%s)" % fields['state_id'][1]) or ''),
            }

    def company_address(self):
        return self.company_addr
    
    def partner_address(self):
        return self.partner_addr
    
    def get_text_month(self):
        months={'01':' Enero',
                '02':'Febrero',
                '03':'Marzo',
                '04':'Abril',
                '05':'Mayo',
                '06':'Junio',
                '07':'Julio',
                '08':'Agosto',
                '09':'Septiembre',
                '10':'Octubre',
                '11':'Noviembre',
                '12':'Diciembre'}
        return months[time.strftime('%m')]
    
    def get_ccc(self,id):
        if not id:
            return ' '
        reg=self.pool.get('account.receivable.channel').read(self.cr,self.uid,[id],['name','code'])
        if not reg:
            return ' '
        return "%s - %s" % (reg[0]['name'].upper(),reg[0]['code'])
    
    def get_amount(self):
        amount=0
        for r in self.objects:
            amount= amount + r.amount
        return amount
        
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
        
    # Posar menys espai entre les linies de la taula "Albarans"
    # Altura de la linia = 12.5
    # Linies de la taula = self.lines_per_page
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowHeights=((str(12.5) + ",") * len(self.objects))[:-1]
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
        res = self.dom.documentElement.toxml('utf-8')
        return res
        
        
report_sxw.report_sxw('report.customer.notice', 'account.receivable', 'addons/account_receivable/report/customer_notice.rml',
    parser=customer_notice,header=False)

