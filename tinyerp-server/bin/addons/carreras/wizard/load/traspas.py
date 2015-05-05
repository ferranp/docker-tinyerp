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
  Carrega de fulls de ruta, albarans i factures

"""
import os.path
import time
import wizard
import pooler 
import netsvc
from glob import glob
import StringIO
import base64
import threading

from common import *

logger = netsvc.Logger()


select_form = '''<?xml version="1.0"?>
<form string="Traspàs mensual des de Cache">
    <label string="Traspàs mensual des de Cache" colspan="4"/>
    <newline/>
    <field name="load_file_albarans" colspan="4"/>
    <newline/>
    <field name="load_file_factures" colspan="4"/>
    <newline/>
    <field name="load_file_comptats" colspan="4"/>
</form>'''

select_fields = {
    'load_file_albarans':{'string': 'Fitxer de d\'Albarans','type': 'binary'},
    'load_file_factures':{'string': 'Fitxer de Factures','type': 'binary'},
    'load_file_comptats':{'string': 'Fitxer de Clients de Comptats','type': 'binary'},
}

_factures={"BD":{},"TC":{},"TT":{}}
def _load_factures(cr,uid,f):
    logger.notifyChannel("info", netsvc.LOG_INFO,"Carregar factures")
    for lin in f:
        if len(lin.strip()) < 10:
            continue
        if lin[-7:-6]=="V":
            print "6",numfac
            return False
        if lin.startswith('^FRA('):
            lin = lin.strip()
            cname=lin[6:8]
            company_id = get_company(cr,uid,cname)
            if not company_id:
                continue
            numfac=lin[21:-1]
            l=len(numfac)
            fact={}
            fact["D"]=lin[12:20]
            fact["G"]=f.next()
            lin=f.next()
            if lin[21:-7] != numfac:
                print "1",numfac
                return False
            if lin[-5:-4] != 'I':
                print "2",numfac
                return False
            fact["I"]=f.next()
            fact["L"]=list()
            lin=f.next()
            if lin[21+l+2:21+l+3]!="L":
                print "7",numfac
                return False
            while lin[21+l+2:21+l+3]=="L":
                if lin[21:21+l] != numfac:
                    print "3",numfac
                    return False
                fact["L"].append(f.next())
                lin=f.next()
            if lin[21:-9] != numfac:
                print "4",numfac
                return False
            if lin[-7:-6] != 'V':
                print "5",numfac
                return False
            fact["V"]=f.next()
            _factures[cname][int(numfac)]=fact
    return True

_comptats={"BD":{},"TC":{},"TT":{}}
def _load_comptats(cr,uid,f):
    logger.notifyChannel("info", netsvc.LOG_INFO,'Carregar clients de comptat')
    for lin in f:
        if len(lin.strip()) < 15:
            continue
        if lin.startswith('^TTCOMPT('):
            lin = lin.strip()
            cname=lin[10:12]
            company_id = get_company(cr,uid,cname)
            if not company_id:
                continue
            _comptats[cname][lin[16:-1]]=f.next()
    return True

_accounts={}
def _load_accounts(cr,uid):
    logger.notifyChannel("info", netsvc.LOG_INFO,'Carregar comptes en memoria')
    cr.execute("select id,code,company_id from account_account " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _accounts[(c[1],c[2])] = c[0]
        
def get_account(cr,uid,code,company):
    return _accounts[(code,company)]

_journals={}    
def _load_journals(cr,uid):
    logger.notifyChannel("info", netsvc.LOG_INFO,'Carregar diaris en memoria')
    cr.execute("select id,code,company_id from account_journal " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _journals[(c[1].strip(),c[2])] = c[0]
        
def get_journal(cr,uid,code,company):
    return _journals[(code,company)]

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
        return pool.get('product.product').browse(cr,uid,art_id[0])
    return False

class TraspasBatch(threading.Thread):
    def __init__(self,cr, uid, data, context, emp):
        threading.Thread.__init__(self)
        self.dbname = cr.dbname
        self.uid = uid
        self.data = data
        self.context = context
        self.emp=emp
        
    def run(self):
        cr = pooler.get_db(self.dbname).cursor()
        #print "start thread " 
        try:
            self.process(cr, self.uid, self.data, self.context)
            cr.commit()
            #print "end thread " + str(newinv)
        except Exception , e:
            logger.notifyChannel("info", netsvc.LOG_INFO,e)
            

    def _load_order(self, lin, cr, uid, data, context):
        # ELS FULLS DE RUTA NO ES TRASPASSEN
        if lin[0][0][3]=='1':
            return
        
        if lin[0][0][3]=='1':
            name=lin[0][0][4]
            prefix= lin[0][0][3] + " " +name
        elif lin[0][0][3]=='2':
            if lin[0][1][21] == "":
                name = 'VA-%s' % lin[0][0][4]
            else:
                name = lin[0][1][21]
            prefix= lin[0][0][3] + " " + name + " " + lin[0][0][4]
        else:
            logger.notifyChannel("info", netsvc.LOG_INFO,"Tipus de registre desconegut > %s" % lin[0][0])
            return

        
        self.numero_albarans = self.numero_albarans + 1
        #if self.numero_albarans > 10:
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
                logger.notifyChannel("info", netsvc.LOG_INFO,"%s > Centre desconegut < %s > s'assigna Sabadell" % (prefix,lin[0][1][38]))
                shop_id = self.shop_id["TT1"]
        elif lin[0][0][0][1:3] == "TC":
            shop_id = self.shop_id["TC"]
        elif lin[0][0][0][1:3] == "BD":
            shop_id = self.shop_id["BD"]
        else:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s > Empresa %s no trobada" % (prefix,lin[0][0][0][1:3]))
            return

        company_id = self.company[lin[0][1][37]]
        o={}
        o['name']=name
        o['company_id']=company_id
        o['shop_id']=shop_id
        o['pricelist_id']=self.default_pricelist

        ids = self.pool.get("res.partner.customer").search(cr,uid,[('name','=',lin[0][0][2])])
        if not ids:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s > Client %s no trobat" % (prefix,lin[0][0][2]))
            return

        o['customer_id'] = ids[0]
        customer = self.pool.get("res.partner.customer").browse(cr,uid,o['customer_id'])
        o['partner_id']=customer.partner_id.id
        o['partner_order_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['contact'])['contact']
        o['partner_invoice_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['invoice'])['invoice']
        o['partner_shipping_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['delivery'])['delivery']
        if not o['partner_order_id'] or not o['partner_invoice_id'] or not o['partner_shipping_id']:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s Adreces no trobades, client: %s" % (prefix,lin[0][0][2]))
            logger.notifyChannel("info", netsvc.LOG_INFO," partner_order_id %s" % o['partner_order_id'])
            logger.notifyChannel("info", netsvc.LOG_INFO," partner_invoice_id %s" % o['partner_invoice_id'])
            logger.notifyChannel("info", netsvc.LOG_INFO," partner_shipping_id %s" % o['partner_shipping_id'])
            return

        o['stuff_desc']=lin[0][1][33]
        o['delivery_note']=lin[0][1][34] + "\n" + lin[0][1][35]
        o['client_order_ref']=lin[0][1][11]

        line_type=lin[1][0][5][-1:]
        if line_type not in self.line_type:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s > Tipus de linia desconegut %s" % (prefix,lin[1][0][5]))
            return
        o['line_type']=self.line_type[line_type]

        o['state']='draft'
        o['date_order']=lin[0][1][0][0:4]+"-"+lin[0][1][0][4:6]+"-"+lin[0][1][0][6:8]
        o['block']=False

        if lin[0][0][3]=='2':
            o['state']='manual'

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

            if lin[0][1][2]=="P":
                o['block']=True

        invoice_line_ids=False
        if lin[0][0][3]=='2':
            if lin[0][1][2] !="P" and len(lin[0][1][2]) > 0:
                prefix2,inv_id,invoice_line_ids,partner= self._load_invoice(cr,uid,lin,prefix,company_id)
                if not prefix2:
                    logger.notifyChannel("info", netsvc.LOG_INFO,prefix)
                    return False
                prefix=prefix2
                o['invoice_ids']=[(6,0,[inv_id])]
                o['state']='progress'
                if partner.id != customer.partner_id.id:
                    o['partner_id']=partner.id
                    o['partner_order_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['contact'])['contact']
                    o['partner_invoice_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['invoice'])['invoice']
                    o['partner_shipping_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['delivery'])['delivery']
                    if not o['partner_order_id'] or not o['partner_invoice_id'] or not o['partner_shipping_id']:
                        logger.notifyChannel("info", netsvc.LOG_INFO,"%s Adreces no trobades, client comptat, partner: %s" % (prefix,o['partner_id']))
                        logger.notifyChannel("info", netsvc.LOG_INFO," partner_order_id %s" % o['partner_order_id'])
                        logger.notifyChannel("info", netsvc.LOG_INFO," partner_invoice_id %s" % o['partner_invoice_id'])
                        logger.notifyChannel("info", netsvc.LOG_INFO," partner_shipping_id %s" % o['partner_shipping_id'])
                        return

        void = self.pool.get('sale.order').search(cr,uid,[('name','=',name),('company_id','=',company_id)])
        try:
            if void:
                # NO S'ACTUALITZEN ELS ALBARANS JA TRASPASSATS
                logger.notifyChannel("info", netsvc.LOG_INFO,prefix+" ja traspassat")
                return
                oid=void[0]
                self.pool.get('sale.order').write(cr,uid,oid,o)
            else:
                oid = self.pool.get('sale.order').create(cr,uid,o)
            if o['state'] == 'manual':
                self.wf_service.trg_validate(uid, 'sale.order', oid, 'manual_invoice', cr)
            #elif o['state'] == 'progress':
            #    self.wf_service.trg_validate(uid, 'sale.order', oid, 'order_confirm', cr)
        except Exception, e:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s Excepcio al crear la sale.order: %s" % (prefix,str(e)))
            return

        logger.notifyChannel("info", netsvc.LOG_INFO,prefix)
        for i in range(1,len(lin)):
            l= self._load_line[line_type](o['company_id'],lin[i][1], cr, uid, data, context)
            if not l:
                logger.notifyChannel("info", netsvc.LOG_INFO,lin)
                continue
            l['line_type']=self.line_type[line_type]
            l['order_id']=oid
            if 'name' not in l:
                l['name']=str(i*10)
            l['sequence']=str(i*10)
            l['pricelist_partner_id']=False
            l['state']='done'
            l['invoiced']=False
            if invoice_line_ids:
                l['invoice_lines']=[(6,0,invoice_line_ids)]
                l['invoiced']=True
            vlid = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',oid),('sequence','=',lin[i][0][5][0:2])])
            if vlid:
                lid=vlid[0]
                self.pool.get('sale.order.line').write(cr,uid,lid,l)
            else:
                lid = self.pool.get('sale.order.line').create(cr,uid,l,context={})
        
        return

    def _load_invoice(self,cr,uid,lin,prefix,company_id):
        try:
            if lin[0][0][2][1:4]=="000":
                if lin[0][1][37] == "TL":
                    num_fac="2%06d" % int(lin[0][1][2][1:])
                elif lin[0][1][37] == "TJ":
                    num_fac="3%06d" % int(lin[0][1][2][1:])
                else:
                    num_fac="1%06d" % int(lin[0][1][2][1:])
            else:
                if lin[0][1][37] == "TJ":
                    num_fac="1%06d" % int(lin[0][1][2][1:])
                else:
                    num_fac="0%06d" % int(lin[0][1][2])
        except ValueError:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s numero de factura erroni: %s" % (prefix,lin[0][1][2]))
            return False
        prefix = prefix + " " + num_fac

        if int(num_fac) not in _factures[lin[0][0][0][1:3]]:
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s la factura no es troba en el fitxer de factures" % prefix)
            return False
        fact=_factures[lin[0][0][0][1:3]][int(num_fac)]
        date_inv = fact["D"][0:4] + '-' +fact["D"][4:6] +'-' +fact["D"][6:8]
        numfac = "%s/%s" % (num_fac[0:1],num_fac[1:])
        l=fact["G"].split('#')
        cust = l[0]
        amount = float(l[3])
        descompte=0.0
        despeses=0.0
        if len(l[17]) > 0:
            descompte = float(l[17])
        if len(l[6]) > 0:
            despeses = float(l[6])
        l=fact["I"].split('#')
        por_iva = l[10]
        imp_iva = l[4]
        acc = "4300%s" % cust
        acc_id = get_account(cr,uid,acc,company_id)
        
        fac = {}
        fac['name'] = numfac
        fac['origin'] = "Càrrega Caché"
        fac['type'] = 'out_invoice'
        fac['number'] = numfac
        fac['state'] = 'draft'
        fac['date_invoice'] = date_inv
        fac['date_due'] = date_inv
        if cust[1:4]=="000":
            comp=_comptats[lin[0][0][0][1:3]][num_fac].split('#')
            ref=comp[4].replace('-','')
            ids = self.pool.get('res.partner').search(cr,uid,[('ref','=',ref)])
            if not ids:
                id=self._create_partner(cr,uid,ref,comp)
                logger.notifyChannel("info", netsvc.LOG_INFO,"%s crear partner %s %d" % (prefix,ref,id))
            else:
                id=ids[0]
            partner = self.pool.get('res.partner').browse(cr,uid,id)
        else:
            partner = get_partner(cr,uid,cust)
        fac['partner_id'] = partner.id
        ret_partner=partner
        #if len(lin0[13]) > 7:
        #    emp['last_invoice'] = lin0[13][0:4] + '-' + lin0[13][4:6] + '-' + lin0[13][6:8]
        fac['address_invoice_id']= self.pool.get('res.partner').address_get(cr, uid, [partner.id], ['invoice'])['invoice']

        fac['payment_term']=self.pay_term_comptat
        if cust[1:4]!="000" and partner.property_payment_term and partner.property_payment_term.id:
            fac['payment_term'] = partner.property_payment_term.id 

        fac['account_id'] = acc_id
        fac['currency_id'] = 1
        fac['journal_id'] = get_journal(cr,uid,"VENT",company_id)
        fac['company_id'] = company_id
        
        s = [('name','=',numfac),('partner_id','=',partner.id),('company_id','=',company_id)]
        ids = self.pool.get("account.invoice").search(cr,uid,s)
        if ids:
            dids=self.pool.get("account.invoice").read(cr,uid,ids[0],['invoice_line'])['invoice_line']
            #self.pool.get("account.invoice.line").unlink(cr,uid,dids)
            #fac['invoice_line']=[]
            #self.pool.get("account.invoice").write(cr,uid,ids,fac)
            return prefix,ids[0],dids,ret_partner            
        else:
            ids = self.pool.get("account.invoice").create(cr,uid,fac)
            ids = [ids]
        
        v_acc_id=get_account(cr,uid,'70510',company_id)
        tax_id = self.pool.get('account.account').read(cr,uid,[v_acc_id],['tax_ids'])[0]
        line_id = self.pool.get('account.invoice.line').create(cr, uid, {
            'name': numfac,
            'invoice_id': ids[0],
            'account_id': v_acc_id,
            'price_unit': amount,
            'quantity': 1,
            'discount': 0.0,
            'uos_id': False,
            'product_id': False,
            'invoice_line_tax_id': [ (6,0,tax_id['tax_ids']) ],
            'note': False,
            'account_analytic_id': False,
        })
        l_ids=[line_id]

        if descompte !=0:
            partner = get_partner(cr,uid,cust)
            taxes = partner.property_account_discount.tax_ids
            line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                'name': "Descuento",
                'invoice_id': ids[0],
                'account_id': partner.property_account_discount.id,
                'price_unit': -descompte,
                'quantity': 1,
                'discount': 0.0,
                'uos_id': False,
                'product_id': False,
                'invoice_line_tax_id': [(6,0,[t.id for t in taxes  ])],
                'note': False,
                'account_analytic_id': False,
            })
            l_ids.append(line_id)

        if despeses !=0:
            partner = get_partner(cr,uid,cust)
            line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                'name': "Gastos Financieros",
                'invoice_id': ids[0],
                'account_id': partner.property_account_financing.id,
                'price_unit': despeses,
                'quantity': 1,
                'discount': 0.0,
                'uos_id': False,
                'product_id': False,
                'invoice_line_tax_id': False,
                'note': False,
                'account_analytic_id': False,
            })
            l_ids.append(line_id)

        self.pool.get("account.invoice").button_compute(cr,uid,ids)
        return prefix,ids[0],l_ids,ret_partner

    def _create_partner(self,cr,uid,ref,comp):
        name = comp[0].decode('latin1').strip()

        emp = dict()
        emp['name'] = name
        emp['ref'] = ref
        #emp['category_id'] = [(6,0,self.categ_id)]
        emp['credit_limit'] = 0.0
        emp_id = self.pool.get('res.partner').create(cr,uid,emp,context={})

        addr = dict()
        addr['name'] = name
        addr['partner_id'] = emp_id
        addr['type'] = 'default'
        addr['street'] = comp[1].decode('latin1')
        if len(comp[2].split('-')) > 1:
            addr['zip'] = comp[2].split('-',2)[0].decode('latin1')
            addr['city'] = " ".join(comp[2].split('-')[1:])
            addr['city'] = addr['city'].decode('latin1')
        else:
            addr['zip'] = ''
            addr['city'] = comp[2].decode('latin1')

        addr['phone'] = comp[7].decode('latin1')
        addr_id = self.pool.get('res.partner.address').create(cr,uid,addr)
        return emp_id
        

    def _load_TR(self, company_id, lin, cr, uid, data, context):
        l={}
        product_id=get_art(cr,uid,lin[0].strip())
        if not product_id:
            logger.notifyChannel("info", netsvc.LOG_INFO,"crear %s no trobal" % lin[0])
            return False
        l['product_id']=product_id.id
        product_obj=self.pool.get('product.template').browse(cr,uid,product_id.id)
        for tax in product_obj.taxes_id:
            if tax.company_id.id == company_id:
                break
        l['name']=product_id.partner_ref
        l['tax_id']=[ (6,0,[tax.id]) ]
        l['depth']=int(lin[1])
        #l['price_net']=float(lin[2])
        l['price_unit']=float(lin[6])
        l['kilos']=float(lin[7])
        l['quantity']=float(lin[5])
        price_net=round(float(lin[2].strip()),2)
        price_net2=round(float(l['kilos'] * l['price_unit']),2)
        if price_net == price_net2:
            l['product_uom']=self.kgm_id
            l['product_uom_qty']=float(lin[7])
            return l
        price_net2=round(float(l['quantity'] * l['price_unit']),2)
        if price_net == price_net2:
            l['product_uom']=self.unit_id
            l['product_uom_qty']=float(lin[5])
            return l
        # si no quadra cap multiplicació -> 1 * net = net
        l['kilos']=1.0
        l['quantity']=1.0
        l['price_unit']=float(lin[2].strip())
        l['product_uom']=self.kgm_id
        l['product_uom_qty']=1.0
        return l

    def _load_RE(self, company_id, lin, cr, uid, data, context):
        l={}
        l['product_uom']=self.unit_id
        product_id=get_art(cr,uid,lin[0].strip())
        if not product_id:
            logger.notifyChannel("info", netsvc.LOG_INFO,"crear %s no trobal" % lin[0])
            return False
        l['product_id']=product_id.id
        product_obj=self.pool.get('product.template').browse(cr,uid,product_id.id)
        for tax in product_obj.taxes_id:
            if tax.company_id.id == company_id:
                break 
        l['name']=product_id.partner_ref
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
        l['price_net']=float(lin[2])
        if len(lin[5]):
            qty=float(lin[5])
        else:
            qty=1.0
        l['tax_id']=[ (6,0,self.company_taxes[company_id]) ]
        l['product_uom_qty']=qty
        l['kilos']=qty
        l['quantity']=qty
        l['product_id']=False
        if len(lin[6]):
            l['price_unit']=float(lin[6])
        else:
            l['price_unit']=0.0
        return l

    def process(self,cr,uid,data,context):
        self.pool = pooler.get_pool(cr.dbname)

        _load_accounts(cr,uid)
        _load_journals(cr,uid)

        uid=self.pool.get('res.users').search(cr, uid, [('login','=','batch')])[0]

        self.pay_term_comptat= self.pool.get('account.payment.term').search(cr,uid,[('type','=','comptat')])[0]

        self.categ_id = self.pool.get('res.partner.category').search(cr,uid,[('name','=','Client')])
        self.wf_service = netsvc.LocalService("workflow")

        self._load_line={"2":self._load_TR,"3":self._load_RE,"7":self._load_VA}
        self.line_type={"2":"TR","3":"RE","7":"VA"}
        self.kgm_id=self.pool.get('product.uom').search(cr,uid,[('name','=','KGM')])[0]
        self.unit_id=self.pool.get('product.uom').search(cr,uid,[('name','=','Unit')])[0]
        self.default_pricelist=self.pool.get('product.pricelist').search(cr,uid,[('name','=','Default Sale Pricelist')])[0]

        self.company={}
        self.company["TT"]=self.pool.get('res.company').search(cr,uid, [('short_name','=',"TT")])[0]
        self.company["TJ"]=self.pool.get('res.company').search(cr,uid, [('short_name','=',"TJ")])[0]
        self.company["TC"]=self.pool.get('res.company').search(cr,uid, [('short_name','=',"TC")])[0]
        self.company["TL"]=self.pool.get('res.company').search(cr,uid, [('short_name','=',"TL")])[0]
        self.company["BD"]=self.pool.get('res.company').search(cr,uid, [('short_name','=',"BD")])[0]

        self.company_taxes={}
        for comp in ["TT","TJ","TC","TL","BD"]:
            id=self.company[comp]
            s = [('name','=',"Iva repercutit al 16%"),('company_id','=',id)]
            self.company_taxes[id]= self.pool.get('account.tax').search(cr,uid,s)

        self.shop_id={}
        self.shop_id["TT1"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Sabadell')])[0]
        self.shop_id["TT2"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Rubí')])[0]
        self.shop_id["TT3"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Manresa')])[0]
        self.shop_id["TC"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Barcelona')])[0]
        self.shop_id["BD"] = self.pool.get('sale.shop').search(cr,uid,[('name','=','Hospitalet')])[0]
        
        f = StringIO.StringIO(base64.decodestring(data['form']['load_file_comptats']))
        #f = open('/opt/docs/Carreras/COMPTATS')
        if not _load_comptats(cr,uid,f):
            return {}

        f = StringIO.StringIO(base64.decodestring(data['form']['load_file_factures']))
        #f = open('/opt/docs/Carreras/fitxers/FRATTOCT2007')
        if not _load_factures(cr,uid,f):
            return {}

        #self._load_file(cr,uid,data,"/opt/docs/Carreras/fitxers/ALBTTOCT2007",context)
        #return {}
        
        #canviem temporalment l'empresa de l'usuari 'batch' per la càrrega
        company_orig = self.pool.get('res.users').company_get(cr,uid,uid)
        self.pool.get('res.users').write(cr,uid,[uid],{'company_id':self.company[self.emp]})
        
        self._load_file(cr,uid,data,None,context)
        
        #tornem l'empresa original a l'usuari 'batch'
        self.pool.get('res.users').write(cr,uid,[uid],{'company_id':company_orig})
        
        logger.notifyChannel("info", netsvc.LOG_INFO,"FINISH HIM")

        return {}

    def load_year(self,cr,uid,data,year,months,emps,context):
        if os.path.isdir('/opt/fitxers'):
            direc='/opt/fitxers/'
        else:
            direc='/opt/docs/Carreras/fitxers/'
        for m in months:
            for e in emps:
                path=direc+'ALB'+e+m+year
                if os.path.isfile(path):
                    print "*****************",path,"******************"
                    self._load_file(cr,uid,data,path,context)
                    cr.commit()

    def _load_file(self, cr, uid, data, file=None, context={}):
        if data['form'].get('load_file_albarans',False):
            f = StringIO.StringIO(base64.decodestring(data['form']['load_file_albarans']))
        else:
            if file == None:
                f = fbackup()
            else:
                f = open(file)

        self.numero_albarans=0
        self.numero_albarans_facturats=0
        self.num_commit=0

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
            self.num_commit=self.num_commit + 1
            if self.num_commit == 50:
                self.num_commit=0
                print "COMMIT"
                cr.commit()
            
        if len(lin) > 1:
            self._load_order(lin,cr,uid,data,context)
        return {}


class wizard_traspas(wizard.interface):

    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        if not data['form'].get('load_file_albarans',False):
            raise wizard.except_wizard('Procés Cancel·lat',
                "Falta el fitxer d'albarans")
        if not data['form'].get('load_file_factures',False):
            raise wizard.except_wizard('Procés Cancel·lat',
                "Falta el fitxer de factures")
        if not data['form'].get('load_file_comptats',False):
            raise wizard.except_wizard('Procés Cancel·lat',
                "Falta el fitxer de clients de comptats")
        
        f = StringIO.StringIO(base64.decodestring(data['form']['load_file_albarans']))
        while True:
            lin=f.next()
            c1=lin[6:8]
            if c1 in ["BD","TC","TT"]:
                break
        while True:
            lin=f.next()
            c2=lin[6:8]
            if c2 in ["BD","TC","TT"]:
                break
        if c1 != c2:
            raise wizard.except_wizard('Procés Cancel·lat',
                "Els fitxers de factures i albarans han de ser de la mateix empresa i periode")
        t = TraspasBatch(cr,uid,data,context,c1)
        t.start()
        raise wizard.except_wizard('Procés de traspàs executant-se ...', 
                                    "Comproveu els albarans i factures en uns minuts.")
        
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
wizard_traspas('carreras.traspas')
