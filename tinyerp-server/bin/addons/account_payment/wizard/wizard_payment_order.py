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
import wizard
import pooler
from tools.misc import UpdateableStr



FORM = UpdateableStr()

FIELDS = {
	'entries': {'string':'Entries', 'type':'many2many',
		'relation': 'account.move.line',},
}


def search_entries(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	line_obj = pool.get('account.move.line')

	# Search for move line to pay:
	line_ids = line_obj.search(cr, uid, [
		('reconcile_id', '=', False),
		('amount_to_pay', '>', 0)], context=context)

	FORM.string = '''<?xml version="1.0"?>
<form string="Populate Payment:">
	<field name="entries" colspan="4" height="300" width="800" nolabel="1"
		domain="[('id', 'in', [%s])]"/>
</form>''' % (','.join([str(x) for x in line_ids]))
	return {'entries': line_ids}

def create_payment(self, cr, uid, data, context):
	line_ids= data['form']['entries'][0][2]
	if not line_ids: return {}

	pool= pooler.get_pool(cr.dbname)
	order_obj = pool.get('payment.order')
	line_obj = pool.get('account.move.line')

	payment = order_obj.browse(cr, uid, data['id'],
			context=context)
	t = payment.mode and payment.mode.type.code or 'manual'
	line2bank= pool.get('account.move.line').line2bank(cr, uid,
			line_ids, t, context)

	## Finally populate the current payment with new lines:
	for line in line_obj.browse(cr, uid, line_ids, context=context):
		pool.get('payment.line').create(cr,uid,{
			'move_line_id': line.id,
			'amount_currency': line.amount_to_pay,
			'bank_id': line2bank.get(line.id),
			'order_id': payment.id,
			}, context=context)
	return {}


class wizard_payment_order(wizard.interface):
	"""
	Create a payment object with lines corresponding to the account move line
	to pay according to the date and the mode provided by the user.
	Hypothesis:
	- Small number of non-reconcilied move line , payment mode and bank account type,
	- Big number of partner and bank account.

	If a type is given, unsuitable account move lines are ignored.
	"""
	states = {
		'init': {
			'actions': [search_entries],
			'result': {
				'type': 'form',
				'arch': FORM,
				'fields': FIELDS,
				'state': [
					('end','_Cancel'),
					('create','_Add to payment order', '', True)
				]
			},
		 },
		'create': {
			'actions': [],
			'result': {
				'type': 'action',
				'action': create_payment,
				'state': 'end'}
			},
		}

wizard_payment_order('populate_payment')


