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
  Llista el Risc dels bancs
"""
import pooler
import time
from report import report_sxw

class bank_risk(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(bank_risk, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'format_date': self.format_date,
            'rlines': self.rlines,
            'vlines': self.vlines,
            'get_total':self.get_total,
        })

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        super(bank_risk, self).preprocess(objects, data, ids)
        self.process_rems(objects)
        return
        if 'form' in data:
            obj= self.pool.get('account.receivable')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        super(account_receivables, self).preprocess(objects, data, ids)
        total,receivables=self.process_lines()
        self.caps=[]
        self.caps.append(["Suma d'imports",total])
        self.caps.append(["Número d'efectes",receivables])
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def process_rems(self,objects):
        rec_obj=self.pool.get('account.receivable')
        rem_obj=self.pool.get('account.receivable.remittance')
        date = time.strftime('%Y-%m-%d')
        self.vlines={}
        self.rlines={}
        self.totals={}
        for bank in objects:
            self.vlines[bank.id]=[]
            self.rlines[bank.id]=[]
            self.totals[bank.id]=('0','0.00')
            
            s = [('state','=','received'),
                ('channel_id','=',bank.id),
                ('company_id','child_of',[bank.company_id.id])]
            rem_ids = rem_obj.search(self.cr,self.uid,s)
            s = [('remittance_id','in',rem_ids)]
            rec_ids = rec_obj.search(self.cr,self.uid,s)
            
            recs=[]
            for rec in rec_obj.browse(self.cr,self.uid,rec_ids):
                if rec.date_risk >= date:
                    recs.append(rec)
            if len(recs)==0:
                continue
            
            recs.sort(lambda x,y: cmp(
                x.partner_id and x.partner_id.customer_ids and x.partner_id.customer_ids[0].name or ' ',
                y.partner_id and y.partner_id.customer_ids and y.partner_id.customer_ids[0].name or ' '))
            recs.sort(lambda x,y:  cmp(x.date_risk,y.date_risk))
            
            last=None
            imp_acu=0
            num_acu=0
            imp_tot=0
            num_tot=0
            
            rlines=[]
            vlines=[]
            for rec in recs:
                if last:
                    if rec.date_risk != last.date_risk:
                        rlines.append([
                            '','--- Total %d Efectes---' % num_acu,
                            '',self.format_date(last.date_risk),imp_acu,''])
                        vlines.append([self.format_date(last.date_risk),num_acu,imp_acu])
                        imp_acu=0
                        num_acu=0
                imp_acu=imp_acu + rec.amount
                imp_tot=imp_tot + rec.amount
                num_acu=num_acu + 1
                num_tot=num_tot + 1

                line=[]
                line.append(rec.partner_id and rec.partner_id.customer_ids and rec.partner_id.customer_ids[0].name or ' ')
                line.append(rec.partner_id and rec.partner_id.name or ' ')
                line.append(self.format_date(rec.date_maturity))
                line.append(self.format_date(rec.date_risk))
                line.append(rec.amount)
                line.append(rec.name)
                rlines.append(line)
                last=rec
            
            vlines.append([self.format_date(last.date_risk),num_acu,imp_acu])
            self.vlines[bank.id]=vlines
            rlines.append([
                '','--- Total %d Efectes---' % num_acu,
                '',self.format_date(last.date_risk),imp_acu,''])
            self.rlines[bank.id]=rlines
            self.totals[bank.id]=(num_tot,imp_tot)
        return

    def vlines(self,bank):
        return self.vlines[bank.id]
    
    def rlines(self,bank):
        return self.rlines[bank.id]

    def get_total(self,bank):
        return self.totals[bank.id]

    # Posar menys espai entre les linies de la taula
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rrowHeights=[]
        for lines in self.rlines.values():
            raw="14"
            for line in lines:
                if line[1][0:10]=='--- Total ':
                    raw=raw+",18"
                else:
                    raw=raw+",11"
            raw=raw+",5,11"
            rrowHeights.append(raw)
        vrowHeights=[]
        for lines in self.vlines.values():
            raw="14"
            for line in lines:
                raw=raw+",11"
            raw=raw+",5,11"
            vrowHeights.append(raw)
        
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                if len(rrowHeights):
                    elem.setAttribute("rowHeights",rrowHeights.pop(0))
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Venciments":
                if len(vrowHeights):
                    elem.setAttribute("rowHeights",vrowHeights.pop(0))
                
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.account_receivable.bank_risk', 'account.receivable.channel', 'addons/account_receivable/report/bank_risk.rml',parser=bank_risk)
report_sxw.report_sxw('report.account_receivable.bank_risk_detail', 'account.receivable.channel', 'addons/account_receivable/report/bank_risk_detail.rml',parser=bank_risk)

