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

  Carrega de fulls de ruta i albarans

"""
import time
import wizard
import pooler 
import netsvc
from glob import glob

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de fulls de ruta i albarans">
    <label string="Carrega de fulls de ruta i albarans" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

_tax={}    
def _load_tax(cr,uid):
    cr.execute("select id,code,company_id from account_tax ")
    for c in cr.fetchall():
        _tax[(c[1].strip(),c[2])] = c[0]

def get_partner(cr,uid,cust):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get("res.partner.customer").search(cr,uid,[('name','=',cust)])
    if ids:
        c = pool.get("res.partner.customer").browse(cr,uid,ids[0])
        return c.partner_id
    else:
        return False

def get_art(cr,uid,art):
    pool = pooler.get_pool(cr.dbname)
    s = [('default_code','=',art)]
    art_id = pool.get('product.product').search(cr,uid,s)
    if art_id:
        return art_id[0]
    return False

class wizard_load_order(wizard.interface):

    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load_order(self, lin, cr, uid, data, context):
        if lin[0][0][0][1:3] not in ("TT","TC","BD"):
            return

        if lin[0][0][3]=='1':
            name=lin[0][0][4]
        elif lin[0][0][3]=='2':
            if lin[0][1][21] == "":
                name = 'Albara ' + lin[0][0][4]
            else:
                name = lin[0][1][21]
        else:
            print "Tipus de registre desconegut >",lin[0][0]
            return

        self.numero_albarans = self.numero_albarans + 1
        #if self.numero_albarans > 100:
        #if lin[0][0][4] not in ("8931","8928","635917","620724") and self.numero_albarans > 100:
        #if lin[0][0][4] not in ("8931","8928","635917","620724"):
        #    return

        #if lin[0][1][37] != "TL":
        #    return
        #if self.numero_albarans_facturats > 10:
        #    return
        #print "<",name,">","<",lin[0][0][4],">","<",lin[0][1][37],">",lin[1][0][5][2:3]

        if lin[0][0][0][1:3] == "TT":
            if lin[0][1][38] == "1":
                shop_id = self.shop_id["TT1"]
            elif lin[0][1][38] == "2":
                shop_id = self.shop_id["TT2"]
            elif lin[0][1][38] == "3":
                shop_id = self.shop_id["TT3"]
            else:
                print name,"> Centre desconegut <",lin[0][1][38],"> s'assigna Sabadell"
                shop_id = self.shop_id["TT1"]
        elif lin[0][0][0][1:3] == "TC":
            shop_id = self.shop_id["TC"]
        elif lin[0][0][0][1:3] == "BD":
            shop_id = self.shop_id["BD"]
        else:
            return
            
        company_id = get_company(cr,uid,lin[0][1][37])

        o={}
        o['name']=name
        o['company_id']=company_id
        o['shop_id']=shop_id
        o['pricelist_id']=self.pool.get('product.pricelist').search(cr,uid,[('name','=','Default Sale Pricelist')])[0]

        ids = self.pool.get("res.partner.customer").search(cr,uid,[('name','=',lin[0][0][2])])
        if not ids:
            print name,"> Client",lin[0][0][2],"no trobat"
            return

        o['customer_id'] = ids[0]
        customer_obj = self.pool.get("res.partner.customer").browse(cr,uid,o['customer_id'])
        partner_obj = customer_obj.partner_id
        #partner=get_partner(cr,uid,int(lin[0][0][2]))
        o['partner_id']=partner_obj.id
        o['partner_order_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['contact'])['contact']
        o['partner_invoice_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['invoice'])['invoice']
        o['partner_shipping_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['delivery'])['delivery']
        if not o['partner_order_id'] or not o['partner_invoice_id'] or not o['partner_shipping_id']:
            print 'partner_order_id',o['partner_order_id']
            print 'partner_invoice_id',o['partner_invoice_id']
            print 'partner_shipping_id',o['partner_shipping_id']
            return
        
            
        o['stuff_desc']=lin[0][1][33]
        o['delivery_note']=lin[0][1][34] + "\n" + lin[0][1][35]
        o['client_order_ref']=lin[0][1][11]
        
        line_type=lin[1][0][5][2:3]
        if line_type == "7":
            return
        if line_type not in self.line_type:
            print name,"> Tipus de linia desconegut",lin[1][0][5]
            return
        o['line_type']=self.line_type[line_type]
        #print o

        invoice_line_ids=False

        state='draft'

        o['date_order']=lin[0][1][0][0:4]+"-"+lin[0][1][0][4:6]+"-"+lin[0][1][0][6:8]
        if lin[0][0][3]!='1':
            state='router'
            self.n1=self.n1+1

            o['delivery']=lin[0][0][4]
            o['date_delivery']=lin[0][1][0][0:4]+"-"+lin[0][1][0][4:6]+"-"+lin[0][1][0][6:8]
            o['min_req_hardness']='.'
            o['max_req_hardness']='.'
            o['min_req_depth']='.'
            o['max_req_depth']='.'
            o['min_obt_hardness']='.'
            o['max_obt_hardness']='.'
            o['min_obt_depth']='.'
            o['max_obt_depth']='.'

            if len(lin[0][1][2]) > 0:
                #print lin[0][1][2]
                #print lin[0][1][2]
                try:
                    if lin[0][0][2][1:4]=="000":
                        if lin[0][1][37] == "TL":
                            num_fac="2"+'-'+str(int(lin[0][1][2][1:]))
                        elif lin[0][1][37] == "TJ":
                            num_fac="3"+'-'+str(int(lin[0][1][2][1:]))
                        else:
                            num_fac="1"+'-'+str(int(lin[0][1][2][1:]))
                    else:
                        if lin[0][1][37] == "TJ":
                            num_fac="1"+'-'+str(int(lin[0][1][2][1:]))
                        else:
                            num_fac="0"+'-'+str(int(lin[0][1][2]))
                except ValueError:
                    print "value error",lin[0][1]
                    return
                #print serie,'-',lin[0][1][2]
                #if lin[0][1][37] == "TL":
                #elif lin[0][1][37] == "TJ":
                #elif lin[0][1][37] == "TC":
                #elif lin[0][1][37] == "BD":
                date_min=o['date_delivery'][0:4]+'-01-01'
                date_max=o['date_delivery'][0:4]+'-12-31'
                s=[('name','=',num_fac),('date_invoice','>=',date_min),('date_invoice','<=',date_max),('company_id','=',company_id)]
                invoice_ids = self.pool.get('account.invoice').search(cr,uid,s)
                state="done"
                if len(invoice_ids) > 1:
                    print "********** <",name,"> <",lin[0][0][4],"> <",lin[0][1][37],"> <",lin[1][0][5][2:3],"> <",num_fac,">",lin[0][1][2],lin[0][0][2],invoice_ids
                    invoice_line_ids = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',invoice_ids[0])])
                elif len(invoice_ids) == 1:
                    o['invoice_ids']=[(6,0,invoice_ids)]
                    invoice_line_ids = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',invoice_ids[0])])
                    #print "<",name,"> < albara",lin[0][0][4],"> < full de ruta",lin[0][1][37],"> < tipus",lin[1][0][5][2:3],"> <",num_fac,">"
                    #print "<",name,"> <",lin[0][0][4],"> <",lin[0][1][37],"> <",lin[1][0][5][2:3],"> <",num_fac,">",lin[0][1][2],lin[0][0][2]
                else:
                    print "XXXXXXXXX <",name,"> < albara",lin[0][0][4],"> <",lin[0][1][37],"> < tipus",lin[1][0][5][2:3],">"
                    #return
            else:
                #print "sense factura <",name,"> <",lin[0][0][4],"> <",lin[0][1][37],"> < tipus",lin[1][0][5][2:3],">"
                self.n2=self.n2+1
                #return

        void = self.pool.get('sale.order').search(cr,uid,[('name','=',name),('company_id','=',company_id)])

        if void:
            oid=void[0]
            self.pool.get('sale.order').write(cr,uid,oid,o)
        else:
            oid = self.pool.get('sale.order').create(cr,uid,o)

        for i in range(1,len(lin)):
            #print "<",i,",",line_type,">",lin[i]
            #print line_type
            l= self._load_line[line_type](o['company_id'],lin[i][1], cr, uid, data, context)
            if not l:
                print lin
                continue
            l['line_type']=line_type
            l['order_id']=oid
            if 'name' not in l:
                l['name']=str(i*10)
            l['sequence']=str(i*10)
            l['pricelist_partner_id']=False
            if invoice_line_ids:
                l['invoice_lines']=[(6,0,invoice_line_ids)]
            vlid = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',oid),('sequence','=',lin[i][0][5][0:2])])
            if vlid:
                lid=vlid[0]
                self.pool.get('sale.order.line').write(cr,uid,lid,l)
            else:
                lid = self.pool.get('sale.order.line').create(cr,uid,l,context={})

        if state=='router':
            wf_service = netsvc.LocalService('workflow')
            try:
                wf_service.trg_validate(uid, 'sale.order', oid, 'order_confirm', cr)
            except:
                pass

        return

    def _load_TR(self, company_id, lin, cr, uid, data, context):
        l={}
        l['product_uom']=self.kgm_id
        product_id=get_art(cr,uid,lin[0].strip())
        if not product_id:
            print 'producte',lin[0],'no trobat'
            return False
        l['product_id']=product_id
        product_obj=self.pool.get('product.template').browse(cr,uid,product_id)
        for tax in product_obj.taxes_id:
            if tax.company_id.id == company_id:
                break
        l['tax_id']=[ (6,0,[tax.id]) ]
        l['depth']=int(lin[1])
        #l['price_net']=float(lin[2])
        l['price_unit']=float(lin[6])
        l['product_uom_qty']=float(lin[7])
        l['kilos']=float(lin[7])
        l['quantity']=float(lin[5])
        return l

    def _load_RE(self, company_id, lin, cr, uid, data, context):
        l={}
        l['product_uom']=self.unit_id
        product_id=get_art(cr,uid,lin[0].strip())
        if not product_id:
            print 'producte',lin[0],'no trobat'
            return False
        l['product_id']=product_id
        product_obj=self.pool.get('product.template').browse(cr,uid,product_id)
        for tax in product_obj.taxes_id:
            if tax.company_id.id == company_id:
                break
        l['tax_id']=[ (6,0,[tax.id]) ]
        l['length']=int(lin[1])
        #l['price_net']=float(lin[2])
        l['diameter']=int(lin[3])
        l['piece_id']=self.pool.get('pricelist.piece').search(cr,uid,[('code','=',lin[4])])[0]
        l['product_uom_qty']=float(lin[5])
        l['price_unit']=float(lin[6])
        l['kilos']=1.0
        l['quantity']=float(lin[5])
        
        return l

    def _load_VA(self, company_id, lin, cr, uid, data, context):
        l={}
        l['product_uom']=self.unit_id
        l['name']=lin[1]
        l['price_unit']=1
        l['price_net']=float(lin[2])
        l['product_uom_qty']=float(lin[5])
        l['kilos']=float(lin[5])
        l['quantity']=float(lin[5])
        l['product_id']=False
        return l

    def _load(self, cr, uid, data, context):
        self._load_line={"2":self._load_TR,"3":self._load_RE,"7":self._load_VA}
        self.line_type={"2":"TR","3":"RE","7":"VA"}
        self.kgm_id=self.pool.get('product.uom').search(cr,uid,[('name','=','KGM')])[0]
        self.unit_id=self.pool.get('product.uom').search(cr,uid,[('name','=','Unit')])[0]

        self.shop_id={}
        self.shop_id["TT1"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Sabadell')])[0]
        self.shop_id["TT2"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Rubí')])[0]
        self.shop_id["TT3"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Manresa')])[0]
        self.shop_id["TC"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Barcelona')])[0]
        self.shop_id["BD"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Hospitalet')])[0]


        self._load_file(cr,uid,data,'/opt/docs/Carreras/BACKUP-20070918',context)
        return {}
        self._load_file(cr,uid,data,'/opt/public/cachebak/BACKUP',context)
        return {}
        for y in ['2006']:
            for m in ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC']:
                for e in ['BD','TC','TT']:
                    path='/opt/fitxers/'+'ALB'+e+m+y
                    print "*****************",path,"******************"
                    self._load_file(cr,uid,data,path,context)
                    cr.commit()
                    print "COMMIT"
        for y in ['2007']:
            for m in ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO']:
                for e in ['BD','TC','TT']:
                    path='/opt/fitxers/'+'ALB'+e+m+y
                    print "*****************",path,"******************"
                    self._load_file(cr,uid,data,path,context)
                    cr.commit()
                    print "COMMIT"
        return {}

        for e in ['BD','TC','TT']:
        #for e in ['BD']:
            for m in ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO']:
                path='/opt/docs/Carreras/fitxers/'+'ALB'+e+m+'2007'
                print "*****************",path,"******************"
                self._load_file(cr,uid,data,path,context)
                cr.commit()
                print "COMMIT"
        return {}

    def _load_file(self, cr, uid, data, file, context):
        f = open(file)
        self.pool = pooler.get_pool(cr.dbname)

        self.numero_albarans=0
        self.numero_albarans_facturats=0
        self.n1=0
        self.n2=0

        try:
            while True:
                lin1=f.next()
                if not lin1.startswith('^DOC("'):
                    continue
                if not lin1.strip().endswith(")"):
                    continue
                break
            lin2=f.next()
        except StopIteration:
            return {}
        
        i=0
        lin=list()
        while True:
            
            a = lin1[5:lin1.find(")")].decode('latin-1').split(",")
            b = lin2.decode('latin-1').split('#')
            if len(a) == 5:
                if len(lin) > 1:
                    self._load_order(lin,cr,uid,data,context)
                lin=list()
            if len(a) == 5 or len(a) == 6:
                lin.append((a,b))
            else:
                print a + "\n" + b
                break

            try:
                lin1= f.next()
                lin2= f.next()
            except StopIteration:
                break
            if not lin1.startswith('^DOC("'):
                break
            
        if len(lin) > 1:
            self._load_order(lin,cr,uid,data,context)
        print "Elements llegits",self.numero_albarans
        print "Albarans facturats",self.n1
        print "Albarans sense factura",self.n2
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        }
    }
wizard_load_order('carreras.load_order')
