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

import time
from report import report_sxw
import locale
import netsvc
import xml.dom.minidom

locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

class account_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_invoice, self).__init__(cr, uid, name, context)
        self.logger = netsvc.Logger()
        self.lines_per_page = 28
        self.localcontext.update({
            'time': time,
            'numf': self.numf,
            'format_date': self.format_date,
            'format_date2': self.format_date2,
            'shippings': self.shippings,
            'amount_sum':self.amount_sum,
            'amount_finance':self.amount_finance,
            'per_finance':self.per_finance,
            'per_tax':self.per_tax,
            'amount_base':self.amount_base,
            'amount_discount':self.amount_discount,
            'per_discount':self.per_discount,
            'pages':self.pages,
            'addr':self.addr,
            'copies':self.copies,
            'get_units':self.get_units,
            'get_price':self.get_price,
            'get_text':self.get_text,
            'get_type_name':self.get_type_name,
            'get_obs':self.get_obs,
        })

    def preprocess(self, objects, data, ids):
        super(account_invoice, self).preprocess(objects, data, ids)
        
    def get_units(self,s):
        if not s:
            return ''
        if s.line_type == 'RE':
            return '1,00'
        if s.amount_minimum == s.amount_untaxed:
            return 1
        else:
            return s.order_line[0].product_uom_qty

    def get_price(self,s):
        if not s:
            return ''
        if s.line_type == 'RE':
            return s.amount_untaxed
        if s.amount_minimum == s.amount_untaxed:
            return s.amount_untaxed
        else:
            return s.order_line[0].price_unit
        
    def get_text(self,s):
        if not s:
            return ' '
        if s.line_type == 'RE':
            return 'RECUBRIMIENTOS'
        elif s.line_type == 'TR':
            return s.order_line[0].product_id.name
        else:
            return s.order_line[0].name

    def get_type_name(self,o):
        if not o.payment_term:
            return ' '
        sql = "select name from account_payment_term_type where "+\
              " code='%s'" % o.payment_term.type
        self.cr.execute(sql)
        name=self.cr.fetchone()
        return name and name[0] or ' '

    def get_obs(self,o, line):
        obs=self.datas.get('form',{}).get('obs')
        obs=obs and obs.split('\n') or []
        return len(obs) > line and obs[line] or ' '

    def copies(self,inv):
        if self.datas.get('form',{}).get('original'):
            c = ['ORIGINAL']
            if inv.partner_id.customer_ids:
                copies = inv.partner_id.customer_ids[0].invoice_copies
                if copies > 1:
                    for i in range(copies - 1):
                        c.append('COPIA')
            return c
        return ['COPIA']

    def addr(self,inv):
        if not (inv.address_invoice_id and inv.address_contact_id):
            return False
        if inv.address_invoice_id == inv.address_contact_id:
            return False
        return inv.address_contact_id

    def pages(self,o):
        sql = "select count(order_id) from sale_order_invoice_rel where "+\
              " invoice_id='%d'" % o.id
        self.cr.execute(sql)
        orders = self.cr.fetchone()[0]
        pages,remainder = divmod(orders,self.lines_per_page)
        if remainder > 0 or pages == 0:
            pages = pages + 1
        return pages
        
    def amount_sum(self,o):
        sum = 0.0
        sql = "select order_id from sale_order_invoice_rel where "+\
              " invoice_id='%d' order by order_id" % o.id
        self.cr.execute(sql)
        ids = [ x[0] for x in self.cr.fetchall() ] 
        for order in self.pool.get('sale.order').browse(self.cr,self.uid,ids):
            sum = sum + order.amount_untaxed
        return self.numf(sum)

    def amount_base(self,o):
        sum = 0
        for tax in o.tax_line:
            sum = sum + tax.base
        #return o.type=='out_invoice' and self.numf(sum) or self.numf(-sum)
        return self.numf(sum)
            

    def amount_discount(self,o):
        sum = 0
        for line in o.invoice_line:
            if line.account_id.code == '66500':
                sum = sum + line.price_subtotal
        if sum:
            return self.numf(sum)
            #return o.type=='out_invoice' and self.numf(sum) or self.numf(-sum)
        return ""

    def per_discount(self,o):
        sum = 0
        for line in o.invoice_line:
            if line.account_id.code == '66500':
                sum = sum - line.price_subtotal
        if sum:
            return o.partner_id.customer_ids[0].discount_inv
        return ""

    def amount_finance(self,o):
        sum = 0
        for line in o.invoice_line:
            if line.account_id.code == '76900':
                sum = sum + line.price_subtotal
        if sum:
            return self.numf(sum)
        return ""

    def per_finance(self,o):
        sum = 0
        for line in o.invoice_line:
            if line.account_id.code == '76900':
                sum = sum - line.price_subtotal
        if sum and o.partner_id.customer_ids[0].financing_cost:
            return o.partner_id.customer_ids[0].financing_cost.percentage
        return ""

    def per_tax(self,o):
        if o.invoice_line:
          if o.invoice_line[0].invoice_line_tax_id:
            return locale.format("%d",o.invoice_line[0].invoice_line_tax_id[0].amount * 100)
        return 0

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def format_date2(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '/' + date1[1] 
        else:
            return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
        
    def shippings(self,inv,page=0):
        self.logger.notifyChannel("info", netsvc.LOG_INFO,"printing invoice %s %d" % (inv.number,page))
        sql = "select order_id from sale_order_invoice_rel where "+\
              " invoice_id=%d order by order_id" % inv.id
        self.cr.execute(sql)
        ids = [x[0] for x in self.cr.fetchall()] 

        lines=[]
        for so in self.pool.get('sale.order').browse(self.cr,self.uid,ids):
            if so.line_type == 'RE':
                line=[]
                line.append(self.format_date2(so.date_delivery))
                line.append(so.delivery)
                line.append('RECUBRIMIENTOS')
                line.append(so.client_order_ref or '')
                line.append("%.2f" % 1)
                line.append("%.3f" % so.amount_untaxed)
                line.append("%.2f" % so.amount_untaxed)
                lines.append(line)
            else:
                for sol in so.order_line:
                    line=[]
                    line.append(self.format_date2(so.date_delivery))
                    line.append(so.delivery)
                    if so.line_type == 'TR':
                        line.append(sol.product_id.name)
                    else:
                        line.append(sol.name)
                    line.append(so.client_order_ref or '')
                    if so.line_type == 'TR' and so.amount_minimum == so.amount_untaxed:
                        line.append("%.2f" % 1)
                        line.append("%.3f" % (so.amount_untaxed/len(so.order_line)))
                        line.append("%.2f" % (so.amount_untaxed/len(so.order_line)))
                    else:
                        line.append("%.2f" % sol.product_uom_qty)
                        line.append("%.3f" % sol.price_unit)
                        line.append("%.2f" % sol.price_subtotal)
                    lines.append(line)
        
        ini = page * self.lines_per_page
        end = min(ini + self.lines_per_page ,len(lines))
        rlines = lines[ini:end]
        
        if len(rlines) < self.lines_per_page:
            for i in range(self.lines_per_page - len(rlines)):
                rlines.append(None)
        return rlines

    def _add_header(self, node):
        #rml_head = tools.file_open('custom/corporate_rml_header.rml').read()
        #<frame id="first" x1="0.0" y1="0.0" width="595" height="842"/>
        header = """ 
        <header>
        <pageTemplate>
            <frame id="first" x1="0.0" y1="0.0" width="595" height="842"/>
            <pageGraphics>
                <image x="4mm" y="5mm" 
                file="addons/carreras/report/fondo_fac.png" 
                height="288mm" width="200mm"/>
            </pageGraphics>
        </pageTemplate>
        </header>
        """ 
        head_dom = xml.dom.minidom.parseString(header)
        node2 = head_dom.documentElement
        for tag in node2.childNodes:
            if tag.nodeType==tag.ELEMENT_NODE:
                found = self._find_node(node, tag.localName)
        #		rml_frames = found.getElementsByTagName('frame')
                if found:
                    if tag.hasAttribute('position') and (tag.getAttribute('position')=='inside'):
                        found.appendChild(tag)
                    else:
                        found.parentNode.replaceChild(tag, found)
        #		for frame in rml_frames:
        #			tag.appendChild(frame)
        return True

    # Posar menys espai entre les linies de la taula "Albarans"
    # Altura de la taula = 350
    # Linies de la taula = self.lines_per_page
    def _parse(self, rml_dom, objects, data, header=False):
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,"parsing invoice  ...")
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        #self.node_context = {}
        #self.dom = rml_dom
        size=350.0
        rowSize=round(float(size/self.lines_per_page),2)
        rowHeights=((str(rowSize) + ",") * self.lines_per_page)[:-1]
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Albarans":
                elem.setAttribute("rowHeights",rowHeights)
        res = self.dom.documentElement.toxml('utf-8')
        return res

class account_invoice_copia(account_invoice):

    def copies(self,inv):
        return ['COPIA']

class account_invoice_original(account_invoice):

    def copies(self,inv):
        return ['ORIGINAL']

report_sxw.report_sxw('report.account.customer_invoice', 'account.invoice', 'addons/carreras/report/invoice.rml'\
        ,header=True, parser=account_invoice)
report_sxw.report_sxw('report.account.customer_invoice_copia', 'account.invoice', 'addons/carreras/report/invoice.rml'\
        ,header=True, parser=account_invoice_copia)
report_sxw.report_sxw('report.account.customer_invoice_original', 'account.invoice', 'addons/carreras/report/invoice.rml'\
        ,header=True, parser=account_invoice_original)

#report_sxw.rml_parse
