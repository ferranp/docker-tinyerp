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
  Confirmacio BATCH de factures

"""
import time
import wizard
import netsvc
import pooler 

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

dates_form = '''<?xml version="1.0"?>
<form string="Confirmació de factures">
    <field name="company_id" colspan="4"/>
    <field name="date_max" />
</form>'''

dates2_form = '''<?xml version="1.0"?>
<form string="Confirmació de factures">
    <field name="company_id" colspan="4"/>
    <field name="num_inv" colspan="4"/>
    <field name="amount_inv" colspan="4"/>
</form>'''

finish_form = '''<?xml version="1.0"?>
<form string="Confirmació de factures">
    <label string="Procés finalitzat"/>
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'date_max': {'string': 'Data Màxima Factures a Confirmar', 'type': 'date'},
    'num_inv': {'string': 'Numero Factures a Confirmar', 'type': 'integer', 'readonly': True},
    'amount_inv': {'string': 'Import Factures a Confirmar', 'type': 'float', 'readonly': True},
}

class wizard_invoice_confirm(wizard.interface):

    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']

        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date - RelativeDateTime(days=1)
        data['form']['date_max'] = date.strftime("%Y-%m-%d")

        return data['form']

    def _get_totals(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']

        i_obj = pool.get('account.invoice')
        s = []
        s.append(('state','=','draft'))
        s.append(('type','in',self.types))
        s.append(('date_invoice','<=',data['form']['date_max']))
        i_ids = i_obj.search(cr,uid,s,context=context)
        data['form']['num_inv'] = len(i_ids)
        amount = 0.0
        for inv in i_obj.browse(cr,uid,i_ids):
            amount = amount + inv.amount_total
        data['form']['amount_inv'] = amount
        
        return data['form']

    def _invoice_confirm(self, cr, uid, data, context):
        wf_service = netsvc.LocalService('workflow')
        pool = pooler.get_pool(cr.dbname)
        i_obj = pool.get('account.invoice')
        s = []
        s.append(('state','=','draft'))
        s.append(('type','in',self.types))
        s.append(('date_invoice','<=',data['form']['date_max']))
        logger = netsvc.Logger()
        for id in i_obj.search(cr,uid,s,context=context):
            obj=i_obj.browse(cr,uid,id)
            logger.notifyChannel("info", netsvc.LOG_INFO,str(obj.name)+" "+str(obj.state)+"->"+"open")
            wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_open', cr)
        #raise wizard.except_wizard('OK')
        return {}

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('total','Buscar Factures')]}
        },
        'total': {
            'actions': [_get_totals],
            'result': {'type':'form', 'arch':dates2_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('confirm','Confirmar Factures')]}
        },
        'confirm': {
            'actions': [_invoice_confirm], 
            'result': {'type':'state', 'state':'finish'}
        },
        'finish': {
            'actions': [], 
            'result': {'type':'form', 'arch':finish_form, 'fields':{}, 'state':[('end','Tanca')]}
        }
    }

class wizard_customer_invoice_confirm(wizard_invoice_confirm):
    types = ['out_invoice']
    #types = ['out_invoice','out_refund']

class wizard_supplier_invoice_confirm(wizard_invoice_confirm):
    types = ['in_invoice']
    #types = ['in_invoice','in_refund']


wizard_customer_invoice_confirm('carreras.invoice_confirm')

wizard_supplier_invoice_confirm('carreras.supplier_invoice_confirm')

