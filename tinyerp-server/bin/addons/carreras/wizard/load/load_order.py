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
import os.path
import time
import wizard
import pooler 
import netsvc
from glob import glob
import StringIO
import base64
import string

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de fulls de ruta i albarans">
    <label string="Carrega de fulls de ruta i albarans" colspan="4"/>
    <newline/>
    <field name="load_file" colspan="4"/>
</form>'''


select_fields = {
    'load_file':{
        'string': 'Fitxer a carregar',
        'type': 'binary',
    }
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
        return pool.get('product.product').browse(cr,uid,art_id[0])
    return False

_comptats={"BD":{},"TC":{},"TT":{}}
def _load_comptats(cr,uid,f):
    print 'Carregar clients de comptat'
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

class wizard_load_order(wizard.interface):

    def _set_default(self, cr, uid, data, context):
        return data['form']

    def get_cash_partner(self,cr,uid,lin, prefix):
        if lin[0][1][37] == "TL":
            num_fac="2%06d" % int(lin[0][1][2][1:])
        elif lin[0][1][37] == "TJ":
            num_fac="3%06d" % int(lin[0][1][2][1:])
        else:
            num_fac="1%06d" % int(lin[0][1][2][1:])
            
        comp=_comptats[lin[0][0][0][1:3]][num_fac].split('#')
        ref=comp[4].replace('-','')
        ids = self.pool.get('res.partner').search(cr,uid,[('ref','=',ref)])
        if not ids:
            id=self._create_partner(cr,uid,ref,comp)
            print prefix,"crear partner",ref,id
        else:
            id=ids[0]
        partner = self.pool.get('res.partner').browse(cr,uid,id)
        
        return partner.id

    def _create_partner(self,cr,uid,ref,comp):
        name = comp[0].decode('latin1').strip()
        d = self.pool.get('res.partner').search(cr,uid,[('name','=',name)])
        if d:
            name = name + " (*)"
            print "                   Nom del Client Duplicat"

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

    def _load_order(self, lin, cr, uid, data, context):
        # full de ruta
        if lin[0][0][3]=='1':
            return
        # albara no facturat
        if len(lin[0][1][2]) == 0:
            self.n2=self.n2+1
            return
        # albara bloquejat
        if lin[0][1][2]=="P":
            self.n2=self.n2+1
            #o['block']=True
            return
        
        #proves
        #if lin[0][0][0][1:3] != "BD":
        #    return
        #if self.numero_albarans > 10:
        #    return
        
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
            print "Tipus de registre desconegut >",lin[0][0]
            return

        self.numero_albarans = self.numero_albarans + 1

        if lin[0][0][0][1:3] == "TT":
            if lin[0][1][38] == "1":
                shop_id = self.shop_id["TT1"]
            elif lin[0][1][38] == "2":
                shop_id = self.shop_id["TT2"]
            elif lin[0][1][38] == "3":
                shop_id = self.shop_id["TT3"]
            else:
                print prefix,"> Centre desconegut <",lin[0][1][38],"> s'assigna Sabadell"
                shop_id = self.shop_id["TT1"]
        elif lin[0][0][0][1:3] == "TC":
            shop_id = self.shop_id["TC"]
        elif lin[0][0][0][1:3] == "BD":
            shop_id = self.shop_id["BD"]
        else:
            print prefix,"> Empresa",lin[0][0][0][1:3],"no trobada"
            return

        company_id = self.company[lin[0][1][37]]
        o={}
        o['name']=name
        o['company_id']=company_id
        o['shop_id']=shop_id
        o['pricelist_id']=self.default_pricelist

        ids = self.pool.get("res.partner.customer").search(cr,uid,[('name','=',lin[0][0][2])])
        if not ids:
            print prefix,"> Client",lin[0][0][2],"no trobat"
            return

        o['customer_id'] = ids[0]
        customer_obj = self.pool.get("res.partner.customer").browse(cr,uid,o['customer_id'])
        if lin[0][0][2][1:4]!="000":
            o['partner_id']=customer_obj.partner_id.id
        else:
            o['partner_id']=self.get_cash_partner(cr,uid,lin,prefix)
        o['partner_order_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['contact'])['contact']
        o['partner_invoice_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['invoice'])['invoice']
        o['partner_shipping_id']=self.pool.get('res.partner').address_get(cr, uid, [o['partner_id']], ['delivery'])['delivery']
        if not o['partner_order_id'] or not o['partner_invoice_id'] or not o['partner_shipping_id']:
            print prefix, "Adreces no trobades, client:",lin[0][0][2],'[ order',o['partner_order_id'],'] [ invoice',o['partner_invoice_id'],'] [ shipping',o['partner_shipping_id'],']'
            return

        o['stuff_desc']=lin[0][1][33]
        o['delivery_note']=lin[0][1][34] + "\n" + lin[0][1][35]
        o['client_order_ref']=lin[0][1][11]

        line_type=lin[1][0][5][-1:]
        #if line_type!="7":
        #    return
        if line_type not in self.line_type:
            print prefix,"> Tipus de linia desconegut",lin[1][0][5]
            return
        o['line_type']=self.line_type[line_type]

        o['date_order']=lin[0][1][0][0:4]+"-"+lin[0][1][0][4:6]+"-"+lin[0][1][0][6:8]

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
        o['block']=False

        try:
            if lin[0][0][2][1:4]=="000":
                if lin[0][1][37] == "TL":
                    num_fac="2.%06d" % int(lin[0][1][2][1:])
                elif lin[0][1][37] == "TJ":
                    num_fac="3.%06d" % int(lin[0][1][2][1:])
                else:
                    num_fac="1.%06d" % int(lin[0][1][2][1:])
            else:
                if lin[0][1][37] == "TJ":
                    num_fac="1.%06d" % int(lin[0][1][2][1:])
                else:
                    num_fac="0.%06d" % int(lin[0][1][2])
        except ValueError:
            print prefix,"numero de factura erroni:",lin[0][1][2]
            return

        prefix = prefix + " " + num_fac
        date_min=o['date_delivery'][0:4]+'-01-01'
        date_max=o['date_delivery'][0:4]+'-12-31'
        s1=[('name','=',num_fac),('date_invoice','>=',date_min),('date_invoice','<=',date_max),('company_id','=',company_id)]
        invoice_ids = self.pool.get('account.invoice').search(cr,uid,s1)
        if len(invoice_ids) == 0:
            year=str(int(o['date_delivery'][0:4]) + 1)
            date_min=year+'-01-01'
            date_max=year+'-12-31'
            s2=[('name','=',num_fac),('date_invoice','>=',date_min),('date_invoice','<=',date_max),('company_id','=',company_id)]
            invoice_ids = self.pool.get('account.invoice').search(cr,uid,s2)

        if len(invoice_ids) == 0:
            print prefix,"albara facturat sense factura :"
            print prefix,"  ",s1
            print prefix,"  ",s2
            return
        if len(invoice_ids) > 1:
            print prefix,"mes d'una factura per l'albara"

        invoice_line_ids=False
        invoice_line_ids = self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',invoice_ids[0])])
        if not invoice_line_ids:
            print prefix,"no es troben linies de la factura"
            return
        o['invoice_ids']=[(6,0,[invoice_ids[0]])]

        o['state']='done'
        o['shipped']=True
        #o['date_comission']=time.strftime('%Y-%m-%d')
        o['date_comission']='2008-06-30'
        self.n1=self.n1+1
        void = self.pool.get('sale.order').search(cr,uid,[('name','=',name),('company_id','=',company_id)])

        try:
            if void:
                oid=void[0]
                self.pool.get('sale.order').write(cr,uid,oid,o)
            else:
                oid = self.pool.get('sale.order').create(cr,uid,o)
                

            #self.wf_service.trg_validate(uid, 'sale.order', oid, 'order_confirm', cr)
            #self.wf_service.trg_validate(uid, 'sale.order', oid, 'manual_invoice', cr)
            self.wf_service.trg_validate(uid, 'sale.order', oid, 'subflow.paid', cr)
        except Exception, e:
            cr.commit()
            print prefix,"excepcio al crear la sale.order :",e
            return

        vwinst = self.pool.get('workflow.instance').search(cr,uid,[('res_type','=','sale.order'),('res_id','=',oid)])
        if vwinst:
            self.pool.get('workflow.instance').unlink(cr,uid,vwinst)
            vwit = self.pool.get('workflow.workitem').search(cr,uid,[('inst_id','in',vwinst)])
            if vwit:
                self.pool.get('workflow.workitem').unlink(cr,uid,vwit)

        """
        w={}
        w['wkf_id']=self.workflow_id
        w['res_id']=oid
        w['res_type']='sale.order'
        w['state']='complete'
        vwinst = self.pool.get('workflow.instance').search(cr,uid,[('res_type','=','sale.order'),('res_id','=',oid)])
        if vwinst:
            winst=vwinst[0]
            self.pool.get('workflow.instance').write(cr,uid,winst,w)
        else:
            winst = self.pool.get('workflow.instance').create(cr,uid,w)
            
        w={}
        w['act_id']=self.wf_act_id
        w['inst_id']=winst
        w['state']="'complete'"
        vwit = self.pool.get('workflow.workitem').search(cr,uid,[('act_id','=',self.wf_act_id),('inst_id','=',winst)])
        if vwit:
            wit=vwit[0]
            self.pool.get('workflow.workitem').write(cr,uid,wit,w)
        else:
            cr.execute("select nextval('"+self.pool.get('workflow.workitem')._sequence+"')")
            id_new = cr.fetchone()[0]
            up0=[]
            up1=[]
            for k,v in w.iteritems():
                up0.append(k)
                up1.append(v)
            upd0=','.join(map(str,up0))
            upd1=','.join(map(str,up1))
            s='insert into wkf_workitem (id,'+upd0+") values ("+str(id_new)+','+upd1+')'
            print s
            cr.execute(s)
            #wit = self.pool.get('workflow.workitem').create(cr,uid,w)
        """
        #print prefix

        for i in range(1,len(lin)):
            l= self._load_line[line_type](o['company_id'],lin[i][1], cr, uid, data, context)
            if not l:
                print prefix
                continue
            l['line_type']=self.line_type[line_type]
            l['order_id']=oid
            if 'name' not in l:
                l['name']=str(i*10)
            l['sequence']=str(i*10)
            l['pricelist_partner_id']=False
            l['state']='done'
            if invoice_line_ids:
                l['invoice_lines']=[(6,0,invoice_line_ids)]
            vlid = self.pool.get('sale.order.line').search(cr,uid,[('order_id','=',oid),('sequence','=',lin[i][0][5][0:2])])
            if vlid:
                lid=vlid[0]
                self.pool.get('sale.order.line').write(cr,uid,lid,l)
            else:
                lid = self.pool.get('sale.order.line').create(cr,uid,l,context={})

        return

    def _load_TR(self, company_id, lin, cr, uid, data, context):
        l={}
        product_id=get_art(cr,uid,lin[0].strip())
        if not product_id:
            print 'producte',lin[0],'no trobat'
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
            print 'producte',lin[0],'no trobat'
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

    def _load(self, cr, uid, data, context):
        self.pool = pooler.get_pool(cr.dbname)
        
        uid=self.pool.get('res.users').search(cr, uid, [('login','=','batch')])[0]
        
        
        vwid = self.pool.get('workflow').search(cr,uid,[('name','=','sale.order.basic')])
        if not vwid:
            print "no es troba el workflow"
            return
        self.workflow_id=vwid[0]
        vwid = self.pool.get('workflow.activity').search(cr,uid,[('wkf_id','=',self.workflow_id),('name','=','done')])
        if not vwid:
            print "no es troba el workflow activity"
            return
        self.wf_act_id=vwid[0]
        
        
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

        self.wf_service = netsvc.LocalService("workflow")
        if not self.load_comptats(cr,uid):
            print "Error Comptats"
            return {}
        
        #produccio
        #months=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC']
        #self.load_year(cr,uid,data,"2006",months,['BD','TC','TT'],context)
        #self.load_year(cr,uid,data,"2007",months,['BD','TC','TT'],context)
        months=['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP']
        self.load_year(cr,uid,data,"2008",months,['BD','TC','TT'],context)
        
        #proves
        #months=['ENE']
        #self.load_year(cr,uid,data,"2007",months,['BD'],context)
        print "Final"
        return {}

    def load_comptats(self,cr,uid):
        if os.path.isfile('/opt/fitxers/COMPTATS'):
            path='/opt/fitxers/COMPTATS'
            f = open(path)
        elif os.path.isfile('/opt/docs/Carreras/fitxers/COMPTATS'):
            path='/opt/docs/Carreras/fitxers/COMPTATS'
            f = open(path)
        else:
            f=fbackup()
        return _load_comptats(cr,uid,f)

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
        if data['form'].get('load_file',False):
            f = StringIO.StringIO(base64.decodestring(data['form']['load_file']))
        else:
            if file == None:
                f = fbackup()
            else:
                f = open(file)

        self.numero_albarans=0
        self.numero_albarans_facturats=0
        self.n1=0
        self.n2=0
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
                cr.commit()
            
        if len(lin) > 1:
            self._load_order(lin,cr,uid,data,context)
        #print "Elements llegits",self.numero_albarans
        #print "Albarans facturats",self.n1
        #print "Albarans sense factura",self.n2
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
