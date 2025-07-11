##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import pooler

pay_form = '''<?xml version="1.0"?>
<form string="Pay invoice">
	<field name="amount"/>
	<field name="journal_id"/>
	<field name="period_id"/>
</form>'''

pay_fields = {
	'amount': {'string': 'Amount paid', 'type':'float', 'required':True},
	'journal_id': {'string': 'Journal', 'type': 'many2one', 'relation':'account.journal', 'required':True, 'domain':[('type','=','cash')]},
	'period_id': {'string': 'Period', 'type': 'many2one', 'relation':'account.period', 'required':True},
}

def _pay_and_reconcile(self, cr, uid, data, context):
	service = netsvc.LocalService("object_proxy")
	form = data['form']
	period_id = form.get('period_id', False)
	journal_id = form.get('journal_id', False)
	writeoff_account_id = form.get('writeoff_acc_id', False)
	writeoff_journal_id = form.get('writeoff_journal_id', False)
	pool = pooler.get_pool(cr.dbname)
	acc_id = pool.get('account.journal').browse(cr, uid, journal_id, context).default_credit_account_id.id
	if not acc_id:
		raise wizard.except_wizard('Error !', 'Your journal must have a default credit and debit account.')
	service.execute(cr.dbname, uid, 'account.invoice', 'pay_and_reconcile', [data['id']], form['amount'], acc_id, period_id, journal_id, writeoff_account_id, period_id, writeoff_journal_id, context)
	return {}

def _trans_reconcile(self, cr, uid, data, context):
	service = netsvc.LocalService("object_proxy")
	return {}

def _wo_check(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
	if pool.get('res.currency').is_zero(cr, uid, invoice.currency_id,
			(data['form']['amount'] - invoice.amount_total)):
		return 'reconcile'
	return 'addendum'

_transaction_add_form = '''<?xml version="1.0"?>
<form string="Information addendum">
	<separator string="Write-Off Move" colspan="4"/>
	<field name="writeoff_acc_id"/>
	<field name="writeoff_journal_id"/>
</form>'''

_transaction_add_fields = {
	'writeoff_acc_id': {'string':'Write-Off account', 'type':'many2one', 'relation':'account.account', 'required':True},
	'writeoff_journal_id': {'string': 'Write-Off journal', 'type': 'many2one', 'relation':'account.journal', 'required':True},
}

def _get_value_addendum(self, cr, uid, data, context={}):
	return {}

def _get_period(self, cr, uid, data, context={}):
	pool = pooler.get_pool(cr.dbname)
	ids = pool.get('account.period').find(cr, uid, context=context)
	period_id = False
	if len(ids):
		period_id = ids[0]
	invoice = pool.get('account.invoice').browse(cr, uid, data['id'], context)
	if invoice.state == 'draft':
		raise wizard.except_wizard('Error !', 'Can not pay draft invoice.')
	return {'period_id': period_id, 'amount': invoice.amount_total}

class wizard_pay_invoice(wizard.interface):
	states = {
		'init': {
			'actions': [_get_period],
			'result': {'type':'form', 'arch':pay_form, 'fields':pay_fields, 'state':[('end','Cancel'),('writeoff_check','Pay Invoice')]}
		},
		'writeoff_check': {
			'actions': [],
			'result' : {'type': 'choice', 'next_state': _wo_check }
		},
		'addendum': {
			'actions': [_get_value_addendum],
			'result': {'type': 'form', 'arch':_transaction_add_form, 'fields':_transaction_add_fields, 'state':[('end','Cancel'),('reconcile','Pay and reconcile')]}
		},
		'reconcile': {
			'actions': [_pay_and_reconcile],
			'result': {'type':'state', 'state':'end'}
		}
	}
wizard_pay_invoice('account.invoice.pay')

