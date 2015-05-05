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
Tarifes de Compres

"""
import pooler
import time
from report import report_sxw
import locale
import netsvc

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime


locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d


class pricelist_supplier_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(pricelist_supplier_report, self).__init__(cr, uid, name, context)
        pool = pooler.get_pool(cr.dbname)
        self.localcontext.update( {
            'time': time,
            'caps': self.caps,
            'pages': self.pages,
            'numf': lambda x: x and locale.format("%0.2f",x,grouping=True) or '',
            'format_date': self.format_date,
            'get_title': self.get_title,
            #'get_period': self.get_period,
            #'get_shop': self.get_shop,
            #'get_products': self.get_products,
            #'get_customer': self.get_customer,
        })

    def get_title(self):
        return self.actual and 'Tarifes de Compres Vigents' or 'Tarifes de Compres Històriques' 

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        self.actual=False
        order='family_id'
        user = self.pool.get('res.users').read(self.cr,self.uid,[self.uid],['company_id'])[0]
        company_id = user['company_id'][0]
        self.rows=[]
        
        if 'form' in data:
            obj= self.pool.get('product.product')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
            self.actual=data['form']['actual']
            order=data['form']['order']
            company_id=data['form']['company_id']
        super(pricelist_supplier_report, self).preprocess(objects, data, ids)
        self.process_lines(ids,self.actual,order,company_id)
        return

    def pages(self):
        return self.mem_pages
    def caps(self,p):
        form=self.datas['form']
        caps=[]
        if form['order']=='family_id':
            o=self.pool.get('product.family').browse(self.cr,self.uid,p[0][0][8])
            caps.append(['Familia',o and (o.name+' '+o.description) or 'No definida'])
        else:
            o=self.pool.get('product.department').browse(self.cr,self.uid,p[0][0][9])
            caps.append(['Departament',o and (o.name+' '+o.description) or 'No definit'])
        caps.append(['Famílies','%s - %s' % (form['family1'] or '',form['family2'] or '')])
        caps.append(['Departaments','%s - %s' % (form['department1'] or '',form['department2'] or '')])
        caps.append(['Productes','%s - %s' % (form['code1'] or '',form['code2'] or '')])
        
        return caps


    def process_lines(self,product_ids,actual,order,company_id):
        """
        batch_id=self.pool.get('res.users').search(self.cr,self.uid,[('login','=','batch')])
        if not batch_id:
            return
        batch_id=batch_id[0]
        """

        obj=self.pool.get('product.family')
        ids= obj.search(self.cr,self.uid,[])
        codes= [(x.id,x.name) for x in obj.browse(self.cr,self.uid,ids)]
        fam_codes=dict(codes)
        fam_codes['']=''
        obj=self.pool.get('product.department')
        ids= obj.search(self.cr,self.uid,[])
        codes= [(x.id,x.name) for x in obj.browse(self.cr,self.uid,ids)]
        dep_codes=dict(codes)
        dep_codes['']=''

        form=self.datas['form']
        query=  "SELECT p.default_code, t.name, '', " +\
                      " s.name, r.name, l.price, l.date_start,l.date_end, p.family_id, p.department_id " +\
                "FROM product_product p, product_template t, pricelist_supplier l," +\
                    " res_partner r, res_partner_supplier s " +\
                "WHERE p.product_tmpl_id=t.id AND p.id=l.product_id AND" +\
                    " l.partner_id=r.id AND s.partner_id=r.id AND " +\
                    " s.company_id='%d' AND p.id IN (%s) " % \
                    (company_id,','.join(map(str,product_ids)))
        if actual:
            query="%s AND (l.date_end IS NULL OR l.date_end >= '%s')" % \
                (query, time.strftime('%Y-%m-%d'))
        query="%s ORDER BY p.%s,p.default_code,l.date_end desc" % (query,order)
        self.cr.execute(query)
        
        pages={}
        last_page=None
        lines=[]
        last_code=None
        total=0
        for row in self.cr.fetchall():
            row= map(lambda x: x and x or '', row)
            row[1]=row[1].split('\n')[0]
            if order=='family_id':
                row[2]=dep_codes[row[9]]
                curr_page=fam_codes[row[8]]
            if order=='department_id':
                row[2]=fam_codes[row[8]]
                curr_page=dep_codes[row[9]]
            curr_code=row[0]
            
            if last_page and last_page != curr_page:
                pages[last_page]=(lines,total)
                lines=[]
                last_code=None
                total=0
            
            if last_code and last_code == curr_code:
                row[0]=''
                row[1]=''
                row[2]=''
            else:
                total+=1
            
            lines.append(row)
            
            last_page=curr_page
            last_code=curr_code
        
        pages[last_page]=(lines,total)
        
        keys=pages.keys()
        keys.sort()
        
        self.mem_pages=[]
        for k in keys:
            self.mem_pages.append(pages[k])
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    """
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowHeights="14"
        for line in self.lines:
            if line[2]=='':
                rowHeights+=",18"
            else:
                rowHeights+=",11"
        rowHeights+=",20"
        
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Cap":
                elem.setAttribute("rowHeights","12,12,12,12")
        
        res = self.dom.documentElement.toxml('utf-8')
        return res
    """

report_sxw.report_sxw('report.carreras.pricelist_supplier_report', 'product.product', 'addons/carreras/report/pricelist_supplier_report.rml',parser=pricelist_supplier_report)
