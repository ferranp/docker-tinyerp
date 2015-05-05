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
Estadístiques
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

class estadis_product(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(estadis_product, self).__init__(cr, uid, name, context)
        pool = pooler.get_pool(cr.dbname)
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'sum': self.sum,
            'get_period': self.get_period,
            'get_shop': self.get_shop,
            'get_products': self.get_products,
            'get_customer': self.get_customer,
        })

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        if 'form' in data:
            obj= self.pool.get('product.product')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        super(estadis_product, self).preprocess(objects, data, ids)
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_period(self):
        form=self.datas['form']
        return "%s - %s" % (self.format_date(form['date_1']),self.format_date(form['date_2']))
    def get_shop(self):
        form=self.datas['form']
        if not form['shop_id']:
            return "Tots"
        return self.pool.get('sale.shop').browse(self.cr,self.uid,form['shop_id']).name
    def get_products(self):
        form=self.datas['form']
        return "%s - %s" % (form['product_1'],form['product_2'])
    def get_customer(self):
        form=self.datas['form']
        if not form['customer_id']:
            return "Tots"
        return self.pool.get('res.partner.customer').browse(self.cr,self.uid,form['customer_id']).name

    def lines(self):
        batch_id=self.pool.get('res.users').search(self.cr,self.uid,[('login','=','batch')])
        if not batch_id:
            return []
        batch_id=batch_id[0]
        
        form=self.datas['form']
        query=  "SELECT r.order_id " +\
                "FROM sale_order o, sale_order_line l, sale_order_invoice_rel r, account_invoice i " +\
                "WHERE o.id=r.order_id AND i.id=r.invoice_id AND o.id=l.order_id"
        query = "%s AND i.date_invoice BETWEEN '%s' AND '%s'" % (query,form['date_1'],form['date_2'])
        query = "%s AND l.product_id in (%s)" % (query,','.join(map(str,form['ids'])))
        if form['shop_id']:
            query = "%s AND o.shop_id='%d'" % (query,form['shop_id'])
        if form['customer_id']:
            query = "%s AND o.customer_id='%d'" % (query,form['customer_id'])
        query = "%s group by r.order_id" % query

        self.cr.execute(query)
        ids=[ row[0] for row in self.cr.fetchall() ]

        products={}
        so_obj=self.pool.get('sale.order')

        limit=10000
        length=len(ids)
        last_size=length % limit
        if last_size:
            sizes= [limit] * ((length - last_size)/limit) + [last_size]
        else:
            sizes= [limit] * ((length - last_size)/limit)

        logger = netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,len(ids))
        logger.notifyChannel("info", netsvc.LOG_INFO,"%d %d" % (len(sizes),limit))
        
        offset=0
        for size in sizes:
            slice_ids=ids[offset:offset+size]
            logger.notifyChannel("info", netsvc.LOG_INFO,"%d %d" % (offset,size))
            for so in so_obj.browse(self.cr,batch_id,slice_ids):
                for l in so.order_line:
                    if l.product_id.id in form['ids']:
                        if l.product_id.default_code not in products:
                            products[l.product_id.default_code]=[l.product_id.default_code]+[0.0]*13
                        month=int(so.invoice_ids[0].date_invoice[5:7])
                        products[l.product_id.default_code][month] += so.amount_lines and so.amount_untaxed * l.price_subtotal/ so.amount_lines or 0
            offset += size
        
        self._sum=[0.0]*14
        for c in products:
            for m in range(1,13):
                products[c][13] += products[c][m]
                self._sum[m] += products[c][m]
            self._sum[13] += products[c][13]
        for c in products:
            for m in range(1,14):
                products[c][m] = locale.format("%.2f",products[c][m],grouping=True)
        for m in range(1,14):
            self._sum[m] = locale.format("%.2f",self._sum[m],grouping=True)
        
        lines=products.values()
        lines.sort(lambda x,y:  cmp(x[0],y[0]))
        return lines
    
    def sum(self,m):
        return self._sum[m]

class estadis_customer(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(estadis_customer, self).__init__(cr, uid, name, context)
        pool = pooler.get_pool(cr.dbname)
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'sum': self.sum,
            'get_period': self.get_period,
            'get_customers': self.get_customers,
            'get_shop': self.get_shop,
            'get_products': self.get_products,
        })

    #
    # objects: browse_record_list
    # data:    {'model':model,'id':id1,'report_type':pdf}
    # ids:     [id1,id2,...,idn]
    #
    def preprocess(self, objects, data, ids):
        if 'form' in data:
            obj= self.pool.get('product.product')
            objects= obj.browse(self.cr,self.uid,data['form']['ids'])
            ids=data['form']['ids']
        self.sum_1=0.0
        self.sum_2=0.0
        self.lines=[]
        super(estadis_customer, self).preprocess(objects, data, ids)
        return

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_period(self):
        form=self.datas['form']
        return "%s - %s" % (self.format_date(form['date_1']),self.format_date(form['date_2']))
    def get_customers(self):
        form=self.datas['form']
        return "%s - %s" % (form['customer_1'],form['customer_2'])
    def get_shop(self):
        form=self.datas['form']
        if not form['shop_id']:
            return "Tots"
        return self.pool.get('sale.shop').browse(self.cr,self.uid,form['shop_id']).name
    def get_products(self):
        form=self.datas['form']
        return "%s - %s" % (form['product_1'],form['product_2'])

    def lines(self):
        batch_id=self.pool.get('res.users').search(self.cr,self.uid,[('login','=','batch')])
        if not batch_id:
            return []
        batch_id=batch_id[0]
        
        form=self.datas['form']
        date = mx.DateTime.strptime(form['date_2'], '%Y-%m-%d')
        date = date + RelativeDateTime(day=1,month=1) 
        date1 = date.strftime("%Y-%m-%d")
        date = date + RelativeDateTime(day=31,month=12) 
        date2 = date.strftime("%Y-%m-%d")

        query=  "SELECT r.order_id " +\
                "FROM sale_order o, sale_order_line l, sale_order_invoice_rel r, account_invoice i, res_partner_customer c " +\
                "WHERE o.id=r.order_id AND i.id=r.invoice_id AND o.id=l.order_id AND o.customer_id=c.id"
        query = "%s AND i.date_invoice BETWEEN '%s' AND '%s'" % (query,date1,date2)
        query = "%s AND l.product_id in (%s)" % (query,','.join(map(str,form['ids'])))
        query = "%s AND c.name BETWEEN '%s' AND '%s'" % (query,form['customer_1'],form['customer_2'])
        if form['shop_id']:
            query = "%s AND o.shop_id='%d'" % (query,form['shop_id'])
        query = "%s group by r.order_id" % query

        self.cr.execute(query)
        ids=[ row[0] for row in self.cr.fetchall() ]
        if not ids:
            return []

        customers={}
        so_obj=self.pool.get('sale.order')
        
        limit=10000
        length=len(ids)
        last_size=length % limit
        if last_size:
            sizes= [limit] * ((length - last_size)/limit) + [last_size]
        else:
            sizes= [limit] * ((length - last_size)/limit)

        logger = netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,len(ids))
        logger.notifyChannel("info", netsvc.LOG_INFO,"%d %d" % (len(sizes),limit))
        
        offset=0
        for size in sizes:
            slice_ids=ids[offset:offset+size]
            logger.notifyChannel("info", netsvc.LOG_INFO,"%d %d" % (offset,size))
            for so in so_obj.browse(self.cr,batch_id,slice_ids):
                if so.customer_id.name not in customers:
                    customers[so.customer_id.name]={}
                cust=customers[so.customer_id.name]
                for l in so.order_line:
                    if l.product_id.id in form['ids']:
                        if l.product_id.default_code not in cust:
                            cust[l.product_id.default_code]= [
                                so.customer_id.name,
                                so.partner_id.name,
                                l.product_id.default_code,
                                l.product_id.name,
                                0.0,
                                0.0]
                        amount= so.amount_untaxed * l.price_subtotal/ so.amount_lines
                        date_invoice= so.invoice_ids[0].date_invoice
                        
                        if date_invoice >= form['date_1'] and date_invoice <= form['date_2']:
                            cust[l.product_id.default_code][4]+= amount
                        cust[l.product_id.default_code][5]+= amount
                customers[so.customer_id.name]=cust
            offset += size
        
        raw=[]
        for customer in customers.values():
            raw=raw + customer.values()

        raw.sort(lambda x,y:  cmp(x[2],y[2]))
        raw.sort(lambda x,y:  cmp(x[0],y[0]))
        if form['order'] == 'name':
            raw.sort(lambda x,y:  cmp(x[1],y[1]))
        
        last=None
        lines=[]
        acum_1=0.0
        acum_2=0.0
        for line in raw:
            if last:
                if last[0] != line[0]:
                    lines.append([
                        last[0],
                        last[1],
                        '',
                        '',
                        locale.format("%.2f",acum_1,grouping=True),
                        locale.format("%.2f",acum_2,grouping=True)])
                    self.sum_1+=acum_1
                    self.sum_2+=acum_2
                    acum_1=0.0
                    acum_2=0.0
            lines.append([
                line[0],
                line[1],
                line[2],
                line[3],
                locale.format("%.2f",line[4],grouping=True),
                locale.format("%.2f",line[5],grouping=True)])
            acum_1+=line[4]
            acum_2+=line[5]
            last=line
        
        lines.append([
            last[0],
            last[1],
            '',
            '',
            locale.format("%.2f",acum_1,grouping=True),
            locale.format("%.2f",acum_2,grouping=True)])
        self.sum_1+=acum_1
        self.sum_2+=acum_2
        
        self.sum_1=locale.format("%.2f",self.sum_1,grouping=True)
        self.sum_2=locale.format("%.2f",self.sum_2,grouping=True)
        self.lines=lines
        #for i in lines:
        #    print i
        return lines
        
    def sum(self,m):
        return m==1 and self.sum_1 or self.sum_2

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

report_sxw.report_sxw('report.estadis.product', 'product.product', 'addons/carreras/report/estadis_product.rml',parser=estadis_product)
report_sxw.report_sxw('report.estadis.customer', 'product.product', 'addons/carreras/report/estadis_customer.rml',parser=estadis_customer)
