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
  Llista una remesa
"""
import pooler
import time
from report import report_sxw

class account_remittance(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_remittance, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'format_date': self.format_date,
            'lines': self.lines,
            'get_type': self.get_type,
            'unicode':self.unicode,
        })
        self.mem_lines={}

    def unicode(self,string):
        return unicode(string,'utf8')

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        super(account_remittance, self).preprocess(objects, data, ids)
        return
    
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
        
    def get_type(self,rem):
        obj = self.pool.get('account.payment.term.type')
        ids = obj.search(self.cr, self.uid, [('code','=',rem.type)])
        if not ids:
            return ''
        reg = obj.read(self.cr,self.uid,ids,['name'])
        return reg[0]['name']

    def get_address(self,partner_id,field):
        addr = self.pool.get('res.partner').address_get(self.cr,self.uid,[partner_id])['default']
        addr_obj=self.pool.get('res.partner.address')
        return addr_obj.read(self.cr,self.uid,[addr],[field])[0][field]

    def lines(self,rem):
        lines=[]
        for l in rem.receivable_ids:
            line=[]
            line.append(l.partner_id and l.partner_id.customer_ids and l.partner_id.customer_ids[0].name.decode('utf8')[0:45] or '    ')
            line.append(l.partner_id and l.partner_id.name or ' ')
            line.append(l.partner_id and self.get_address(l.partner_id.id,'zip') or ' ')
            line.append(l.partner_id and self.get_address(l.partner_id.id,'city').decode('utf8')[0:20] or ' ')
            line.append(l.date_maturity)
            line.append(l.amount)
            line.append(l.name)
            lines.append(line)
        lines.sort(lambda x,y:  cmp(x[0],y[0]))
        lines.sort(lambda x,y:  cmp(x[4],y[4]))
        
        ret_lines=[]
        last=None
        acum=0
        for i,line in enumerate(lines):
            if last:
                if line[4] != last[4]:
                    ret_lines.append([
                        '','--- TOTAL %s ---' % self.format_date(last[4]),
                        '','','',acum,''])
                    acum=0
            acum=acum + line[5]
            ret_lines.append(line)
            last=line
        ret_lines.append([
            '','--- TOTAL %s ---' % self.format_date(last[4]),
            '','','',acum,''])
        self.mem_lines[rem.id]=ret_lines
        return ret_lines
        
    # Posar menys espai entre les linies de la taula "Albarans"
    # Altura de la linia = 12.5
    # Linies de la taula = self.lines_per_page
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowHeights=[]
        for id,lines in self.mem_lines.iteritems():
            raw="14"
            for line in lines:
                if line[1][0:10]=='--- TOTAL ':
                    raw=raw+",18"
                else:
                    raw=raw+",11"
            rowHeights.append(raw)
        
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights.pop(0))
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Cap":
                elem.setAttribute("rowHeights","12,12,12,12")
                
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.account.remittance', 'account.receivable.remittance', 'addons/account_receivable/report/remittance.rml',parser=account_remittance)

