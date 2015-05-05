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

import time
import wizard
import pooler 

limits_form = '''<?xml version="1.0"?>
<form string="Límits de la selecció automàtica d'efectes">
    <separator string="Límits de la selecció automàtica d'efectes" colspan="4"/>
    <field name="maturity_from" />
    <field name="maturity_to" />
    <field name="account_id" colspan="4" />
    <field name="amount_max"/>
    <newline />
    <field name="type"/>
</form>'''

def get_types(self, cr, uid, context={}):
    obj = pooler.get_pool(cr.dbname).get('account.payment.term.type')
    ids = obj.search(cr, uid, [])
    res = obj.read(cr, uid, ids, ['code', 'name'], context)
    res = [(r['code'], r['name']) for r in res]
    return res

limits_fields = {
    'account_id': {'string': 'Compte','type': 'many2one','relation': 'account.account',},
    'maturity_from': {'string': 'Venciment desde','type': 'date',},
    'maturity_to': {'string': 'Venciment fins a','type': 'date',},
    'amount_max': {'string': 'Import Màxim Remesa','type': 'float',},
    'type': {'string': 'Tipus d\'Efecte','type': 'selection','selection':get_types},
}
conf_form = '''<?xml version="1.0"?>
<form string="Confirmació de selecció automàtica d'efectes">
    <label colspan="4" string="Confirma la incorporacio dels efectes a la remesa" />
    <field name="num" />
    <field name="amount" />
</form>'''

conf_fields = {
    'num': {'string': 'Efectes seleccionats','type': 'integer','readonly':True,},
    'amount': {'string': 'Import seleccionat','type': 'float','readonly':True,},
}

class wizard_remittance_receivables(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        #data['form']['maturity_from'] = time.strftime('%Y-%m-%d')
        #data['form']['maturity_from'] = time.strftime('%Y-%m-%d')
        pool = pooler.get_pool(cr.dbname)
        remesa = pool.get('account.receivable.remittance').read(cr,uid,[data['id']])[0]
        if remesa['state'] != 'draft':
            raise wizard.except_wizard(
                'No es poden seleccionar efectes', 
                "La remesa ha d'estar en esborrany")
        data['form']['maturity_from'] = '2000-01-01'
        data['form']['maturity_to'] = '2050-12-31'
        return data['form']

    def _select(self, cr, uid, data, context):
        form = data['form']
        pool = pooler.get_pool(cr.dbname)    
        r_obj = pool.get('account.receivable')
        
        limits = [('state','=','pending'),('remittance_id','=',False)]
        if form['maturity_from' ] and form['maturity_to']:
            limits.append(('date_maturity','>=',form['maturity_from' ]))
            limits.append(('date_maturity','<=',form['maturity_to' ]))
        if form.get('account_id'):
            limits.append(('account_id','=',form['account_id' ]))
        if form.get('type'):
            limits.append(('type','=',form['type']))

        ids = r_obj.search(cr,uid,limits)

        if form['amount_max'] > 0.0:
            amount = 0
            r_ids = []
            for e in r_obj.browse(cr,uid,ids):
                if ( amount + e.amount ) < form['amount_max']:
                    r_ids.append(e.id)
                    amount += e.amount
        else:
            r_ids = ids
            
        if len(r_ids) == 0:
            form['ids'] = r_ids
            form['num'] = len(r_ids)
            form['amount'] = 0.0
            raise wizard.except_wizard('Procés cancel·lat', "No s'ha seleccionat cap efecte")
            return form
        form['ids'] = r_ids
        form['num'] = len(r_ids)

        id_set = ",".join(map(lambda x:str(x),r_ids))
        cr.execute("select sum(amount) from account_receivable where id in ("+id_set+")")
        form['amount'] = cr.fetchone()[0]
        return form

    def _write(self, cr, uid, data, context):
        form = data['form']
        if 'ids' not in form or len(form['ids']) == 0:
            return {}

        pool = pooler.get_pool(cr.dbname)
        remesa = data['id']
        rec = {
            'remittance_id': remesa,
        }
        pool.get('account.receivable').write(cr,uid,form['ids'],rec)

        return {}

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form, 'fields':limits_fields, 'state':[('end','Cancel·lar'),('select','Seleccionar')]}
        },
        'select': {
            'actions': [_select], 
            'result': {'type':'form', 'arch':conf_form, 'fields':conf_fields, 'state':[('end','Cancel·lar'),('write','Confirmar')]}
        },
        'write': {
            'actions': [_write],
            'result': {'type':'state','state':'end' }
        }
    }
wizard_remittance_receivables('remittance.receivables')

