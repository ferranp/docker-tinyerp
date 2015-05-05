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
import time
import wizard
import pooler 

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

form1 = '''<?xml version="1.0"?>
<form string="Estadística per Tractament">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="date_1" required="1"/>
    <field name="date_2" required="1" nolabel="1"/>
    <field name="shop_id" />
    <label string="[En blanc tots]" align="0.0"/>
    <field name="product_1" required="1"/>
    <field name="product_2" required="1" nolabel="1" />
    <field name="customer_id" />
    <label string="[En blanc tots]" align="0.0"/>
</form>'''

form2 = '''<?xml version="1.0"?>
<form string="Estadística de Clients">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="customer_1" required="1"/>
    <field name="customer_2" required="1" nolabel="1"/>
    <field name="product_1" required="1"/>
    <field name="product_2" required="1" nolabel="1" />
    <field name="date_1" required="1"/>
    <field name="date_2" required="1" nolabel="1"/>
    <field name="shop_id" />
    <label string="[En blanc tots]" align="0.0"/>
    <newline />
    <field name="order" />
</form>'''

fields = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'date_1': {'string': 'Període', 'type': 'date'},
    'date_2': {'string': '-', 'type': 'date'},
    'shop_id': {'string': 'Centre de Treball', 'type': 'many2one', 'relation': 'sale.shop'},
    'product_1': {'string': 'Tractaments', 'type': 'char', 'size': 2},
    'product_2': {'string': '-', 'type': 'char', 'size': 2},
    'customer_1': {'string': 'Clients', 'type': 'char', 'size': 4},
    'customer_2': {'string': '-', 'type': 'char', 'size': 4},
    'customer_id': {'string': 'Client', 'type': 'many2one', 'relation': 'res.partner.customer'},
    'order': {'string':'Ordre','type':'selection','size':5,'selection':[('code','Codi'),('name','Nom,Codi')]},
}

class wizard_estadis_product(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        data['form']['company_id'] = user.company_id.id
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1,month=1) 
        data['form']['date_1'] = date.strftime("%Y-%m-%d")
        date = date + RelativeDateTime(day=31,month=12) 
        data['form']['date_2'] = date.strftime("%Y-%m-%d")
        
        data['form']['product_1'] = '00'
        data['form']['product_2'] = '99'
        return data['form']

    def _get_selection_ids(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        s=[('default_code','>=',data['form']['product_1']),('default_code','<=',data['form']['product_2']),('categ_id','ilike','Vendes')]
        data['form']['ids']=pool.get('product.product').search(cr,uid,s)
        return data['form']
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form1, 'fields':fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'estadis.product', 'get_id_from_action':True, 'state':'end'}
        },
    }

class wizard_estadis_customer(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        data['form']['company_id'] = user.company_id.id
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date + RelativeDateTime(days=-1) 
        data['form']['date_2'] = date.strftime("%Y-%m-%d")
        date = date + RelativeDateTime(day=1) 
        data['form']['date_1'] = date.strftime("%Y-%m-%d")
        data['form']['product_1'] = '00'
        data['form']['product_2'] = '99'
        data['form']['customer_1'] = '0000'
        data['form']['customer_2'] = '9999'
        data['form']['order'] = 'code'
        return data['form']

    def _get_selection_ids(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        s=[('default_code','>=',data['form']['product_1']),('default_code','<=',data['form']['product_2']),('categ_id','ilike','Vendes')]
        data['form']['ids']=pool.get('product.product').search(cr,uid,s)
        return data['form']
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form2, 'fields':fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'estadis.customer', 'get_id_from_action':True, 'state':'end'}
        },
    }

wizard_estadis_product('carreras.estadis.product')
wizard_estadis_customer('carreras.estadis.customer')
