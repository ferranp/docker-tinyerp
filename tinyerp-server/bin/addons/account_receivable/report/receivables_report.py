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

class account_receivables(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_receivables, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'format_date': self.format_date,
            'lines': self.lines,
            'caps': self.caps,
        })

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        if 'form' in data:
            obj= self.pool.get('account.receivable')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        super(account_receivables, self).preprocess(objects, data, ids)
        total,receivables=self.process_lines()
        self.caps=[]
        self.caps.append(["Suma d'imports",total])
        self.caps.append(["Número d'efectes",receivables])
        if 'form' in data:
            f=data['form']
            if f['state'] != 'all':
                states={'draft':'Esborrany','pending':'Pendent','posted':'Remesat','received':'Cobrat'}
                self.caps.append(['Estat',states[f['state']]])
            if f['unpaid'] != 'all':
                states={'normal':'No','unpaid':'Sí'}
                self.caps.append(['Impagats',states[f['unpaid']]])
            if f['morositat'] != 'all':
                states={'normal':'Normal','moros':'Morós'}
                self.caps.append(['Morositat',states[f['morositat']]])
            if f['type']:
                self.caps.append(['Tipus',self.get_type(f['type'])])
            if f['venc_min'] or f['venc_max']:
                if not f['venc_min']:
                    self.caps.append(['Venciment Màxim',self.format_date(f['venc_max'])])
                elif not f['venc_max']:
                    self.caps.append(['Venciment Mínim',self.format_date(f['venc_min'])])
                else:
                    self.caps.append(['Rang de venciments',"%s - %s" % 
                       (self.format_date(f['venc_min']),
                        self.format_date(f['venc_max']))])
            if f['date_min'] or f['date_max']:
                if not f['date_min']:
                    self.caps.append(['Data Màxima',self.format_date(f['date_max'])])
                elif not f['date_max']:
                    self.caps.append(['Data Mínima',self.format_date(f['date_min'])])
                else:
                    self.caps.append(['Rang de dates',"%s - %s" % 
                        (self.format_date(f['date_min']),
                        self.format_date(f['date_max']))])
            if f['customer_id_1'] or f['customer_id_2']:
                if not f['customer_id_1']:
                    self.caps.append(['Codi de Client Màxim',f['customer_id_2']])
                elif not f['customer_id_2']:
                    self.caps.append(['Codi de Client Mínim',f['customer_id_1']])
                else:
                    self.caps.append(['Codis de Clients',"%s - %s" % 
                        (f['customer_id_1'],f['customer_id_2'])])
        return

    def get_customer(self,id):
        reg = self.pool.get('res.partner.customer').read(self.cr,self.uid,[id],['name'])
        return reg[0]['name']

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
        
    def get_type(self,type):
        obj = self.pool.get('account.payment.term.type')
        ids = obj.search(self.cr, self.uid, [('code','=',type)])
        if not ids:
            return ''
        reg = obj.read(self.cr,self.uid,ids,['name'])
        return reg[0]['name']

    def get_address(self,partner_id,field):
        addr = self.pool.get('res.partner').address_get(self.cr,self.uid,[partner_id])['default']
        addr_obj=self.pool.get('res.partner.address')
        return addr_obj.read(self.cr,self.uid,[addr],[field])[0][field]
        
    def process_lines(self):
        self.mem_lines=[]
        if not self.objects:
            return 0,0
        lines=[]
        for l in self.objects:
            line=[]
            line.append(l.partner_id and l.partner_id.customer_ids and l.partner_id.customer_ids[0].name or ' ')
            line.append(l.partner_id and l.partner_id.name or ' ')
            line.append(l.partner_id and self.get_address(l.partner_id.id,'zip') or ' ')
            line.append(l.partner_id and self.get_address(l.partner_id.id,'city').decode('utf8')[0:17] or ' ')
            line.append(l.date_maturity)
            line.append(l.amount)
            line.append(l.name)
            lines.append(line)
        if len(lines)==0:
            return ['','','','','','','']
        
        lines.sort(lambda x,y:  cmp(x[0],y[0]))
        lines.sort(lambda x,y:  cmp(x[4],y[4]))
        
        last=None
        acum=0
        total=0
        receivables=0
        for i,line in enumerate(lines):
            if last:
                if line[4] != last[4]:
                    self.mem_lines.append([
                        '','--- TOTAL %s ---' % self.format_date(last[4]),
                        '','','',acum,''])
                    acum=0
            acum=acum + line[5]
            total=total+line[5]
            receivables=receivables+1
            self.mem_lines.append(line)
            last=line
        self.mem_lines.append([
            '','--- TOTAL %s ---' % self.format_date(last[4]),
            '','','',acum,''])
        return total,receivables
            
    def lines(self):
        return self.mem_lines
    
    def caps(self):
        return self.caps
    
    # Posar menys espai entre les linies de la taula "Albarans"
    # Altura de la linia = 12.5
    # Linies de la taula = self.lines_per_page
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        
        rowHeights="14"
        for line in self.mem_lines:
            if line[1][0:10]=='--- TOTAL ':
                rowHeights=rowHeights+",18"
            else:
                rowHeights=rowHeights+",11"
        
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Cap":
                elem.setAttribute("rowHeights",("12,"*len(self.caps))[:-1])
                
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.receivables.report', 'account.receivable', 'addons/account_receivable/report/receivables_report.rml',parser=account_receivables)

