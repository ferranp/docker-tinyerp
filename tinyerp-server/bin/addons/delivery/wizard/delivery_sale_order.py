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

delivery_form = """<?xml version="1.0"?>
<form string="Create deliveries">
	<separator colspan="4" string="Delivery Method" />
	<field name="carrier_id" />
</form>
"""

delivery_fields = {
	'carrier_id' : {'string':'Delivery Method', 'type':'many2one', 'relation': 'delivery.carrier','required':True}
}

def _delivery_default(self, cr, uid, data, context):
	order_obj = pooler.get_pool(cr.dbname).get('sale.order')
	order = order_obj.browse(cr, uid, data['ids'])[0]
	if not order.state in ('draft'):
		raise wizard.except_wizard('Order not in draft state !', 'The order state have to be draft to add delivery lines.')

	carrier_id = order.partner_id.property_delivery_carrier.id
	return {'carrier_id': carrier_id}

def _delivery_set(self, cr, uid, data, context):
	order_obj = pooler.get_pool(cr.dbname).get('sale.order')
	line_obj = pooler.get_pool(cr.dbname).get('sale.order.line')
	order_objs = order_obj.browse(cr, uid, data['ids'], context)

	for order in order_objs:
		grid_id = pooler.get_pool(cr.dbname).get('delivery.carrier').grid_get(cr, uid, [data['form']['carrier_id']],order.partner_shipping_id.id)
		if not grid_id:
			raise wizard.except_wizard('No grid avaible !', 'No grid matching for this carrier !')
		grid = pooler.get_pool(cr.dbname).get('delivery.grid').browse(cr, uid, [grid_id])[0]

		line_obj.create(cr, uid, {
			'order_id': order.id,
			'name': grid.carrier_id.name,
			'product_uom_qty': 1,
			'product_uom': grid.carrier_id.product_id.uom_id.id,
			'product_id': grid.carrier_id.product_id.id,
			'price_unit': grid.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context), 
			'tax_id': [(6,0,[ x.id for x in grid.carrier_id.product_id.taxes_id])],
			'type': 'make_to_stock'
			})

	return {}

class make_delivery(wizard.interface):
	states = {
		'init' : {
			'actions' : [_delivery_default],
			'result' : {'type' : 'form', 'arch' : delivery_form, 'fields' : delivery_fields, 'state' : [('end', 'Cancel'),('delivery', 'Create delivery line') ]}
		},
		'delivery' : {
			'actions' : [_delivery_set],
			'result' : {'type' : 'state', 'state' : 'end'}
		},
	}
make_delivery("delivery.sale.order")
