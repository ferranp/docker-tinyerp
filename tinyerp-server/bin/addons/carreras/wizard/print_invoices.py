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
"""
  Imprimir factures amb batch

"""
import wizard
import netsvc
import pooler
import netsvc
import threading
import time

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

logger = netsvc.Logger()

dates_form = '''<?xml version="1.0"?>
<form string="Impressió de factures">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="customer_id_1"/>
    <field name="customer_id_2"/>
    <newline/>
    <field name="date_min" />
    <field name="date_max" />
    <field name="invoice_min" />
    <field name="invoice_max" />
    <newline/>
    <field name="obs" colspan="4"/>
    <separator string="Originals / Còpies" colspan="4"/>
    <field name="original" />
    <label string="Es farà l'original i les còpies segons el client" />
    <newline/>
    <field name="num_copies" />
    <label string="Informar només si no s'imprimeix l'original" />
    <newline/>
    <field name="printer" />
</form>'''

dates2_form = '''<?xml version="1.0"?>
<form string="Impressió de factures">
    <separator string="Factures a Imprimir" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="num_invs" colspan="4"/>
</form>'''

print_form = '''<?xml version="1.0"?>
<form string="Confirmació de factures">
    <separator string="Imprimir Factures ?" colspan="4"/>
</form>'''

message_form = '''<?xml version="1.0"?>
<form string="Impressió de factures">
    <label string="Impressió Iniciada ..." />
</form>'''

invoice_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'customer_id_1': {'string': 'De Codi de Client', 'type': 'many2one', 'relation': 'res.partner.customer'},    
    'customer_id_2': {'string': 'A Codi de Client', 'type': 'many2one', 'relation': 'res.partner.customer'},    
    'partner_id': {'string': 'Client', 'type': 'many2one', 'relation': 'res.partner'},    
    'date_min': {'string': 'De la Data Factura', 'type': 'date'},
    'date_max': {'string': 'A la Data Factura', 'type': 'date'},
    'invoice_min': {'string': "De la Factura", 'type': 'char'},
    'invoice_max': {'string': "A la Factura", 'type': 'char'},
    'obs': {'string': "Observacions", 'type': 'text'},
    'num_invs': {'string': "Factures Seleccionades", 'type': 'integer', 'readonly': True},
    'original' : {'string':'Imprimir Originals', 'type':'boolean', 'default': lambda x,y,z: True},
    'num_copies' : {'string':'Numero de copies', 'type':'integer', 'default': lambda x,y,z: 1},
    'printer' : {'string':'Impressora', 'type':'many2one', 'relation':'printjob.printers'},
}

class BatchInvoices(threading.Thread):
    def __init__(self,cr, uid, data, context):
        threading.Thread.__init__(self)
        logger.notifyChannel("info", netsvc.LOG_INFO,"printing batch invoices ids=%s ..." % str(data['form']['ids']))
        self.dbname = cr.dbname
        self.uid = uid
        self.data = data
        self.context = context

    def run(self):
        cr = pooler.get_db(self.dbname).cursor()
        pool = pooler.get_pool(self.dbname)
        report_obj = netsvc.LocalService('report')
        
        i_obj = pool.get('account.invoice')

        password=pool.get('res.users').browse(cr,self.uid,self.uid).password
        
        ids=[]
        self.data['form']['print_batch']=True
        j_obj=pool.get('printjob.job')
        printing=False

        for id in self.data['form']['ids']:
            copies = 0
            if not self.data['form']['original']:
                copies = self.data['form']['num_copies']
            else:
                report_id=report_obj.report(self.dbname, self.uid, password,
		    'account.customer_invoice_original', [id], self.data, self.context)
                printing=True
                while printing:
                    time.sleep(0.1)
                    cr = pooler.get_db(self.dbname).cursor()
                    report=j_obj.read(cr,self.uid,[report_id],['state'])
                    if report[0]['state'] != 'draft':
                        printing=False

                inv = i_obj.browse(cr,self.uid,id)
                if inv and inv.partner_id.customer_ids:
                    copies = inv.partner_id.customer_ids[0].invoice_copies - 1

            if copies > 0:
                printing=True
                for i in range(copies):
                    report_id=report_obj.report(self.dbname, self.uid, password, 
		        'account.customer_invoice_copia', [id], self.data, self.context)
                while printing:
                    time.sleep(0.1)
                    cr = pooler.get_db(self.dbname).cursor()
                    report=j_obj.read(cr,self.uid,[report_id],['state'])
                    if report[0]['state'] != 'draft':
                        printing=False
        return

class print_invoice(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]

        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1,month=1) 
        data['form']['date_min'] = date.strftime("%Y-%m-%d")
        date = date + RelativeDateTime(day=31,month=12) 
        data['form']['date_max'] = date.strftime("%Y-%m-%d")

        child_c = pool.get('res.company')._get_company_children(cr,uid,data['form']['company_id'])
        
        comp_str = ",".join([str(c) for c in child_c])

        data['form']['invoice_min'] = ''
        data['form']['invoice_max'] = '99999999'

        data['form']['obs'] = ''
        
        self.ini=0
        return data['form']

    def _get_totals(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]
        s_obj = pool.get('account.invoice')
        
        date_min = data['form']['date_min']
        date_max = data['form']['date_max']

        inv_min = data['form']['invoice_min'] or ' '
        inv_max = data['form']['invoice_max']
        
        child_c = pool.get('res.company')._get_company_children(cr,uid,data['form']['company_id'])
        
        comp_str = ",".join([str(c) for c in child_c])
        
        sql = "select id from account_invoice where "+\
              " date_invoice between '%s' and '%s' and "+\
              " name between '%s' and '%s' "+\
              " and company_id in (%s) " 
        sql = sql % (date_min,date_max,inv_min,inv_max,comp_str)

        if data['form']['customer_id_1'] and not data['form']['customer_id_2']:
            data['form']['customer_id_2'] =  data['form']['customer_id_1']
        
        if data['form']['customer_id_1'] and data['form']['customer_id_2']:
            c_obj = pool.get('res.partner.customer')
            name1 = c_obj.browse(cr,uid,data['form']['customer_id_1']).name
            name2 = c_obj.browse(cr,uid,data['form']['customer_id_2']).name
            sql = sql + " and partner_id in (select partner_id from res_partner_customer "+\
                " where name between '%s' and '%s')" % (name1,name2)
                

        if data['form']['partner_id']:
            sql = sql + " and partner_id=%d" % data['form']['partner_id']

        sql= sql + " order by number"

        cr.execute(sql)
        ids = [ x[0] for x in cr.fetchall() ]

        data['form']['ids'] = ids
        data['form']['num_invs'] = len(ids)
        return data['form']

    def _print_batch(self, cr, uid, data, context):
        if len(data['form']['ids']) == 0:
            return data['form']
        if not data['form']['original'] and data['form']['num_copies'] == 0:
            return data['form']

        t = BatchInvoices(cr,uid,data,context)
        t.start()
        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('total','Seleccionar Factures')]}
        },
        'total': {
            'actions': [_get_totals],
            'result': {'type':'form', 'arch':dates2_form, 'fields':invoice_fields, 'state':[('end','Cancelar'),('end_msg','Imprimir')]}            
        },
        'end_msg': {
            'actions': [_print_batch],
            'result': {'type':'form', 'arch':message_form, 'fields':invoice_fields, 'state':[('end','Tancar')]}
        },
    }

print_invoice("carreras.print_invoices")
