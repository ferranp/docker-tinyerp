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
  Llistat de factures de clients
  Es mostra l'empresa 
  Es seleccionen els limits
"""
import time
import wizard
import pooler 

invoice_form = '''<?xml version="1.0"?>
<form string="Llistat de factures a Clients">
    <field name="company_id" colspan="4"/>
    <separator string="Límits de seleccio de les factures" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" />
    <field name="state" colspan="4"/>
</form>'''

out_invoice_form = '''<?xml version="1.0"?>
<form string="Llistat IVA de Factures Emeses">
    <field name="company_id" colspan="4"/>
    <separator string="Límits de seleccio de les factures" colspan="4"/>
    <field name="sequence_id" />
    <newline />
    <field name="date_start" />
    <field name="date_end" />
</form>'''

in_invoice_form = '''<?xml version="1.0"?>
<form string="Llistat IVA de Factures a Rebudes">
    <field name="company_id" colspan="4"/>
    <separator string="Límits de seleccio de les factures" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" />
</form>'''

select_fields = {
    'company_id': {
        'string': 'Empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'readonly': True,
    },
    'date_start': {
        'string': 'Data desde',
        'type': 'date',
        'required': True,
    },
    'date_end': {
        'string': 'Data fins a',
        'type': 'date',
        'required': True,
    },
    'state': {
        'string': 'Estat',
        'type': 'selection',
        'selection': [('all','Tots'),('draft','En esborrany'),
                      ('open','Pendent'),('paid','Pagat')],
    },
    'type': {
        'string': 'Tipus',
        'type': 'char',
    },
    'sequence_id': {
        'string': 'Numerador',
        'type': 'many2one',
        'relation': 'ir.sequence',
        #'domain': [('code','in',['account.invoice.out_invoice','account.invoice.out_refund'])]
        'domain': [('code','=','account.invoice.out_invoice')]
    },
}

class wizard_invoice_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        data['form']['state'] = 'all'
        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')
        #data['form']['type']=["out_invoice","out_refund"]
        data['form']['type']=["out_invoice"]
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':invoice_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.invoice_report', 'state':'end'}
        }
    }

class wizard_out_invoice(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        #data['form']['state'] = 'paid'
        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')
        #data['form']['type']=["out_invoice","out_refund"]
        data['form']['type']=["out_invoice"]
        data['form']['order']='date_invoice,number'
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':out_invoice_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.out_invoice_report', 'state':'end'}
        }
    }

class wizard_in_invoice(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        #data['form']['state'] = 'paid'
        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')
        #data['form']['type']=["in_invoice","in_refund"]
        data['form']['type']=["in_invoice"]
        data['form']['order']='date_invoice,number'
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':in_invoice_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.in_invoice_report', 'state':'end'}
        }
    }


wizard_invoice_report('carreras.invoice_report')
wizard_out_invoice('carreras.out_invoice_report')
wizard_in_invoice('carreras.in_invoice_report')
