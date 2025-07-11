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
import pooler

invoice_form = """<?xml version="1.0"?>
<form string="Create invoices">
	<separator colspan="4" string="Do you really want to create the invoices ?" />
	<field name="grouped" />
</form>
"""

invoice_fields = {
	'grouped' : {'string':'Group the invoices', 'type':'boolean', 'default': lambda x,y,z: False}
}

ack_form = """<?xml version="1.0"?>
<form string="Create invoices">
	<separator string="Invoices created" />
</form>"""

ack_fields = {}

def _makeInvoices(self, cr, uid, data, context):
	order_obj = pooler.get_pool(cr.dbname).get('sale.order')
	newinv = []

	order_obj.action_invoice_create(cr, uid, data['ids'], data['form']['grouped'])
	for id in data['ids']:
		wf_service = netsvc.LocalService("workflow")
		wf_service.trg_validate(uid, 'sale.order', id, 'manual_invoice', cr)

	for o in order_obj.browse(cr, uid, data['ids'], context):
		for i in o.invoice_ids:
			newinv.append(i.id)
	return {
		'domain': "[('id','in', ["+','.join(map(str,newinv))+"])]",
		'name': 'Invoices',
		'view_type': 'form',
		'view_mode': 'tree,form',
		'res_model': 'account.invoice',
		'view_id': False,
		'context': "{'type':'out_refund'}",
		'type': 'ir.actions.act_window'
	}
	return {}

class make_invoice(wizard.interface):
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form',
				    'arch' : invoice_form,
				    'fields' : invoice_fields,
				    'state' : [('end', 'Cancel'),('invoice', 'Create invoices') ]}
		},
		'invoice' : {
			'actions' : [_makeInvoices],
			'result' : {'type' : 'action',
				    'action' : _makeInvoices,
				    'state' : 'end'}
		},
	}
make_invoice("sale.order.make_invoice")
