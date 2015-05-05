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
  Demana un compte i si tots o pendents i llista o 
  mostra per pantalla els efectes del compte

"""
import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Consulta de efectes d'un compte">
    <field name="account_id"/>
    <newline/>
    <field name="state"/>
</form>'''

    
select_fields = {
    'account_id': {
        'string': 'Compte',
        'type': 'many2one',
        'relation': 'account.account',
        'domain': [('type','=','receivable')],
        'required': True,
    },
    'state': {
        'string': 'Estat',
        'type': 'selection',
        'selection':[('pending','Pendents'),('all','Tots')],
        'default':'pending',
    },
}

class wizard_customer_receivable(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.receivable', 'tree'))
        view_res = cr.fetchone()
        if form['state'] == 'pending':
            domain = "[('account_id','=',%d),('state','=','pending')]" % (form['account_id'])
            context = "{'account_id':%d,'state':'pending'}" % (form['account_id'])
        else:
            domain = "[('account_id','=',%d)]" % (form['account_id'])
            context = "{'account_id':%d}" % (form['account_id'])
        acc = pool.get('account.account').browse(cr,uid,form['account_id'])
        return {
            'name': 'Cartera de %s ' % acc.name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.receivable',
            'view_id': view_res,
            'domain': domain,
            'context': context,
            'type': 'ir.actions.act_window'
        }
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('view','Veure'),('report','Imprimir') ]}
        },
        'view': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'customer.receivable', 'state':'end'}
        }
    }
wizard_customer_receivable('customer.receivable')

