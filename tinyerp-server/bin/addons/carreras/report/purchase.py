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
import xml.dom.minidom


locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

class purchase_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(purchase_order, self).__init__(cr, uid, name, context)
        self.lines_per_page = 28
        self.localcontext.update({
            'time': time,
            'numf': self.numf,
            'format_date': self.format_date,
            'lines': self.lines,
            'pages':self.pages,
            'get_line': self.get_line,
            'get_address': self.get_address,
        })

    def preprocess(self, objects, data, ids):
        super(purchase_order, self).preprocess(objects, data, ids)

    def get_line(self,s,line):
        if not s:
            return ""
        ss = s.split('\n')
        if len(ss) > line:
            return ss[line]
        return ""

    def get_address(self,o,field):
        if not o.destination:
            return False
        if not o.destination.address:
            return False
        return eval('o.destination.address.' + field)

    def pages(self,o):
        sql = "select count(order_id) from sale_order_invoice_rel where "+\
              " invoice_id='%d'" % o.id
        self.cr.execute(sql)
        orders = self.cr.fetchone()[0]
        pages,remainder = divmod(orders,self.lines_per_page)
        if remainder > 0 or pages == 0:
            pages = pages + 1
        return pages

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '/' + date1[1] + '/' + date1[0]
        else:
            return ""

    def pages(self,o):
        sql = "select count(id) from purchase_order_line where "+\
              " order_id='%d'" % o.id
        self.cr.execute(sql)
        orders = self.cr.fetchone()[0]
        pages,remainder = divmod(orders,self.lines_per_page)
        if remainder > 0 or pages == 0:
            pages = pages + 1
        return pages

    def numf(self,val):
        return val and locale.format("%0.2f",val,grouping=True) or ''
        
    def lines(self,p,page=0):
        lines=[]
        suma=0
        for l in p.order_line:
            suma+= l.price_subtotal
            lines.append([
                    l.product_id.variants,
                    l.product_id.code,
                    l.product_id.name,
                    self.numf(l.product_qty),
                    self.numf(l.price_unit),
                    self.numf(l.discount),
                    self.numf(l.price_subtotal),
                    ])
        
        ini = page * self.lines_per_page
        end = min(ini + self.lines_per_page ,len(lines))
        rlines = lines[ini:end]
        if len(rlines) < self.lines_per_page:
            for i in range(self.lines_per_page - len(rlines)):
                rlines.append(None)
        return rlines

    # Posar menys espai entre les linies de la taula "Titol"
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        size=350.0
        rowSize=round(float(size/self.lines_per_page),2)
        rowHeights=((str(rowSize) + ",") * self.lines_per_page)[:-1]
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Titol2":
                elem.setAttribute("rowHeights","15,15")
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Titol":
                elem.setAttribute("rowHeights","20")
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Capsalera":
                elem.setAttribute("rowHeights","11.5,11.5,11.5")
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Banc":
                elem.setAttribute("rowHeights","11.5,11.5,11.5")
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Peu":
                elem.setAttribute("rowHeights","13.5,13.5,13.5")
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
        res = self.dom.documentElement.toxml('utf-8')
        return res
    

report_sxw.report_sxw('report.purchase.supplier_order', 'purchase.order', 'addons/carreras/report/purchase.rml'\
        ,header=False, parser=purchase_order)

#report_sxw.rml_parse