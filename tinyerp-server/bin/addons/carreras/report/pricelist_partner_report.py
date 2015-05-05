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
  Llistat de Tarifes de Clients
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

class pricelist_partner_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(pricelist_partner_report, self).__init__(cr, uid, name, context)
        self.products = {}
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'format_date': self.format_date,
            'get_pricelist':self.get_pricelist,
            'get_product':self.get_product,
            'lines':self.lines,
            'get_total':self.get_total,
        })
    def preprocess(self, objects, data, ids):
        self.company_id=data['form']['company_id']
        super(pricelist_partner_report, self).preprocess(objects, data, ids)
        
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
    
    def get_product(self,prod):
        if prod in self.products:
            return self.products[prod]
        p = self.pool.get('product.product').read(self.cr,self.uid,[prod],['default_code','name'])
        self.products[prod] = "[%s] %s" % (p[0]['default_code'],p[0]['name'])
        return self.products[prod]

    def get_pricelist(self,partner):
        #print partner,len(self.prices.get(partner,[]))
        return self.prices.get(partner,[])
        
    def lines(self):
        #company_ids=self.pool.get('res.company')._get_company_children(self.cr,self.uid,self.company_id)
        ids = ",".join(map(str,self.ids))
        sql = "select p.name as partner_name,t.name,t.product_id,t.minimum,t.apply_minimum ,t.price " +\
              "from pricelist_partner t, res_partner p, res_partner_customer c " +\
              "where t.company_id = '%d' and c.partner_id = t.partner_id and " % self.company_id +\
              "c.partner_id = p.id and c.id in (%s) order by p.name" % ids

        """
        d = {}
        for p in ids:
            d[p] = []
        sql = sql % s_ids
        self.cr.execute(sql )
        for p in self.cr.dictfetchall():
            if p['partner_id'] in d:
                d[p['partner_id']].append(p)
        self.prices = d
        
        res = []
        for partner in self.objects:
            for p in self.get_pricelist(partner.id):
                p['partner'] = partner
                res.append(p)
        """
        
        res=[]
        self.cr.execute(sql)
        for r in self.cr.dictfetchall():
            line=[]
            line.append(r['partner_name'])
            line.append(r['name'])
            line.append(self.get_product(r['product_id']))
            line.append(r['apply_minimum'] and self.numf(r['minimum']) or '')
            line.append(self.numf(r['price']))
            res.append(line)
            
        self.total = len(res)
        return res
    
    def get_total(self):
        return self.total

report_sxw.report_sxw('report.carreras.pricelist_partner_report', 'res.partner.customer', 'addons/carreras/report/pricelist_partner_report.rml',parser=pricelist_partner_report)
                       
