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
   Llistat del 347

"""
import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Llistat per a la declaració model 347">
    <field name="company_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" />
    <field name="order" />
    <field name="type" />
    <field name="limit" />
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
    'order': {
        'string': 'Ordent per',
        'type': 'selection',
        'required': True,
        'selection': [('ref','NIF'),('name','Nom'),('amount','Import Descendent')]
    },
    'type': {
        'string': 'Intervinents',
        'type': 'selection',
        'required': True,
        'selection': [('out_invoice','Clients'),('in_invoice','Proveïdors')]
    },
    'limit': {
        'string': 'Import Límit',
        'type': 'float',
        'required': True,
    },
}

class wizard_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        data['form']['order'] = 'ref'
        data['form']['type'] = 'out_invoice'
        data['form']['limit'] = 3000.00

        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')

        return data['form']

        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.report_347', 'state':'end'}
        }
    }
wizard_report('carreras.report_347')

