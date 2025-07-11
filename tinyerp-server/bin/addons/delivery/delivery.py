##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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

import netsvc
from osv import fields,osv,orm

class delivery_carrier(osv.osv):
	_name = "delivery.carrier"
	_description = "Carrier and delivery grids"
	_columns = {
		'name': fields.char('Carrier', size=64, required=True),
		'partner_id': fields.many2one('res.partner', 'Carrier partner', required=True),
		'product_id': fields.many2one('product.product', 'Delivery product', required=True),
		'grids_id': fields.one2many('delivery.grid', 'carrier_id', 'Delivery grids'),
		'active': fields.boolean('Active')
	}
	_defaults = {
		'active': lambda *args:1
	}
	def grid_get(self, cr, uid, ids, contact_id, context={}):
		contact = self.pool.get('res.partner.address').browse(cr, uid, [contact_id])[0]
		for carrier in self.browse(cr, uid, ids):
			for grid in carrier.grids_id:
				get_id = lambda x: x.id
				country_ids = map(get_id, grid.country_ids)
				state_ids = map(get_id, grid.state_ids)
				if country_ids and not contact.country_id.id in country_ids:
					continue
				if state_ids and not contact.state_id.id in state_ids:
					continue
				if grid.zip_from and (contact.zip or '')< grid.zip_from:
					continue
				if grid.zip_to and (contact.zip or '')> grid.zip_to:
					continue
				return grid.id
		return False
delivery_carrier()

class delivery_grid(osv.osv):
	_name = "delivery.grid"
	_description = "Delivery grid"
	_columns = {
		'name': fields.char('Grid Name', size=64, required=True),
		'sequence': fields.integer('Sequence', size=64, required=True),
		'carrier_id': fields.many2one('delivery.carrier', 'Carrier', required=True, ondelete='cascade'),
		'country_ids': fields.many2many('res.country', 'delivery_grid_country_rel', 'grid_id', 'country_id', 'Countries'),
		'state_ids': fields.many2many('res.country.state', 'delivery_grid_state_rel', 'grid_id', 'state_id', 'States'),
		'zip_from': fields.char('Start Zip', size=12),
		'zip_to': fields.char('To Zip', size=12),
		'line_ids': fields.one2many('delivery.grid.line', 'grid_id', 'Grid Line'),
		'active': fields.boolean('Active'),
	}
	_defaults = {
		'active': lambda *a: 1,
		'sequence': lambda *a: 1,
	}
	_order = 'sequence'


	def get_price(self, cr, uid, id, order, dt, context):

		total = 0
		weight = 0
		volume = 0

		for line in order.order_line:
			if not line.product_id:
				continue
			total += line.price_subtotal or 0.0
			weight += (line.product_id.weight or 0.0) * line.product_uom_qty
			volume += (line.product_id.volume or 0.0) * line.product_uom_qty


		return self.get_price_from_picking(cr, uid, id, total,weight, volume, context)

			
	def get_price_from_picking(self, cr, uid, id, total, weight, volume, context={}):
		grid = self.browse(cr, uid, id, context)

		price = 0.0
		ok = False

		for line in grid.line_ids:
			price_dict = {'price': total, 'volume':volume, 'weight': weight, 'wv':volume*weight}
			test = eval(line.type+line.operator+str(line.max_value), price_dict)
			if test:
				if line.price_type=='variable':
					price = line.list_price * price_dict[line.variable_factor]
				else:
					price = line.list_price
				ok = True
				break
		if not ok:
			raise except_osv('No price avaible !', 'No line matched this order in the choosed delivery grids !')

		return price


delivery_grid()

class delivery_grid_line(osv.osv):
	_name = "delivery.grid.line"
	_description = "Delivery line of grid"
	_columns = {
		'name': fields.char('Name', size=32, required=True),
		'grid_id': fields.many2one('delivery.grid', 'Grid',required=True),
		'type': fields.selection([('weight','Weight'),('volume','Volume'),('wv','Weight * Volume'), ('price','Price')], 'Variable', required=True),
		'operator': fields.selection([('=','='),('<=','<='),('>=','>=')], 'Operator', required=True),
		'max_value': fields.float('Maximum Value', required=True),
		'price_type': fields.selection([('fixed','Fixed'),('variable','Variable')], 'Price Type', required=True),
		'variable_factor': fields.selection([('weight','Weight'),('volume','Volume'),('wv','Weight * Volume'), ('price','Price')], 'Variable Factor', required=True),
		'list_price': fields.float('List Price', required=True),
		'standard_price': fields.float('Standard Price', required=True),
	}
	_defaults = {
		'type': lambda *args: 'weight',
		'operator': lambda *args: '<=',
		'price_type': lambda *args: 'fixed',
		'variable_factor': lambda *args: 'weight',
	}
	_order = 'list_price'


delivery_grid_line()


