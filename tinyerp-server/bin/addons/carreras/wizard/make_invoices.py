# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: make_invoice.py 1070 2005-07-29 12:41:24Z nicoe $
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

# 04.05.09 Al generar factures triar les que tenen import 0

"""
  Generar factures amb batch

"""
import wizard
import netsvc
import pooler
import time
import threading

inv_dates_form = '''<?xml version="1.0"?>
<form string="Facturació d'Albarans">
    <separator colspan="4" string="Limits de Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="date_invoice" />
    <newline/>
    <field name="customer_id_1"/>
    <field name="customer_id_2"/>
    <newline/>
    <field name="date_min" />
    <field name="date_max" />
    <field name="delivery_min" />
    <field name="delivery_max" />
</form>'''

inv_dates2_form = '''<?xml version="1.0"?>
<form string="Facturació d'Albarans">
    <separator string="Albarans Seleccionats" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="num_orders" colspan="4"/>
    <field name="amount_orders" colspan="4"/>
    <separator string="Procediment" colspan="4"/>
    <field name="batch" />
    <newline/>
    <field name="grouped" />
</form>'''

inv_print_form = '''<?xml version="1.0"?>
<form string="Facturació d'Albarans">
    <separator string="Imprimir les factures" colspan="4"/>
</form>'''

ref_dates_form = '''<?xml version="1.0"?>
<form string="Generació d'Abonaments">
    <separator colspan="4" string="Limits de Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="date_invoice" />
    <newline/>
    <field name="customer_id_1"/>
    <field name="customer_id_2"/>
    <newline/>
    <field name="date_min" />
    <field name="date_max" />
    <field name="delivery_min" />
    <field name="delivery_max" />
</form>'''

ref_dates2_form = '''<?xml version="1.0"?>
<form string="Generació d'Abonaments">
    <separator string="Albarans Seleccionats" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="num_orders" colspan="4"/>
    <field name="amount_orders" colspan="4"/>
    <separator string="Procediment" colspan="4"/>
    <field name="batch" />
    <newline/>
    <field name="grouped" />
</form>'''

ref_print_form = '''<?xml version="1.0"?>
<form string="Generació d'Abonaments">
    <separator string="Imprimir els abonaments" colspan="4"/>
</form>'''

invoice_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'date_invoice': {'string': 'Data de facturació', 'type': 'date'},    
    'customer_id_1': {'string': 'De Codi de Client', 'type': 'many2one', 'relation': 'res.partner.customer'},    
    'customer_id_2': {'string': 'A Codi de Client', 'type': 'many2one', 'relation': 'res.partner.customer'},    
    'partner_id': {'string': 'Client', 'type': 'many2one', 'relation': 'res.partner'},    
    'date_min': {'string': 'De la Data Albarà', 'type': 'date'},
    'date_max': {'string': 'A la Data Albarà', 'type': 'date'},
    'delivery_min': {'string': "De l'Albarà", 'type': 'char'},
    'delivery_max': {'string': "A l'Albarà", 'type': 'char'},
    'num_orders': {'string': "Numero d'Albarans", 'type': 'integer', 'readonly': True},
    'amount_orders': {'string': 'Import dels Albarans', 'type': 'float', 'readonly': True},
    'batch' : {'string':'Procés en Batch', 'type':'boolean', 'default': lambda x,y,z: True},
    'grouped' : {'string':'Agrupar els Albarans', 'type':'boolean', 'default': lambda x,y,z: True}
}

class BatchInvoices(threading.Thread):
    def __init__(self,cr, uid, data, context):
        threading.Thread.__init__(self)
        self.dbname = cr.dbname
        self.uid = uid
        self.data = data
        self.context = context
        
    def run(self):
        cr = pooler.get_db(self.dbname).cursor()
        #print "start thread " 
        try:
            newinv = _makeInvoices(self, cr, self.uid, self.data, self.context)
            cr.commit()
            #print "end thread " + str(newinv)
        except Exception , e:
            logger= netsvc.Logger()
            logger.notifyChannel("info", netsvc.LOG_INFO,"error: %s" % e)

def make_invoices(self, cr, uid, data, context):
    if data['form'].get('batch'):
        t = BatchInvoices(cr,uid,data,context)
        t.start()
    else:
        newinv = _makeInvoices(self, cr, uid, data, context)
    return {}
        
def view_invoices(self, cr, uid, data, context):
    if data['form'].get('batch'):
        raise wizard.except_wizard('Procés de facturació executant-se ...', 
                                    "Comproveu les factures en uns minuts.")
        return {}
        
    data['ids'] = data['form']['ids']
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')
    newinv = []

    for o in order_obj.browse(cr, uid, data['ids'], context):
        for i in o.invoice_ids:
            if i.id not in newinv:
                newinv.append(i.id)

    return {
        'domain': "[('id','in', ["+','.join(map(str,newinv))+"])]",
        'name': 'Factures Generades',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.invoice',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }

def _makeInvoices(self, cr, uid, data, context):
    data['ids'] = data['form']['ids']
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')
    newinv = []
    order_obj.action_invoice_create(cr, uid, data['ids'], data['form']['grouped'])
    for id in data['ids']:
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', id, 'manual_invoice', cr)
    for o in order_obj.browse(cr, uid, data['ids'], context):
        for i in o.invoice_ids:
            if i.id not in newinv:
                newinv.append(i.id)

    inv_obj=pooler.get_pool(cr.dbname).get('account.invoice')

    # Forçar el periode a la data de factura
    period_obj = pooler.get_pool(cr.dbname).get('account.period')
    for i in inv_obj.browse(cr, uid, newinv):
        s = [('date_start','<=',data['form']['date_invoice']),
             ('date_stop','>=',data['form']['date_invoice']),
             ('company_id','=',i.company_id.id),
            ]
        p_id = period_obj.search(cr, uid,s)
        if len(p_id) ==0:
            raise wizard.except_wizard('No es pot iniciar la facturació.', 
                                    "No existeix cap periode en aquesta empresa i data.")
        d = {
            'date_invoice': data['form']['date_invoice'],
            'period_id' : p_id[0]
        }
        inv_obj.write(cr, uid, i.id, d)
        inv_obj.compute_date_due(cr,uid,i.id)
    return newinv

def _printInvoices(self, cr, uid, data, context):
    data['ids'] = data['form']['ids']
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')
    newinv = []
    for o in order_obj.browse(cr, uid, data['ids'], context):
        for i in o.invoice_ids:
            if i.id not in newinv:
                newinv.append(i.id)
    return {'ids' : newinv , 'original':True}

def _get_defaults(self,cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    
    if not pool.get("res.users").has_groups(cr,uid,uid,["Direcció","Administració"]):
        raise wizard.except_wizard(
            "Facturació cancel·lada",
            "L'usuari no té permís per facturar albarans")
    
    user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
    data['form']['company_id'] = user['company_id'][0]
    data['form']['date_invoice'] = time.strftime('%Y-%m-%d')

    data['form']['date_min'] = '2000-01-01'
    data['form']['date_max'] = '2050-12-31'
    
    child_c = pool.get('res.company')._get_company_children(cr,uid,data['form']['company_id'])
    
    comp_str = ",".join([str(c) for c in child_c])

    sql = "select min(delivery),max(delivery) from sale_order where "\
          + " delivery is not null and state in ('manual')"\
          + " and company_id in (%s) " % comp_str
    cr.execute(sql)
    min,max = cr.fetchone()

    data['form']['delivery_min'] = min
    data['form']['delivery_max'] = max

    return data['form']

def _get_totals(self,cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
    data['form']['company_id'] = user['company_id'][0]
    s_obj = pool.get('sale.order')
    
    date_min = data['form']['date_min']
    date_max = data['form']['date_max']

    if data['form']['date_min'] == False:
        raise wizard.except_wizard('Procés Cancel·lat',"Data d'albarà mínima incorrecta")
    if data['form']['date_max'] == False:
        raise wizard.except_wizard('Procés Cancel·lat',"Data d'albarà màxima incorrecta")
    if data['form']['date_invoice'] == False:
        raise wizard.except_wizard('Procés Cancel·lat',"Data de facturació incorrecta")

    del_min = data['form']['delivery_min']
    del_max = data['form']['delivery_max']

    child_c = pool.get('res.company')._get_company_children(cr,uid,data['form']['company_id'])
    
    comp_str = ",".join([str(c) for c in child_c])
    
    sql = "select id from sale_order where "+\
          " date_delivery between '%s' and '%s' and "+\
          " delivery between '%s' and '%s' and "+\
          " delivery is not null and state in ('manual')"+\
          " and company_id in (%s) and not block" 
    sql = sql % (date_min,date_max,del_min,del_max,comp_str)

    if data['form']['customer_id_1'] and not data['form']['customer_id_2']:
        data['form']['customer_id_2'] =  data['form']['customer_id_1']
    
    if data['form']['customer_id_1'] and data['form']['customer_id_2']:
        c_obj = pool.get('res.partner.customer')
        name1 = c_obj.browse(cr,uid,data['form']['customer_id_1']).name
        name2 = c_obj.browse(cr,uid,data['form']['customer_id_2']).name
        sql = sql + " and customer_id in (select id from res_partner_customer "+\
            " where name between '%s' and '%s')" % (name1,name2)
            

    if data['form']['partner_id']:
        sql = sql + " and partner_id=%d" % data['form']['partner_id']
    
    cr.execute(sql)
    ids = [ x[0] for x in cr.fetchall() ]
    amount,ids=self.filter(cr,uid,ids)

    data['form']['ids'] = ids
    data['form']['num_orders'] = len(ids)
    data['form']['amount_orders'] = amount

    if len(ids) > 100:
        data['form']['batch']=True
        invoice_fields['batch']= {'string':'Procés en Batch', 'type':'boolean', 'default': lambda x,y,z: True, 'readonly':True}
    else:
        data['form']['batch']=False
    return data['form']

class make_invoice(wizard.interface):
    def filter(self,cr,uid,nids):
        pool = pooler.get_pool(cr.dbname)
        ids=[]
        amount=0
        for order in pool.get('sale.order').browse(cr,uid,nids):
            if order.amount_total >= 0:
                ids.append(order.id)
                amount = amount + order.amount_total
        return amount,ids

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':inv_dates_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('total','Seleccionar Albarans')]}
        },
        'total': {
            'actions': [_get_totals],
            'result': {'type':'form', 'arch':inv_dates2_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('invoice','Facturar')]}
        },
        'invoice' : {
            'actions' : [make_invoices],
            'result' : {'type' : 'action',
                    'action' : view_invoices,
                    'state' : 'ask_print'}
        },
        'ask_print': {
            'actions': [],
            'result': {'type':'form', 'arch':inv_print_form, 'fields':invoice_fields, 'state':[('end','Sortir'),('print','Imprimir')]}
        },
        'print': {
            'actions': [_printInvoices],
            'result' : {'type' : 'print',
                    'report' : 'account.customer_invoice',
                    'get_id_from_action':True ,
                    'state' : 'end'}
        },
    }

class make_refunds(wizard.interface):
    def filter(self,cr,uid,nids):
        pool = pooler.get_pool(cr.dbname)
        ids=[]
        amount=0
        for order in pool.get('sale.order').browse(cr,uid,nids):
            if order.amount_total < 0:
                ids.append(order.id)
                amount = amount + order.amount_total
        return amount,ids

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':ref_dates_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('total','Seleccionar Albarans')]}
        },
        'total': {
            'actions': [_get_totals],
            'result': {'type':'form', 'arch':ref_dates2_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('invoice','Generar')]}
        },
        'invoice' : {
            'actions' : [make_invoices],
            'result' : {'type' : 'action',
                    'action' : view_invoices,
                    'state' : 'ask_print'}
        },
        'ask_print': {
            'actions': [],
            'result': {'type':'form', 'arch':ref_print_form, 'fields':invoice_fields, 'state':[('end','Sortir'),('print','Imprimir')]}
        },
        'print': {
            'actions': [_printInvoices],
            'result' : {'type' : 'print',
                    'report' : 'account.customer_invoice',
                    'get_id_from_action':True ,
                    'state' : 'end'}
        },
    }

make_invoice("carreras.make_invoices")
make_refunds("carreras.make_refunds")
