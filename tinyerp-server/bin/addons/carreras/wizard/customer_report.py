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
  Llistat de Clients

"""
import time
import wizard
import pooler 

report_form = '''<?xml version="1.0"?>
<form string="Llistat de Clients">
    <field name="company_id" colspan="4" />
    <field name="name" colspan="4" />
    <field name="code_start" />
    <field name="code_end" />
</form>'''
risk_form = '''<?xml version="1.0"?>
<form string="Risc de Clients">
    <field name="company_id" colspan="4" />
    <field name="name" colspan="4" />
    <field name="code_start" />
    <field name="code_end" />
</form>'''


select_fields = {
    'company_id': {
        'string': 'Empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'readonly': True,
    },
    'name': {
        'string': 'El Nom Conte',
        'type': 'char',
    },
    'code_start': {
        'string': 'Codi desde',
        'type': 'char',
        'required': True,
    },
    'code_end': {
        'string': 'Codi fins a',
        'type': 'char',
        'required': True,
    },
}

class wizard_customer_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        data['form']['code_start'] = '0000'
        data['form']['code_end'] = '9999'
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':report_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'carreras.customer_report', 'state':'end'}
        }
    }
    
class wizard_customer_risk_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        data['form']['code_start'] = '0000'
        data['form']['code_end'] = '9999'
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':risk_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'carreras.customer_risk_report', 'state':'end'}
        }
    }

wizard_customer_report('carreras.customer_report')
wizard_customer_risk_report('carreras.customer_risk_report')

