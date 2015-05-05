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
  Gestió de comissions
"""
import time
import wizard
import pooler 

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

limits_form = '''<?xml version="1.0"?>
<form string="Càlcul de Comissions">
    <separator string="Límits de la selecció" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" nolabel="1"/>
</form>'''
totals_form = '''<?xml version="1.0"?>
<form string="Càlcul de Comissions">
    <separator string="Límits de la selecció" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="date_start" readonly="1"/>
    <field name="date_end" readonly="1" nolabel="1"/>
    <separator string="Càlcul de les Comissions" colspan="4"/>
    <field name="albarans" readonly="1" colspan="4"/>
</form>'''
end_form = '''<?xml version="1.0"?>
<form string="Càlcul de Comissions">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''

limits_form2 = '''<?xml version="1.0"?>
<form string="Tancament de les Liquidacions">
    <separator string="Límits de la selecció" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" nolabel="1"/>
    <separator string="Liquidació" colspan="4"/>
    <field name="date" required="1"/>
</form>'''
totals_form2 = '''<?xml version="1.0"?>
<form string="Tancament de les Liquidacions">
    <separator string="Límits de la selecció" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="date_start" readonly="1"/>
    <field name="date_end" readonly="1" nolabel="1"/>
    <separator string="Marcar els albarans seleccionats" colspan="4"/>
    <field name="date" required="1" readonly="1"/>
    <newline />
    <field name="albarans" readonly="1"/>
</form>'''
end_form2 = '''<?xml version="1.0"?>
<form string="Tancament de les Liquidacions">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''

limits_fields = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'date_start': {'string': 'Data de Factura','type': 'date',},
    'date_end': {'string': '-','type': 'date', 'required':True,},
    'albarans': {'string': 'Albarans Seleccionats','type': 'integer',},
    'date': {'string': 'Data de la Liquidació','type': 'date',},
}

class wizard_comission_calculation(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        data['form']['company_id'] = user.company_id.id
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date - RelativeDateTime(days=1)
        data['form']['date_end'] = date.strftime("%Y-%m-%d")
        
        return data['form']

    def _totals(self,cr,uid,data,context):
        pool = pooler.get_pool(cr.dbname)
        
        query=  "SELECT r.order_id FROM sale_order o, sale_order_invoice_rel r, account_invoice i " +\
                "WHERE i.company_id = '%d' AND o.id=r.order_id AND i.id=r.invoice_id " +\
                "AND o.date_comission IS NULL " +\
                "AND i.state <> 'cancel' AND " +\
                "(o.block_comission IS NULL OR o.block_comission = False)"

        form=data['form']
        if form['date_start']:
            query=query + " AND i.date_invoice BETWEEN '%s' AND '%s'"
            query= query % (form['company_id'],form['date_start'],form['date_end'])
        else:
            query= query + " AND i.date_invoice <= '%s'"
            query= query % (form['company_id'],form['date_end'])

        cr.execute(query)
        form['ids']=[ row[0] for row in cr.fetchall() ]
        form['albarans']=len(form['ids'])
        return data['form']

    def _process(self,cr,uid,data,context):
        pool = pooler.get_pool(cr.dbname)
        pool.get('sale.order').set_comission(cr,uid,data['form']['ids'])
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form, 'fields':limits_fields, 'state':[('end','Cancelar'),('select','Selecciona') ]}
        },
        'select': {
            'actions': [_totals],
            'result': {'type':'form', 'arch':totals_form, 'fields':limits_fields, 'state':[('end','Cancelar'),('compute','Càlcul') ]}
        },
        'compute': {
            'actions': [_process],
            'result': {'type':'form', 'arch':end_form, 'fields':limits_fields, 'state':[('end','Tanca')]}
        },
    }

class wizard_date_close(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        data['form']['company_id'] = user.company_id.id
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date - RelativeDateTime(days=1)
        data['form']['date_end'] = date.strftime("%Y-%m-%d")
        data['form']['date'] = date.strftime("%Y-%m-%d")
        
        return data['form']

    def _totals(self,cr,uid,data,context):
        pool = pooler.get_pool(cr.dbname)
        
        query=  "SELECT r.order_id FROM sale_order o, sale_order_invoice_rel r, account_invoice i " +\
                "WHERE i.company_id = '%d' AND o.id=r.order_id AND i.id=r.invoice_id " +\
                "AND o.date_comission IS NULL " +\
                "AND i.state <> 'cancel' AND " +\
                "(o.block_comission IS NULL OR o.block_comission = False)"

        form=data['form']
        if form['date_start']:
            query=query + " AND i.date_invoice BETWEEN '%s' AND '%s'"
            query= query % (form['company_id'],form['date_start'],form['date_end'])
        else:
            query= query + " AND i.date_invoice <= '%s'"
            query= query % (form['company_id'],form['date_end'])

        cr.execute(query)
        form['ids']=[ row[0] for row in cr.fetchall() ]
        form['albarans']=len(form['ids'])
        return data['form']

    def _process(self,cr,uid,data,context):
        pool = pooler.get_pool(cr.dbname)
        pool.get('sale.order').close_liquidation(cr,uid,data['form']['ids'],data['form']['date'])
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form2, 'fields':limits_fields, 'state':[('end','Cancela'),('select','Selecciona') ]}
        },
        'select': {
            'actions': [_totals],
            'result': {'type':'form', 'arch':totals_form2, 'fields':limits_fields, 'state':[('end','Cancela'),('close','Marca') ]}
        },
        'close': {
            'actions': [_process],
            'result': {'type':'form', 'arch':end_form2, 'fields':limits_fields, 'state':[('end','Tanca')]}
        },
    }

wizard_date_close('carreras.date.close')
wizard_comission_calculation('carreras.comission.calculation')
