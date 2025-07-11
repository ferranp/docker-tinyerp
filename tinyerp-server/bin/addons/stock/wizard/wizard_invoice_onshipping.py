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
import ir
import pooler
from osv.osv import except_osv
import netsvc

invoice_form = """<?xml version="1.0"?>
<form string="Create invoices">
	<separator colspan="4" string="Create invoices" />
	<field name="journal_id"/>
	<newline/>
	<field name="group"/>
	<newline/>
	<field name="type"/>
</form>
"""

invoice_fields = {
	'journal_id': {
		'string': 'Destination Journal',
		'type': 'many2one',
		'relation': 'account.journal',
		'required': True
	},
	'group': {
		'string': 'Group by partner',
		'type':'boolean'
	},
	'type': {
		'string': 'Type',
		'type': 'selection',
		'selection': [
			('out_invoice', 'Customer Invoice'),
			('in_invoice', 'Supplier Invoice'),
			('out_refund', 'Customer Refund'),
			('in_refund', 'Supplier Refund'),
			],
		'required': True
	},
}

def _get_type(obj, cr, uid, data, context):
	picking_obj=pooler.get_pool(cr.dbname).get('stock.picking')

	pick=picking_obj.browse(cr, uid, data['id'])
	if pick.loc_move_id:
		usage=pick.loc_move_id.usage
	else:
		usage=pick.move_lines[0].location_id.usage

	if pick.type == 'out' and usage == 'supplier':
		type = 'in_refund'
	elif pick.type == 'out' and usage == 'customer':
		type = 'out_invoice'
	elif pick.type == 'in' and usage == 'supplier':
		type = 'in_invoice'
	elif pick.type == 'in' and usage == 'customer':
		type = 'out_refund'
	else:
		type = 'out_invoice'
	return {'type': type}

def _create_invoice(obj, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	picking_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	mod_obj = pool.get('ir.model.data')
	act_obj = pool.get('ir.actions.act_window')

	type = data['form']['type']

	res = picking_obj.action_invoice_create(cr, uid, data['ids'],
			journal_id=data['form']['journal_id'],group=data['form']['group'],
			type=type, context= context)

	invoice_ids = res.values()

	if not invoice_ids:
		return {}

	if type == 'out_invoice':
		xml_id = 'action_invoice_tree5'
	elif type == 'in_invoice':
		xml_id = 'action_invoice_tree8'
	elif type == 'out_refund':
		xml_id = 'action_invoice_tree10'
	else:
		xml_id = 'action_invoice_tree12'

	result = mod_obj._get_id(cr, uid, 'account', xml_id)
	id = mod_obj.read(cr, uid, result, ['res_id'])['res_id']
	result = act_obj.read(cr, uid, id)
	result['res_id'] = invoice_ids
	return result


class make_invoice_onshipping(wizard.interface):
	states = {
		'init': {
			'actions': [_get_type],
			'result': {
				'type': 'form',
				'arch': invoice_form,
				'fields': invoice_fields,
				'state': [
					('end', 'Cancel'),
					('create_invoice', 'Create invoice')
				]
			}
		},
		'create_invoice': {
			'actions': [],
			'result': {
				'type': 'action',
				'action': _create_invoice,
				'state': 'end'
			}
		},
	}

make_invoice_onshipping("stock.invoice_onshipping")

