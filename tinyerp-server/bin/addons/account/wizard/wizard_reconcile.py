##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import wizard
import netsvc
import time
import osv
import pooler

_transaction_form = '''<?xml version="1.0"?>
<form string="Reconciliation">
	<separator string="Reconciliation transactions" colspan="4"/>
	<field name="trans_nbr"/>
	<newline/>
	<field name="credit"/>
	<field name="debit"/>
	<separator string="Write-Off" colspan="4"/>
	<field name="writeoff"/>
</form>'''

_transaction_fields = {
	'trans_nbr': {'string':'# of Transaction', 'type':'integer', 'readonly':True},
	'credit': {'string':'Credit amount', 'type':'float', 'readonly':True},
	'debit': {'string':'Debit amount', 'type':'float', 'readonly':True},
	'writeoff': {'string':'Write-Off amount', 'type':'float', 'readonly':True},
}

def _trans_rec_get(self, cr, uid, data, context={}):
	service = netsvc.LocalService("object_proxy")
	res = filter(lambda x: not x['reconcile_id'], service.execute(cr.dbname, uid, 'account.move.line', 'read', data['ids']))
	credit = debit = 0
	account_id = False
	for trans in res:
		credit += trans['credit']
		debit += trans['debit']
		account_id = trans['account_id'][0]
	return {'trans_nbr': len(res), 'account_id': account_id, 'credit': credit, 'debit': debit, 'writeoff': debit - credit}

def _trans_rec_reconcile(self, cr, uid, data, context):
	service = netsvc.LocalService("object_proxy")
	form = data['form']
	account_id = form.get('writeoff_acc_id', False)
	period_id = form.get('period_id', False)
	journal_id = form.get('journal_id', False)
	service.execute(cr.dbname, uid, 'account.move.line', 'reconcile', data['ids'], 'manual', account_id, period_id, journal_id, context)
	return {}

def _wo_check(self, cr, uid, data, context):
	if data['form']['writeoff'] == 0:
		return 'reconcile'
	return 'addendum'

_transaction_add_form = '''<?xml version="1.0"?>
<form string="Information addendum">
	<separator string="Write-Off Move" colspan="4"/>
	<field name="journal_id"/>
	<field name="period_id"/>
	<field name="writeoff_acc_id" domain="[('type', '&lt;&gt;', 'view')]"/>
</form>'''

_transaction_add_fields = {
	'journal_id': {'string': 'Write-Off Journal', 'type': 'many2one', 'relation':'account.journal', 'required':True},
	'period_id': {'string': 'Write-Off Period', 'type': 'many2one', 'relation':'account.period', 'required':True},
	'writeoff_acc_id': {'string':'Write-Off account', 'type':'many2one', 'relation':'account.account', 'required':True},
}

def _trans_rec_addendum(self, cr, uid, data, context={}):
	pool = pooler.get_pool(cr.dbname)
	ids = pool.get('account.period').find(cr, uid, context=context)
	period_id = False
	if len(ids):
		period_id = ids[0]
	return {'period_id':period_id}


class wiz_reconcile(wizard.interface):
	states = {
		'init': {
			'actions': [_trans_rec_get],
			'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel'),('writeoff_check','Reconcile')]}
		},
		'writeoff_check': {
			'actions': [],
			'result' : {'type' : 'choice', 'next_state': _wo_check }
		},
		'addendum': {
			'actions': [_trans_rec_addendum],
			'result': {'type': 'form', 'arch':_transaction_add_form, 'fields':_transaction_add_fields, 'state':[('end','Cancel'),('reconcile','Reconcile')]}
		},
		'reconcile': {
			'actions': [_trans_rec_reconcile],
			'result': {'type': 'state', 'state':'end'}
		}
	}
wiz_reconcile('account.move.line.reconcile')

