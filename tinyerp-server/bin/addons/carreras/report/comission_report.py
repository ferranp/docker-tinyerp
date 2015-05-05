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
  Llista les comissions dels representants
"""
import pooler
import time
from report import report_sxw
import netsvc

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

import locale
locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

class comission_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(comission_report, self).__init__(cr, uid, name, context)
        pool = pooler.get_pool(cr.dbname)
        self.localcontext.update( {
            'time': time,
            'get_company': self.get_company,
            'lines': self.lines,
            'detail_lines': self.detail_lines,
            'caps': self.caps,
            'numf': self.numf,
        })

    def numf(self,val):
        return val and locale.format("%0.2f",val,grouping=True) or ""

    def get_company(self):
        return self.company_id.name

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        if 'form' in data:
            obj= self.pool.get('agent.agent')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        super(comission_report, self).preprocess(objects, data, ids)
        
        if 'form' in data:
            self.company_id=self.pool.get('res.company').browse(self.cr,self.uid,data['form']['company_id'])
        else:
            self.company_id =self.pool.get('res.users').browse(self.cr,self.uid,self.uid).company_id
        
        query=  "SELECT r.order_id " +\
                "FROM sale_order o, sale_order_invoice_rel r, account_invoice i " +\
                "WHERE o.id=r.order_id AND i.id=r.invoice_id " +\
                "AND i.company_id = '%d' " +\
                "AND i.state <> 'cancel' " +\
                "AND (o.block_comission IS NULL OR o.block_comission = False) "
        query = query % self.company_id
        if 'form' not in data:
            query= "%s AND o.date_comission IS NULL " % query
            date = mx.DateTime.today()
            query= "%s AND i.date_invoice <= '%s' " % (query,date.strftime("%Y-%m-%d"))
        else:
            form=data['form']
            if form['closed'] == 'closed':
                query= "%s AND o.date_comission IS NOT NULL " % query
            if form['closed'] == 'open':
                query= "%s AND o.date_comission IS NULL " % query
            if form['agent_id']:
                query= "%s AND o.agent_id ='%d' " % (query,form['agent_id'])
            else:
                query= "%s AND o.agent_id IS NOT NULL " % query
            if form['date_start']:
                query="%s AND i.date_invoice BETWEEN '%s' AND '%s' " \
                    % (query,form['date_start'],form['date_end'])
            else:
                query= "%s AND i.date_invoice <= '%s' " % (query,form['date_end'])
        query= "%s GROUP BY r.order_id " % query
        
        logger = netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,query)
        self.cr.execute(query)
        ids=[ row[0] for row in self.cr.fetchall() ]
        logger.notifyChannel("info", netsvc.LOG_INFO,len(ids))
        base,comission=self.process_lines(ids)
        
        self.caps=[]
        self.caps.append(["Suma de Bases",base])
        self.caps.append(["Total Comissions",comission])
        if 'form' in data:
            if form['agent_id']:
                agent_id= self.pool.get('agent.agent').browse(self.cr,self.uid,form['agent_id'])
                self.caps.append(["Representant",agent_id.name])
            else:
                self.caps.append(["Representants","Tots"])
            if form['date_start']:
                self.caps.append(['Interval',
                    "%s - %s" % (self.format_date(form['date_start']),self.format_date(form['date_end']))])
            else:
                self.caps.append(['Data Màxmia',self.format_date(form['date_end'])])
            if form['closed'] == 'closed':
                self.caps.append(['Albarans','Liquidats'])
            elif form['closed'] == 'open':
                self.caps.append(['Albarans','No Liquidats'])
            else:
                self.caps.append(['Albarans','Tots'])
                
        else:
            self.caps.append(['Data Màxmia',date.strftime("%d-%m-%Y")])
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
        
    def process_lines(self,ids):
        self.lines=[]
        self.detail_lines=[]
        lines=[]
        for so in self.pool.get('sale.order').browse(self.cr,self.uid,ids):
            line=[]
            line.append(so.agent_id.code)
            line.append(so.agent_id.name)
            line.append(so.order_line[0].product_id.code)
            line.append(so.order_line[0].product_id.name)
            line.append(so.delivery)
            line.append(self.format_date(so.date_delivery))
            line.append(so.amount_untaxed)
            line.append(so.amount_comission)
            lines.append(line)
        
        if len(lines)==0:
            return 0,0
        
        lines.sort(lambda x,y:  cmp(x[4],y[4]))
        lines.sort(lambda x,y:  cmp(x[2],y[2]))
        lines.sort(lambda x,y:  cmp(x[0],y[0]))
        
        last=None
        agent_acum_1=0
        agent_acum_2=0
        prod_acum_1=0
        prod_acum_2=0
        tot_acum_1=0
        tot_acum_2=0
        
        for i,line in enumerate(lines):
            if last:
                if (line[2] != last[2] or line[0] != last[0]):
                    self.lines.append([
                        last[0],last[1],
                        last[2],last[3],
                        prod_acum_1,prod_acum_2])
                        
                    self.detail_lines.append(['','','','','','','',''])
                    self.detail_lines.append([
                        '',"TOTAL " + last[1],
                        '',last[3],'','',
                        prod_acum_1,prod_acum_2])
                    prod_acum_1=0
                    prod_acum_2=0
                    self.detail_lines.append(['','','','','','','',''])
                
                if line[0] != last[0]:
                    self.lines.append(['','','','','',''])
                    self.lines.append([
                        '',"TOTAL " +last[1],
                        '','',agent_acum_1,agent_acum_2])
                    self.lines.append(['','','','','',''])
                    
                    self.detail_lines.append([
                        '',"TOTAL " +last[1],'','',
                        '','',agent_acum_1,agent_acum_2])
                    self.detail_lines.append(['','','','','','','',''])
                    agent_acum_1=0
                    agent_acum_2=0
            
            agent_acum_1 += line[6]
            agent_acum_2 += line[7]
            prod_acum_1 += line[6]
            prod_acum_2 += line[7]
            tot_acum_1 += line[6]
            tot_acum_2 += line[7]
            
            self.detail_lines.append(line)
            last=line

        self.lines.append([
            last[0],last[1],
            last[2],last[3],
            prod_acum_1,prod_acum_2])
        self.lines.append(['','','','','',''])
        self.lines.append([
            '',"TOTAL " +last[1],
            '','',agent_acum_1,agent_acum_2])
        self.lines.append(['','','','','',''])

        self.detail_lines.append(['','','','','','','',''])
        self.detail_lines.append([
            '',"TOTAL " + last[1],
            '',last[3],'','',
            prod_acum_1,prod_acum_2])
        self.detail_lines.append(['','','','','','','',''])
        self.detail_lines.append([
            '',"TOTAL " + last[1],'','',
            '','',agent_acum_1,agent_acum_2])
        self.detail_lines.append(['','','','','','','',''])
        return tot_acum_1,tot_acum_2
        
    def lines(self):
        return self.lines

    def detail_lines(self):
        return self.detail_lines
    
    def caps(self):
        return self.caps

    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowHeights="14"
        if self.name == 'comission.report':
            lines=self.lines
        else:
            lines=self.detail_lines
        
        for line in lines:
            if line[1]=='':
                rowHeights=rowHeights+",5"
            else:
                rowHeights=rowHeights+",11"
        
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                print rowHeights
                elem.setAttribute("rowHeights",rowHeights)
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Cap":
                elem.setAttribute("rowHeights",("12,"*len(self.caps))[:-1])
                
        res = self.dom.documentElement.toxml('utf-8')
        return res

class close_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(close_report, self).__init__(cr, uid, name, context)
        pool = pooler.get_pool(cr.dbname)
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'get_dates': self.get_dates,
            'numf': self.numf,
        })

    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        if 'form' in data:
            obj= self.pool.get('agent.agent')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        super(close_report, self).preprocess(objects, data, ids)
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_dates(self):
        form=self.datas['form']
        return "%s - %s" % (self.format_date(form['date_start']),self.format_date(form['date_end']))

    def lines(self,o):
        form=self.datas['form']
        s=[]
        s.append(('agent_id','=',o.id))
        s.append(('date_comission','>=',form['date_start']))
        s.append(('date_comission','<=',form['date_end']))
        s.append(('company_id','child_of',[form['company_id']]))
        so_obj=self.pool.get('sale.order')
        ids=so_obj.search(self.cr,self.uid,s)
        logger = netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,len(ids))
        
        base=0
        comission=0
        products={}
        for so in so_obj.browse(self.cr,self.uid,ids):
            product_id=so.order_line[0].product_id
            if product_id.code not in products:
                products[product_id.code]=[]
                products[product_id.code].append(product_id.code)
                products[product_id.code].append(product_id.name)
                products[product_id.code].append(0.0)
                for p in o.product_ids:
                    if p.product_id.id == product_id.id:
                        products[product_id.code].append(p.comission)
                        break
                else:
                    if product_id.default_agent_id and product_id.default_agent_id.id == o.id:
                        products[product_id.code].append(product_id.default_comission)
                    else:
                        products[product_id.code].append(so.comission)
                products[product_id.code].append(0.0)
                        
            products[product_id.code][2] += so.amount_untaxed
            products[product_id.code][4] += so.amount_comission
            base+=so.amount_untaxed
            comission+=so.amount_comission
        
        for k in products.keys():
            products[k][2]=locale.format("%.2f",products[k][2],grouping=True)
            products[k][4]=locale.format("%.2f",products[k][4],grouping=True)
        
        lines=products.values()
        lines.sort(lambda x,y:  cmp(x[0],y[0]))
        lines.append(['','','','',''])
        lines.append([  '',
                        'TOTAL LIQUIDACIÓ',
                        locale.format("%.2f",base,grouping=True),
                        '',
                        locale.format("%.2f",comission,grouping=True)])
        
        return lines

report_sxw.report_sxw('report.close.report', 'agent.agent', 'addons/carreras/report/comission_close_report.rml',parser=close_report)
report_sxw.report_sxw('report.comission.report', 'agent.agent', 'addons/carreras/report/comission_report.rml',parser=comission_report)
report_sxw.report_sxw('report.comission.report.detail', 'agent.agent', 'addons/carreras/report/comission_report_detail.rml',parser=comission_report)

