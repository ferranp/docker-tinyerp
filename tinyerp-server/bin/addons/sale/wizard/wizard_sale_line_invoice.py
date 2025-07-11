##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: make_invoice.py 1070 2005-07-29 12:41:24Z nicoe $
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
import ir
import pooler

invoice_form = """<?xml version="1.0"?>
<form string="Create invoices">
	<separator colspan="4" string="Do you really want to create the invoices ?" />
	<field name="grouped" />
</form>
"""

invoice_fields = {
	'grouped' : {'string':'Group the invoices', 'type':'boolean', 'default': lambda *a: False}
}

def _makeInvoices(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	res = False
	invoices = {}

	#TODO: merge with sale.py/make_invoice
	def make_invoice(order, lines):
		a = order.partner_id.property_account_receivable.id
		if order.partner_id and order.partner_id.property_payment_term.id:
			pay_term = order.partner_id.property_payment_term.id
		else:
			pay_term = False
		inv = {
			'name': order.name,
			'origin': order.name,
			'type': 'out_invoice',
			'reference': "P%dSO%d" % (order.partner_id.id, order.id),
			'account_id': a,
			'partner_id': order.partner_id.id,
			'address_invoice_id': order.partner_invoice_id.id,
			'address_contact_id': order.partner_invoice_id.id,
			'invoice_line': [(6,0,lines)],
			'currency_id' : order.pricelist_id.currency_id.id,
			'comment': order.note,
			'payment_term': pay_term,
		}
		inv_id = pool.get('account.invoice').create(cr, uid, inv)
		return inv_id

	for line in pool.get('sale.order.line').browse(cr,uid,data['ids']):
		if not line.invoiced:
			if not line.order_id.id in invoices:
				invoices[line.order_id.id] = []
			line_id = pool.get('sale.order.line').invoice_line_create(cr, uid,
					[line.id])
			for lid in line_id:
				invoices[line.order_id.id].append((line, lid))
			pool.get('sale.order.line').write(cr, uid, [line.id],
					{'invoiced': True})

	for result in invoices.values():
		order = result[0][0].order_id
		il = map(lambda x: x[1], result)
		res = make_invoice(order, il)
		cr.execute('INSERT INTO sale_order_invoice_rel \
				(order_id,invoice_id) values (%d,%d)', (order.id, res))
	return {}


class line_make_invoice(wizard.interface):
	states = {
		'init' : {
			'actions': [],
			'result': {
				'type': 'form',
				'arch': invoice_form,
				'fields': invoice_fields,
				'state': [
					('end', 'Cancel'),
					('invoice', 'Create invoices')
				]
			}
		},
		'invoice' : {
			'actions' : [_makeInvoices],
			'result' : {'type': 'state', 'state': 'end'}
		},
	}

line_make_invoice("sale.order.line.make_invoice")
