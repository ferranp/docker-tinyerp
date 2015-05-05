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
  Fa el llistat de clients
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

class customer_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(customer_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_count': self.get_count,
            'format_date': self.format_date,
            'lines': self.lines,
            'risk_lines': self.risk_lines,
        })
    def preprocess(self, objects, data, ids):
        super(customer_report, self).preprocess(objects, data, ids)
    
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
        c_obj = self.pool.get('res.partner.customer')
        start = self.datas['form']['code_start']
        end = self.datas['form']['code_end']
        c_id = self.datas['form']['company_id']

        s = []
        s.append(('name','>=',start))
        s.append(('name','<=',end))
        s.append(('company_id','=',c_id))
        if self.datas['form']['name']:
            s.append(('partner_id','ilike',"%" + self.datas['form']['name'] + "%" ))
        ids = c_obj.search(self.cr,self.uid,s,order='name')
        self.count = len(ids)
        self.grid=4+self.count
        return c_obj.browse(self.cr,self.uid,ids)

    def risk_lines(self):
        c_obj = self.pool.get('res.partner.customer')
        start = self.datas['form']['code_start']
        end = self.datas['form']['code_end']
        c_id = self.datas['form']['company_id']

        s = []
        s.append(('name','>=',start))
        s.append(('name','<=',end))
        s.append(('company_id','=',c_id))
        if self.datas['form']['name']:
            s.append(('partner_id','ilike',"%" + self.datas['form']['name'] + "%" ))
        ids = c_obj.search(self.cr,self.uid,s,order='name')
        self.count = 0
        self.grid=4
        
        p_obj = self.pool.get('res.partner')
        lines=[]
        for c in c_obj.browse(self.cr,self.uid,ids):
            if not c.partner_id.alb_risk and not c.partner_id.fac_risk and \
               not c.partner_id.efe_risk and not c.partner_id.cir_risk and \
               not c.partner_id.imp_risk and not c.partner_id.mor_risk:
                continue
            if self.count and not self.count % 3:
                lines.append(['','','','','','','','','','',''])
                self.grid=self.grid+1
            line=[]
            line.append(c.name)
            line.append(c.partner_id.ref)
            line.append(c.partner_id.name.decode('utf8')[0:15])
            line.append(c.partner_id.alb_risk or '0.00')
            line.append(c.partner_id.fac_risk or '0.00')
            line.append(c.partner_id.efe_risk or '0.00')
            line.append(c.partner_id.cir_risk or '0.00')
            line.append(c.partner_id.imp_risk or '0.00')
            line.append(c.partner_id.mor_risk or '0.00')
            line.append(c.partner_id.risk or '0.00')
            line.append(c.partner_id.credit_limit or '0.00')
            lines.append(line)
            self.count=self.count+1
            self.grid=self.grid+1
        return lines

    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowSize=12
        rowHeights=((str(rowSize) + ",") * (self.grid))[:-1]
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.carreras.customer_report', 'res.partner', 'addons/carreras/report/customer_report.rml',parser=customer_report)
report_sxw.report_sxw('report.carreras.customer_risk_report', 'res.partner', 'addons/carreras/report/customer_risk_report.rml',parser=customer_report)

