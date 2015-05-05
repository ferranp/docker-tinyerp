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
  Fa la impressio d'albarans
"""
#
# 16.06.2010 Agafar el %IVA de la primera taxa de la primera línia de la factura
# 27.05.2011 Afegir un dígit més en el número d'albarà
#
import pooler
import time
import locale
import netsvc
import StringIO,os
from tempfile import mkstemp

from report import report_sxw
from printjob import report_raw

locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

class shipping_raw(report_raw):

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return " "

    def add(self,lines,lin,col,text,start='',end='',end_line=False):
        line=list(lines[lin-1])
        ntext=self.convert_raw(text)
        if (col + len(ntext)) > len(line):
            lines[lin-1]=lines[lin-1]+ " "*(col + len(ntext) - len(line))
            line=list(lines[lin-1])
        for i in range(len(ntext)):
            line[col-1+i]=ntext[i]
        for char in reversed(self.get_chars(start)):
            line.insert(col-1,char)
        for char in reversed(self.get_chars(end)):
            line.insert(col+len(self.get_chars(start))+len(text)-1,char)
        if end_line:
            lines[lin-1]=''.join(line[:col+len(self.get_chars(start))+len(text)+len(self.get_chars(end))])
        else:
            lines[lin-1]=''.join(line)

    def add_cap(self,cr,uid,lines,so):
        add=self.add
        #capsalera companyia
        add(lines,1,21,so.company_id.partner_id.name)
        add(lines,2,21,so.company_id.partner_id.address[0].street)
        add(lines,3,21,so.company_id.partner_id.address[0].zip[0:5])
        add(lines,3,27,so.company_id.partner_id.address[0].city)
        add(lines,4,21,"TELEFONO : %-13s" % so.company_id.partner_id.address[0].phone[0:13])
        add(lines,4,46,"FAX : %s" % so.company_id.partner_id.address[0].fax)
        if so.customer_id.name[1:4] == "000":
            add(lines,5,21,"CIF.%s" % so.company_id.partner_id.ref)
        #capsalera client
        addr=so.partner_invoice_id
        add(lines,6,43,so.partner_id.name or '')
        add(lines,7,43,addr.street or '')
        add(lines,8,43,addr.zip and addr.zip[0:5] or '')
        add(lines,8,49,addr.city or '')
        if addr.state_id and addr.state_id.name.upper() != addr.city:
            add(lines,9,43,addr.state_id.name.upper())
        add(lines,12,43,so.partner_id.ref or '')

        #capsalera factura
        if so.customer_id.name[1:4] == "000":
            add(lines,8,26,"FACTURA")
            add(lines,10,26,so.invoice_ids[0].number)

        #capsalera albara
        if len(so.delivery) > 6:
            add(lines,10,1,so.delivery[3:])
        else:
            add(lines,10,1,so.delivery)
        add(lines,10,8,self.format_date(so.date_delivery))
        add(lines,10,19,so.customer_id.name)
        add(lines,12,2,"No.HOJA DE RUTA : %s" % so.name)
        if so.line_type!="RE":
            add(lines,14,4,"FECHA")
            add(lines,14,13,"CONCEPTO")
            add(lines,14,25,"S.REF")
            add(lines,14,55,"PESO")
            add(lines,14,64,"CANT.")
            add(lines,14,74,"PRECIO")
            return
        add(lines,14,4,"TIPO")
        add(lines,14,11,"TRATAMIENTO")
        add(lines,14,30,"LONGI.")
        add(lines,14,42,"DIAM.")
        add(lines,14,49,"MD")
        add(lines,14,53,"CANT.")
        add(lines,14,62,"PRECIO")
        add(lines,14,73,"IMPORTE")
        return

    def lf(self, format, val):
        return locale.format(format ,val, grouping=True)

    def add_line(self,lines,so,i):
        add=self.add
        lf=self.lf
        line=so.order_line[i]
        posy=16 + i%6
        if so.line_type == "RE":
            add(lines,posy,3,line.piece_id.name[0:7])
            add(lines,posy,11,line.product_id.default_code)
            add(lines,posy,14,line.product_id.name)
            add(lines,posy,30,"%6d" % line.length)
            add(lines,posy,42,"%5d" % line.diameter)
            add(lines,posy,50, line.hard_metal and "S" or "N")
            add(lines,posy,53,"%5d" % line.product_uom_qty)
            add(lines,posy,59,lf("%10.3f" ,line.price_unit))
            add(lines,posy,70,lf("%10.2f" ,line.price_subtotal))
            return
        add(lines,posy,2,self.format_date(so.date_order))
        if so.line_type == "TR":
            add(lines,posy,13,"(*) %s" % line.product_id.default_code)
        else:
            add(lines,posy,13,line.name[:10])
        if so.client_order_ref:
            add(lines,posy,25,so.client_order_ref)
        add(lines,posy,52,"%7.3f" % line.kilos or 0)
        if line.price_subtotal < line.price_min and line.price_subtotal >= 0:
            add(lines,posy,64,"%5d" % 1)
            add(lines,posy,70,lf("%10.3f", line.price_min))
        else:
            add(lines,posy,64,"%5d" % line.quantity or 0)
            add(lines,posy,70,lf("%10.3f", line.price_unit))
        return

    def add_peu(self,cr,uid,lines,so):
        add=self.add
        lf=self.lf
        if so.customer_id.name[1:4] != "000":
            #peu albara
            if so.amount_lines < so.amount_minimum and so.amount_lines >= 0:
                add(lines,27,40,"TOTAL ALBARAN MINIMO :")
            else:
                add(lines,27,47,"TOTAL ALBARAN :")
            add(lines,27,68,lf("%12.2f", so.amount_untaxed))
        else:
            #peu factura
            tax=so.invoice_ids[0].invoice_line[0].invoice_line_tax_id[0]
            add(lines,24,46,"BASE IMPONIBLE :")
            add(lines,25,46,"IVA        %2d%% :" % (tax.tax_sign * tax.amount * 100))
            add(lines,27,46,"TOTAL FACTURA  :")
            if so.cash_discount:
                add(lines,23,46,"DESCUENTO  %2d%% :" % so.cash_discount)
            if so.amount_untaxed >= 0:
                #factura
                if so.cash_discount:
                    add(lines,23,63,lf("%12.2f",(so.amount_untaxed * so.cash_discount/100)))
                add(lines,24,63,lf("%12.2f",so.invoice_ids[0].amount_untaxed))
                add(lines,25,63,lf("%12.2f",so.invoice_ids[0].amount_tax))
                add(lines,27,63,lf("%12.2f",so.invoice_ids[0].amount_total))
            else:
                #abonament
                if so.cash_discount:
                    add(lines,23,63,lf("%12.2f",(-so.amount_untaxed * so.cash_discount/100)))
                add(lines,24,63,lf("%12.2f",-so.invoice_ids[0].amount_untaxed))
                add(lines,25,63,lf("%12.2f",-so.invoice_ids[0].amount_tax))
                add(lines,27,63,lf("%12.2f",-so.invoice_ids[0].amount_total))

        if so.line_type != "RE":
            add(lines,28,3,"Material      : %s" % (so.stuff_desc and so.stuff_desc or ''))
            add(lines,29,3,"(*)           : %s" 
                % (so.order_line[0].product_id  and so.order_line[0].product_id.name or ''))

        add(lines,30,3,"OBSERVACIONES :")
        if so.delivery_note:
            for i,line in enumerate(so.delivery_note.splitlines()):
                if i > 2: break
                add(lines,30 + i,19,line)
        if so.customer_id.name[1:4] == "000":
            add(lines,34,3,so.company_id.rml_footer1,'start_compress','end_compress')

    def add_qualitat(self,cr,uid,lines,so):
        self.add_cap(cr,uid,lines,so)
        add=self.add
        add(lines,12,41,"S/REF. : %-20s" % (so.client_order_ref and so.client_order_ref or " "))
        lines[13]=" "*80
        add(lines,14,2," "*80)
        add(lines,14,9,"*** CERTIFICADO DE CALIDAD ***",'start_expand','end_expand',True)
        add(lines,16,3,"TRATAMIENTO EFECTUADO  : %s" 
            % (so.order_line[0].product_id  and so.order_line[0].product_id.name or ''))
        add(lines,17,3,"MATERIAL DE LAS PIEZAS : %s" % (so.stuff_desc and so.stuff_desc or ''))
        add(lines,19,3,"PARAMETROS SOLICITADOS")
        add(lines,20,4,"DUREZA      : %s - %s" % (so.min_req_hardness or "",so.max_req_hardness or ""))
        add(lines,21,4,"PROFUNDIDAD : %s - %s" % (so.min_req_depth or "",so.max_req_depth or ""))
        add(lines,23,3,"PARAMETROS OBTENIDOS")
        add(lines,24,4,"DUREZA      : %s - %s" % (so.min_obt_hardness or "",so.max_obt_hardness or ""))
        add(lines,25,4,"PROFUNDIDAD : %s - %s" % (so.min_obt_depth or "",so.max_obt_depth or ""))
        add(lines,28,3,"OBSERVACIONES :")
        if so.quality_note:
            for i,line in enumerate(so.quality_note.splitlines()):
                if i > 2: break
                add(lines,28 + i,18,line)
        add(lines,32,3,"DECISION      : CONFORME / Responsable : %s (Dpto. Calidad)"
            % (so.shop_id.quality_charge and so.shop_id.quality_charge.name or ''))

    def print_so(self,cr,uid,so):
        logger = netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,"printing sale_order %s ..." % so.delivery or " ")
        lines=[" "*80] * 36
        npag=0
        acum=0
        for i,line in enumerate(so.order_line):
            if i%6 == 0:
                if npag != 0:
                    self.add(lines,22,30,"SUMA Y SIGUE")
                    self.add(lines,22,68,self.lf("%12.2f", acum))
                    self.print_page(lines)
                npag +=1
                lines=[" "*80] * 36
                self.add_cap(cr,uid,lines,so)
            self.add_line(lines,so,i)
            acum += line.price_subtotal

        self.add_peu(cr,uid,lines,so)
        self.print_page(lines)

        lines=[" "*80] * 36
        self.add_qualitat(cr,uid,lines,so)
        self.print_page(lines)
        return

    def print_page(self,lines):
        #logger = netsvc.Logger()
        #logger.notifyChannel("info", netsvc.LOG_INFO,"********************")
        #for i,line in enumerate(lines):
        #    logger.notifyChannel("info", netsvc.LOG_INFO,"%02d %s %02d" % (i,line,i))
        #return
        if self.pdf:
            self.raw.write("<pre>")
            for line in lines[:-2]:
                self.write_raw(line+"\n")
            self.raw.write("</pre><!-- NEW PAGE -->")
        else:
            for line in lines:
                self.write_raw(line+"\n")

    def create_raw(self, cr, uid, ids, datas, context=None):
        #if 'bpf' == self.pool.get('res.users').browse(cr,uid,uid).login:
        #    self.set_printer('panasonic')
        self.pdf = 'pdf' == self.pool.get('res.users').browse(cr,uid,uid).raw_printer.system_name
        if self.pdf:
          self.set_printer('pdf')
        else:
          self.set_printer('epson')
        for so in self.pool.get('sale.order').browse(cr,uid,ids,context):
            self.print_so(cr,uid,so)

    def create(self, cr, uid, ids, datas, context=None):
        self.printers['pdf']={
          'start': '',
          'end': '',
          'start_compress': '<small>',
          'end_compress': '</small>',
          'start_expand': '<b>',
          'end_expand': '</b>',
          '': '',
        }
        logger = netsvc.Logger()
        if not context:
            context={}
        self.raw = StringIO.StringIO()
        self.pool=pooler.get_pool(cr.dbname)
        self.create_raw(cr, uid, ids, datas, context)
        raw = self.raw.getvalue()
        if not self.pdf:
            return (raw, 'raw')

        tmpfile=mkstemp()
        html = "<html><body>" + raw + "</body></html>"
        os.write(tmpfile[0],html)
        cmd='htmldoc --webpage --bodyimage addons/carreras/report/Albara3.jpg -f '+ tmpfile[1] + ".pdf --fontspacing 1 --size 220x160mm --footer '...' --top -8mm --left 6mm --fontsize 14.2 "+ tmpfile[1]
   
        logger.notifyChannel("info", netsvc.LOG_INFO, tmpfile[1])
        logger.notifyChannel("info", netsvc.LOG_INFO, cmd)
        os.system(cmd)
        return (open(tmpfile[1]+'.pdf').read(),'pdf')

shipping_raw('report.sale.order.print_raw','raw')

class shipping_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(shipping_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'format_date': self.format_date,
            'get_line': self.get_line,
            'pages':self.pages,
            'lines_tr':self.lines_tr,
            'lines_re':self.lines_re,
            'lines_va':self.lines_va,
        })
        self.lines_per_page = 6

    def preprocess(self, objects, data, ids):
        super(shipping_report, self).preprocess(objects, data, ids)

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_line(self,s,line):
        if not s:
            return ""
        ss = s.split('\n')
        if len(ss) > line:
            return ss[line]
        return ""
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)
        
    def pages(self,o):
        num = len(o.order_line)
        return (num / (self.lines_per_page + 1)) + 1
        
    def lines_tr(self,o,pag):
        ini = pag * self.lines_per_page
        lines = []
        for line in o.order_line[ini:ini+self.lines_per_page]:
            s = [
                self.format_date(o.date_delivery) or ' ',
                '(*) %s' %  line.product_id.default_code or ' ',
                o.client_order_ref or ' ',
                line.kilos and str(line.kilos) or "0" ,
                line.quantity and str(line.quantity) or "0",
                self.numf(line.price_subtotal),
            ]
            lines.append(s)
            
        while len(lines) < self.lines_per_page:
            lines.append((" ",)*6)
        return lines

    def lines_re(self,o,pag):
        ini = pag * self.lines_per_page
        lines = []
        for line in o.order_line[ini:ini+self.lines_per_page]:
            s = [
                line.piece_id.name[:8],
                line.product_id.name[:20],
                str(line.length),
                str(line.diameter),
                line.hard_metal and 'S' or 'N',
                str(line.product_uom_qty),
                self.numf(line.price_unit),
                self.numf(line.price_subtotal),
            ]
            lines.append(s)
            
        while len(lines) < self.lines_per_page:
            lines.append((" ",)*8)
        return lines

    def lines_va(self,o,pag):
        ini = pag * self.lines_per_page
        lines = []
        for line in o.order_line[ini:ini+self.lines_per_page]:
            s = [
                self.format_date(o.date_delivery) or ' ',
                line.name[0:10] or ' ' ,
                o.client_order_ref or ' ',
                line.kilos and str(line.kilos) or "0" ,
                line.quantity and str(line.quantity) or "0",
                self.numf(line.price_subtotal),
            ]
            lines.append(s)
            
        while len(lines) < self.lines_per_page:
            lines.append((" ",)*6)
        return lines

    # Posar menys espai entre les línies de la taula "Detall"
    # Altura de la taula = size
    # Files de la taula = table_rows
    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        size=100.0
        table_rows=8
        rowSize=round(float(size/table_rows),2)
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                RowHeights=((str(rowSize) + ",") * table_rows)[:-1]
                elem.setAttribute("rowHeights",RowHeights)
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Totals":
                RowHeights=((str(rowSize) + ",") * 4)[:-1]
                elem.setAttribute("rowHeights",RowHeights)
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Qualitat":
                RowHeights=((str(rowSize) + ",") * 8)[:-1]
                elem.setAttribute("rowHeights",RowHeights)
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.sale.order.shipping', 'sale.order', 'addons/carreras/report/shipping.rml'
            ,parser=shipping_report,header=False)
report_sxw.report_sxw('report.sale.order.shipping_re', 'sale.order', 'addons/carreras/report/shipping_re.rml'
            ,parser=shipping_report,header=False)
report_sxw.report_sxw('report.sale.order.shipping_va', 'sale.order', 'addons/carreras/report/shipping_va.rml'
            ,parser=shipping_report,header=False)
            
report_sxw.report_sxw('report.sale.order.cash', 'sale.order', 'addons/carreras/report/cash.rml'
            ,parser=shipping_report,header=False)
report_sxw.report_sxw('report.sale.order.cash_re', 'sale.order', 'addons/carreras/report/cash_re.rml'
            ,parser=shipping_report,header=False)
report_sxw.report_sxw('report.sale.order.cash_va', 'sale.order', 'addons/carreras/report/cash_va.rml'
            ,parser=shipping_report,header=False)

report_sxw.report_sxw('report.sale.order.shipping_quality', 'sale.order', 'addons/carreras/report/shipping_quality.rml'
            ,parser=shipping_report,header=False)
