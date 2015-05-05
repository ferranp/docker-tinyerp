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
#
# 26.03.10 No tractar efectes no actius
#

import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Quadre del saldo de comptes amb cartera">
    <field name="company_id" colspan="4"/>
    <field name="account_start_id" colspan="4"/>
    <field name="account_end_id" colspan="4"/>
</form>'''


select_fields = {
    'account_start_id': {
        'string': 'Compte desde',
        'type': 'many2one',
        'relation': 'account.account',
        'required': True,
        'domain': [('type','=','receivable')],
    },
    'account_end_id': {
        'string': 'Compte fins a',
        'type': 'many2one',
        'relation': 'account.account',
        'required': True,
        'domain': [('type','=','receivable')],
    },
    'company_id': {
        'string': 'Empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'readonly': True,
    },
}

class wizard_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        c_id = pool.get('res.users').browse(cr, uid, uid).company_id.id
        cr.execute("select max(code),min(code) from account_account " +
                    "where type='receivable' and active and company_id = %d" % c_id )
        max,min = cr.fetchone()
        max = pool.get('account.account').search(cr,uid,[('code','=',max)])[0]
        min = pool.get('account.account').search(cr,uid,[('code','=',min)])[0]
        data['form']['account_start_id'] = min
        data['form']['account_end_id'] = max
        data['form']['company_id'] = c_id
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.receivable.match', 'state':'end'}
        }
    }
wizard_report('receivable.match')

