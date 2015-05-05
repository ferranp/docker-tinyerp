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
  Avisos d'efectes vençuts
"""
import time
import wizard
import pooler 

form1 = '''<?xml version="1.0"?>
<form string="Avisos d'efectes vençuts">
    <field name="account_id"/>
    <newline />
    <field name="channel_id"/>
</form>'''
fields1 = {
    'account_id': {
        'string': 'Compte',
        'type': 'many2one',
        'relation': 'account.account',
        'domain': [('type','=','receivable')],
        'required': True,
    },
    'channel_id': {
        'string': 'Canal',
        'type': 'many2one',
        'relation': 'account.receivable.channel',
        'required' : True,
    },
}

form2 = '''<?xml version="1.0"?>
<form string="Avisos d'efectes vençuts">
    <field name="receivables" colspan="4"/>
</form>'''
fields2 = {
    'receivables': {
        'string': 'Efectes vençuts',
        'type': 'many2many',
        'relation': 'account.receivable',
        'help': 'En blanc tots els efectes vençuts'
    },
}

class wizard_customer_notice(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        user_obj=pooler.get_pool(cr.dbname).get('res.users')
        channel_id= user_obj.browse(cr, uid, uid).company_id.channel_id
        data['form']['channel_id']=channel_id.id
        return data['form']

    def _set_receivables_domain(self, cr, uid, data, context):
        fields2['receivables']['domain']=[('account_id','=',data['form']['account_id']),('state','=','pending')]
        return data['form']
    
    def _validate(self, cr, uid, data, context):
        receivables=data['form']['receivables'][0][2]
        if len(receivables) == 0:
            raise wizard.except_wizard('No es genera l\'avís', 
                "No s'ha escollit cap efecte")
        if len(receivables) > 10:
            raise wizard.except_wizard('No es genera l\'avís', 
                "Com a màxim es poden escollir 10 efectes")
        data['form']['ids']=receivables
        return data['form']
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form1, 'fields':fields1, 'state':[('end','Cancelar'),('receivables',"D'acord") ]}
        },
        'receivables': {
            'actions': [_set_receivables_domain], 
            'result': {'type':'form', 'arch':form2, 'fields':fields2, 'state':[('end','Cancelar'),('report',"Imprimir") ]}
        },
        'report': {
            'actions': [_validate],
            'result': {'type':'print','report':'customer.notice', 'get_id_from_action':True, 'state':'end'}
        }
    }
wizard_customer_notice('customer.notice')

