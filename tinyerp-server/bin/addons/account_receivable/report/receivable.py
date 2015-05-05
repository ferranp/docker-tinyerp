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
  Llista un efecte
"""
import pooler
import time
from printjob import report_raw

unitats={
    0:'',
    1:'UN',
    2:'DOS',
    3:'TRES',
    4:'CUATRO',
    5:'CINCO',
    6:'SEIS',
    7:'SIETE',
    8:'OCHO',
    9:'NUEVE',
    10:'DIEZ',
    11:'ONCE',
    12:'DOCE',
    13:'TRECE',
    14:'CATORCE',
    15:'QUINCE',
    16:'DIECISEIS',
    17:'DIECISIETE',
    18:'DIECIOCHO',
    19:'DIECINUEVE',
    }
desenes={
    1:'DIEZ',
    2:'VEINTE',
    3:'TREINTA',
    4:'CUARENTA',
    5:'CINCUENTA',
    6:'SESENTA',
    7:'SETENTA',
    8:'OCHENTA',
    9:'NOVENTA',
    }
centenes={
    0:'',
    1:'CIEN',
    2:'DOSCIENTOS',
    3:'TRESCIENTOS',
    4:'CUATROCIENTOS',
    5:'QUINIENTOS',
    6:'SEISCIENTOS',
    7:'SETECIENTOS',
    8:'OCHOCIENTOS',
    9:'NOVECIENTOS',
    }
milers={
    0:'',1:'MIL',
}

def _100_to_text_es(xifra):
    if xifra in unitats:
        return unitats[xifra]
    else:
        if xifra%10>0:
            return desenes[xifra / 10]+' Y '+ unitats[xifra % 10]
        else:
            return desenes[xifra / 10]

def _1000_to_text_es(xifra):
    d = _100_to_text_es(xifra % 100)
    d2 = xifra/100
    if d2>0:
        return centenes[d2]+' '+d
    else:
        return d

def _10000_to_text_es(xifra):
    if xifra==0:
        return 'CERO'
    part1 = _1000_to_text_es(xifra % 1000)
    part2 = milers.get(xifra / 1000,  _1000_to_text_es(xifra / 1000)+' MIL')
    if part2 and part1:
        part1 = ' '+part1
    return part2+part1

def amount_to_text_es(number, currency):
    units_number = int(number)
    units_name = currency
    if units_number > 1:
        units_name += 's'
    units = _10000_to_text_es(units_number)
    units = units_number and '%s %s' % (units, units_name) or ''

    cents_number = int(number * 100) % 100
    cents_name = (cents_number > 1) and 'Cts.' or 'Ct.'
    cents = _100_to_text_es(cents_number)
    cents = cents_number and '%s %s' % (cents, cents_name) or ''

    if units and cents:
        cents = ' con '+cents
        
    return units + cents

class receivable(report_raw):

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return " "
    
    def add(self,lines,lin,col,text,start='',end=''):
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
        lines[lin-1]=''.join(line)

    def print_rec(self,cr,uid,rec):
        c=self.convert_raw
        ccc=rec.bank_id and rec.bank_id.acc_number.replace("-",'').replace('.','') or ''
        ccc=ccc.ljust(20,' ')

        #prn("123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789\n")
        res=self.pool.get('res.partner').address_get(cr, uid, [rec.company_id.partner_id.id], ['invoice'])
        id= 'invoice' in res and res['invoice'] or res['default']
        caddr= self.pool.get('res.partner.address').browse(cr,uid,id)

        res=self.pool.get('res.partner').address_get(cr, uid, [rec.partner_id.id], ['contact'])
        id= 'contact' in res and res['contact'] or res['default']
        paddr= id and self.pool.get('res.partner.address').browse(cr,uid,id) or None
        street= paddr and paddr.street or ' '
        zip= paddr and paddr.zip or  ' '
        city= paddr and paddr.city or ' '
        prov= paddr and (paddr.state_id and paddr.state_id.name or ' ') or ' '
        prov=prov.upper()
        if prov == city:
            prov = ' '
        
        add=self.add
        lines=[" "*80] * 24
        
        add(lines,1,1,"              %-10s           %-20s %-17s 1/1  " % 
            (c(rec.name),"SABADELL","//*%.2f//" % rec.amount))
        add(lines,3,1,"                           %-10s                 %-10s        %s" %
            (self.format_date(rec.date),self.format_date(rec.date_maturity),self.types[rec.type]))
        
        amount_text=amount_to_text_es(rec.amount,"Euro").ljust(90,'=')
        add(lines,6,1,"                         %-45s" % amount_text[0:45])
        add(lines,7,1,"                         %-45s" % amount_text[45:])
        
        if rec.type not in ['reposicio']:
            add(lines,9,1,"                      %-37s %s" % (rec.bank_id and c(rec.bank_id.name),ccc[0:4]))
            add(lines,10,1,"                      %-37s %s   %s %s" % (rec.bank_id and rec.bank_id.street and c(rec.bank_id.street),ccc[4:8],ccc[8:9],ccc[9:10]))
            add(lines,11,1,"                      %-37s %s" % (rec.bank_id and rec.bank_id.city and c(rec.bank_id.city),ccc[10:20]))
        
        add(lines,13,1,"                                   %s" % rec.partner_id.code)
        
        add(lines,14,1,"              %-35s" % rec.partner_id.name.decode('utf8')[0:35])
        add(lines,15,1,"              %-35s" % street.decode('utf8')[0:35])
        add(lines,16,1,"              %-5s %-30s" % (zip,city.decode('utf8')[0:30]))
        add(lines,17,1,"                    %-30s" % prov)
        
        add(lines,14,55,rec.company_id.name,'start_compress','end_compress')
        add(lines,15,55,caddr.street,'start_compress','end_compress')
        add(lines,16,55,"%5s %s" % (caddr.zip,caddr.city),'start_compress','end_compress')
        add(lines,17,55,rec.company_id.partner_id.ref,'start_compress','end_compress')
        
        self.print_page(lines)
        return

    def print_page(self,lines):
        #print "************** Imprimir"
        #for i,line in enumerate(lines):
        #    print "%02d" % i,line
        for line in lines:
            self.write_raw(line+"\n")

    def create_raw(self, cr, uid, ids, datas, context=None):
        self.pool=pooler.get_pool(cr.dbname)
        if 'bpf' == self.pool.get('res.users').browse(cr,uid,uid).login:
            self.set_printer('panasonic')
        type_obj=self.pool.get('account.payment.term.type')
        type_ids=type_obj.search(cr,uid,[])
        self.types=dict([(type.code,type.name) for type in type_obj.browse(cr,uid,type_ids)])
        
        rec_obj = self.pool.get('account.receivable')
        for rec in rec_obj.browse(cr,uid,ids,context):
            self.print_rec(cr,uid,rec)
            
receivable('report.print.receivable','raw')


