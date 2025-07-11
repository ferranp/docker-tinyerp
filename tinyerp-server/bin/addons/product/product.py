##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: product.py 1310 2005-09-08 20:40:15Z pinky $
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

from osv import osv, fields
import pooler

import math
from _common import rounding

from tools import config

def is_pair(x):
	return not x%2

#----------------------------------------------------------
# UOM
#----------------------------------------------------------

class product_uom_categ(osv.osv):
	_name = 'product.uom.categ'
	_description = 'Product uom categ'
	_columns = {
		'name': fields.char('Name', size=64, required=True),
	}
product_uom_categ()

class product_uom(osv.osv):
	_name = 'product.uom'
	_description = 'Product Unit of Measure'
	_columns = {
		'name': fields.char('Name', size=64, required=True),
		'category_id': fields.many2one('product.uom.categ', 'UOM Category', required=True, ondelete='cascade'),
		'factor': fields.float('Factor', digits=(12, 6), required=True),
		'rounding': fields.float('Rounding Precision', digits=(16, 3), required=True),
		'active': fields.boolean('Active'),
	}
	
	_defaults = {
		'factor': lambda *a: 1.0,
		'active': lambda *a: 1,
		'rounding': lambda *a: 0.01,
	}
	
	def _compute_qty(self, cr, uid, from_uom_id, qty, to_uom_id=False):
		if not from_uom_id or not qty or not to_uom_id:
			return qty
		uoms = self.browse(cr, uid, [from_uom_id, to_uom_id])
		if uoms[0].id == from_uom_id:
			from_unit, to_unit = uoms[0], uoms[-1]
		else:
			from_unit, to_unit = uoms[-1], uoms[0]
		if from_unit.category_id.id <> to_unit.category_id.id:
			return qty
		amount = qty / from_unit['factor']
		if to_uom_id:
			amount = rounding(amount * to_unit['factor'], to_unit['rounding'])
		return amount

	def _compute_price(self, cr, uid, from_uom_id, price, to_uom_id=False):
		if not from_uom_id or not price or not to_uom_id:
			return price
		uoms = self.browse(cr, uid, [from_uom_id, to_uom_id])
		if uoms[0].id == from_uom_id:
			from_unit, to_unit = uoms[0], uoms[-1]
		else:
			from_unit, to_unit = uoms[-1], uoms[0]
		if from_unit.category_id.id <> to_unit.category_id.id:
			return price
		amount = price * from_unit.factor
		if to_uom_id:
			amount = amount / to_unit.factor
		return amount

product_uom()


class product_ul(osv.osv):
	_name = "product.ul"
	_description = "Shipping Unit"
	_columns = {
		'name' : fields.char('Name', size=64),
		'type' : fields.selection([('unit','Unit'),('pack','Pack'),('box', 'Box'), ('palet', 'Palet')], 'Type', required=True),
	}
product_ul()


#----------------------------------------------------------
# Categories
#----------------------------------------------------------
class product_category(osv.osv):

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['name','parent_id'], context)
		res = []
		for record in reads:
			name = record['name']
			if record['parent_id']:
				name = record['parent_id'][1]+' / '+name
			res.append((record['id'], name))
		return res

	def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context):
		res = self.name_get(cr, uid, ids)
		return dict(res)

	_name = "product.category"
	_description = "Product Category"
	_columns = {
		'name': fields.char('Name', size=64, required=True),
		'complete_name': fields.function(_name_get_fnc, method=True, type="char", string='Name'),
		'parent_id': fields.many2one('product.category','Parent Category', select=True),
		'child_id': fields.one2many('product.category', 'parent_id', string='Childs Categories'),
		'sequence': fields.integer('Sequence'),
	}
	_order = "sequence"
	def _check_recursion(self, cr, uid, ids):
		level = 100
		while len(ids):
			cr.execute('select distinct parent_id from product_category where id in ('+','.join(map(str,ids))+')')
			ids = filter(None, map(lambda x:x[0], cr.fetchall()))
			if not level:
				return False
			level -= 1
		return True

	_constraints = [
		(_check_recursion, 'Error ! You can not create recursive categories.', ['parent_id'])
	]
	def child_get(self, cr, uid, ids):
		return [ids]

product_category()


#----------------------------------------------------------
# Products
#----------------------------------------------------------
class product_template(osv.osv):
	_name = "product.template"
	_description = "Product Template"

	def _calc_seller_delay(self, cr, uid, ids, name, arg, context={}):
		result = {}
		for product in self.browse(cr, uid, ids, context):
			if product.seller_ids:
				result[product.id] = product.seller_ids[0].delay
			else:
				result[product.id] = 1
		return result

	_columns = {
		'name': fields.char('Name', size=64, required=True, translate=True, select=True),
		'product_manager': fields.many2one('res.users','Product Manager'),
		'description': fields.text('Description'),
		'description_purchase': fields.text('Purchase Description'),
		'description_sale': fields.text('Sale Description'),
		'type': fields.selection([('product','Stockable Product'),('consu', 'Consumable'),('service','Service')], 'Product Type', required=True),
		'supply_method': fields.selection([('produce','Produce'),('buy','Buy')], 'Supply method', required=True),
		'sale_delay': fields.float('Customer lead time', help="This is the average time between the confirmation of the customer order and the delivery of the finnished products. It's the time you promise to your customers."),
		'produce_delay': fields.float('Manufacturing lead time', help="Average time to produce this product. This is only for the production order and, if it is a multi-level bill of material, it's only for the level of this product. Different delays will be summed for all levels and purchase orders."),
		'procure_method': fields.selection([('make_to_stock','Make to Stock'),('make_to_order','Make to Order')], 'Procure Method', required=True),
		'rental': fields.boolean('Rentable product'),
		'categ_id': fields.many2one('product.category','Category', required=True, change_default=True),
		'list_price': fields.float('List Price', digits=(16, int(config['price_accuracy']))),
		'standard_price': fields.float('Cost Price', required=True, digits=(16, int(config['price_accuracy']))),
		'volume': fields.float('Volume'),
		'weight': fields.float('Gross weight'),
		'weight_net': fields.float('Net weight'),
		'cost_method': fields.selection([('standard','Standard Price'), ('average','Average Price')], 'Costing Method', required=True),
		'warranty': fields.float('Warranty (months)'),
		'sale_ok': fields.boolean('Can be sold', help="Determine if the product can be visible in the list of product within a selection from a sale order line."),
		'purchase_ok': fields.boolean('Can be Purchased', help="Determine if the product is visible in the list of products within a selection from a purchase order line."),
		'uom_id': fields.many2one('product.uom', 'Default UOM', required=True),
		'uom_po_id': fields.many2one('product.uom', 'Purchase UOM', required=True),
		'state': fields.selection([('draft', 'In Development'),('sellable','In Production'),('end','End of Lifecycle'),('obsolete','Obsolete')], 'State'),
		'uos_id' : fields.many2one('product.uom', 'Unit of Sale',
			help='Keep empty to use the default UOM'),
		'uos_coeff': fields.float('UOM -> UOS Coeff', digits=(16,4),
			help='Coefficient to convert UOM to UOS\n'
			' uom = uos * coeff'),
		'mes_type': fields.selection((('fixed', 'Fixed'), ('variable', 'Variable')), 'Measure type', required=True),
		'tracking': fields.boolean('Track lots'),
		'seller_delay': fields.function(_calc_seller_delay, method=True, type='integer', string='Supplier lead time', help="This is the average delay in days between the purchase order confirmation and the reception of goods for this product and for the default supplier. It is used by the scheduler to order requests based on reordering delays."),
		'seller_ids': fields.one2many('product.supplierinfo', 'product_id', 'Partners'),
	}

	def _get_uom_id(self, cr, uid, *args):
		cr.execute('select id from product_uom order by id limit 1')
		res = cr.fetchone()
		return res and res[0] or False

	_defaults = {
		'type': lambda *a: 'product',
		'list_price': lambda *a: 1,
		'cost_method': lambda *a: 'standard',
		'supply_method': lambda *a: 'buy',
		'standard_price': lambda *a: 1,
		'sale_ok': lambda *a: 1,
		'sale_delay': lambda *a: 7,
		'produce_delay': lambda *a: 1,
		'purchase_ok': lambda *a: 1,
		'procure_method': lambda *a: 'make_to_stock',
		'uom_id': _get_uom_id,
		'uom_po_id': _get_uom_id,
		#'uom_price_id' : _get_uom_id,
		#'uos_id' : _get_uom_id,
		'uos_coeff' : lambda *a: 1.0,
		'mes_type' : lambda *a: 'fixed',
	}

	def _check_uos(self, cursor, user, ids):
		for product in self.browse(cursor, user, ids):
			if product.uos_id \
					and product.uos_id.category_id.id \
					== product.uom_id.category_id.id:
				return False
		return True

	_constraints = [(_check_uos,
		'Error: UOS must be in a different category than the UOM', ['uos_id'])]

	def name_get(self, cr, user, ids, context={}):
		if 'partner_id' in context:
			pass
		return super(product_template, self).name_get(cr, user, ids, context)

product_template()

class product_product(osv.osv):
	def _product_price(self, cr, uid, ids, name, arg, context={}):
		res = {}
		quantity = context.get('quantity', 1)
		pricelist = context.get('pricelist', False)
		if pricelist:
			for id in ids:
				price = self.pool.get('product.pricelist').price_get(cr,uid,[pricelist], id, quantity, context=context)[pricelist]
				res[id] = price
		for id in ids:
			res.setdefault(id, 0.0)
		return res

	def _get_product_available_func(states, what):
		def _product_available(self, cr, uid, ids, name, arg, context={}):
			res={}
			for id in ids:
				res.setdefault(id, 0.0)
			return res
		return _product_available

	_product_qty_available = _get_product_available_func(('done',), ('in', 'out'))
	_product_virtual_available = _get_product_available_func(('confirmed','waiting','assigned','done'), ('in', 'out'))
	_product_outgoing_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('out',))
	_product_incoming_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('in',))
	
	def _product_lst_price(self, cr, uid, ids, name, arg, context=None):
		res = {}
		product_uom_obj = self.pool.get('product.uom')
		for id in ids:
			res.setdefault(id, 0.0)
		for product in self.browse(cr, uid, ids, context=context):
			if 'uom' in context:
				uom = product.uos_id or product.uom_id
				res[product.id] = product_uom_obj._compute_price(cr, uid,
						uom.id, product.list_price, context['uom'])
			else:
				res[product.id] = product.list_price
		return res

	def _get_partner_code_name(self, cr, uid, ids, product_id, partner_id, context={}):
		product = self.browse(cr, uid, [product_id], context)[0]
		for supinfo in product.seller_ids:
			if supinfo.name.id == partner_id:
				return {'code': supinfo.product_code, 'name': supinfo.product_name}
		return {'code' : product.default_code, 'name' : product.name}

	def _product_code(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for p in self.browse(cr, uid, ids, context):
			res[p.id] = self._get_partner_code_name(cr, uid, [], p.id, context.get('partner_id', None), context)['code']
		return res

	def _product_partner_ref(self, cr, uid, ids, name, arg, context={}):
		res = {}
		for p in self.browse(cr, uid, ids, context):
			data = self._get_partner_code_name(cr, uid, [], p.id, context.get('partner_id', None), context)
			res[p.id] = (data['code'] and ('['+data['code']+'] ') or '') +data['name']
		return res

	_defaults = {
		'active': lambda *a: 1,
		'price_extra': lambda *a: 0.0,
		'price_margin': lambda *a: 1.0,
	}

	_name = "product.product"
	_description = "Product"
	_table = "product_product"
	_inherits = {'product.template': 'product_tmpl_id'}
	_columns = {
		'qty_available': fields.function(_product_qty_available, method=True, type='float', string='Real Stock'),
		'virtual_available': fields.function(_product_virtual_available, method=True, type='float', string='Virtual Stock'),
		'incoming_qty': fields.function(_product_incoming_qty, method=True, type='float', string='Incoming'),
		'outgoing_qty': fields.function(_product_outgoing_qty, method=True, type='float', string='Outgoing'),
		'price': fields.function(_product_price, method=True, type='float', string='Customer Price', digits=(16, int(config['price_accuracy']))),
		'lst_price' : fields.function(_product_lst_price, method=True, type='float', string='List Price', digits=(16, int(config['price_accuracy']))),
		'code': fields.function(_product_code, method=True, type='char', string='Code'),
		'partner_ref' : fields.function(_product_partner_ref, method=True, type='char', string='Customer ref'),
		'default_code' : fields.char('Code', size=64),
		'active': fields.boolean('Active'),
		'variants': fields.char('Variants', size=64),
		'product_tmpl_id': fields.many2one('product.template', 'Product Template', required=True),
		'ean13': fields.char('EAN13', size=13),
		'packaging' : fields.one2many('product.packaging', 'product_id', 'Palettization', help="Gives the different ways to package the same product. This has no impact on the packing order and is mainly used if you use the EDI module."),
		'price_extra': fields.float('Price Extra', digits=(16, int(config['price_accuracy']))),
		'price_margin': fields.float('Price Margin', digits=(16, int(config['price_accuracy']))),
	}

	def _check_ean_key(self, cr, uid, ids):
		for partner in self.browse(cr, uid, ids):
			if not partner.ean13:
				continue
			if len(partner.ean13) < 12:
				return False
			try:
				int(partner.ean13)
			except:
				return False
			sum=0
			for i in range(12):
				if is_pair(i):
					sum += int(partner.ean13[i])
				else:
					sum += 3 * int(partner.ean13[i])
			check = int(math.ceil(sum / 10.0) * 10 - sum)
			if len(partner.ean13) == 12:
				self.write(cr, uid, partner.id, {
					'ean13': partner.ean13 + str(check)
					})
			elif check != int(partner.ean13[12]):
				return False
		return True

	_constraints = [(_check_ean_key, 'Error: Invalid ean code', ['ean13'])]

	def on_order(self, cr, uid, ids, orderline, quantity):
		pass

	def name_get(self, cr, user, ids, context={}):
		if not len(ids):
			return []
		def _name_get(d):
			#name = self._product_partner_ref(cr, user, [d['id']], '', '', context)[d['id']]
			#code = self._product_code(cr, user, [d['id']], '', '', context)[d['id']]
			name = d.get('name','')
			code = d.get('default_code',False)
			if code:
				name = '[%s] %s' % (code,name)
			if d['variants']:
				name = name + ' - %s' % (d['variants'],)
			return (d['id'], name)
		result = map(_name_get, self.read(cr, user, ids, ['variants','name','default_code'], context))
		return result

	def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=80):
		if not args:
			args=[]
		if not context:
			context={}
		ids = self.search(cr, user, [('default_code','=',name)]+ args, limit=limit, context=context)
		if not len(ids):
			ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
		if not len(ids):
			ids = self.search(cr, user, [('default_code',operator,name)]+ args, limit=limit, context=context)
			ids += self.search(cr, user, [('name',operator,name)]+ args, limit=limit, context=context)
		result = self.name_get(cr, user, ids, context)
		return result

	#
	# Could be overrided for variants matrices prices
	#
	def price_get(self, cr, uid, ids, ptype='list_price', context={}):
		res = {}
		product_uom_obj = self.pool.get('product.uom')

		for product in self.browse(cr, uid, ids, context=context):
			res[product.id] = product[ptype] or 0.0
			if ptype == 'list_price':
				res[product.id] = (res[product.id] * product.price_margin) + \
						product.price_extra
			if 'uom' in context:
				uom = product.uos_id or product.uom_id
				res[product.id] = product_uom_obj._compute_price(cr, uid,
						uom.id, res[product.id], context['uom'])
		return res
#		result = self.read(cr, uid, ids, [ptype, 'price_extra','price_margin'])
#		result2 = {}
#		for res in result:
#			result2[res['id']] = res[ptype] or 0.0
#			if ptype=='list_price':
#				result2[res['id']] = result2[res['id']] * res['price_margin'] + res['price_extra']
#			if 'uom' in context:
#				result2[res['id']] = self.pool.get('product.uom')._compute_price(cr, uid, context['uom'], result2[res['id']])
#		return result2

	def copy(self, cr, uid, id, default=None, context=None):
		if not context:
			context={}

		if ('variant' in context) and context['variant']:
			fields = ['product_tmpl_id', 'active', 'variants', 'default_code', 
					'price_margin', 'price_extra']
			data = self.read(cr, uid, id, fields=fields, context=context)
			for f in fields:
				if f in default:
					data[f] = default[f]
			data['product_tmpl_id'] = data.get('product_tmpl_id', False) \
					and data['product_tmpl_id'][0]
			del data['id']
			return self.create(cr, uid, data)
		else:
			return super(product_product, self).copy(cr, uid, id, default=default,
					context=context)
product_product()

class product_packaging(osv.osv):
	_name = "product.packaging"
	_description = "Conditionnement"
	_rec_name = 'ean'
	_columns = {
		'name' : fields.char('Description', size=64),
		'qty' : fields.float('Quantity by UL',
			help="The total number of products you can put by UL."),
		'ul' : fields.many2one('product.ul', 'Type of UL', required=True),
		'ul_qty' : fields.integer('UL by layer'),
		'rows' : fields.integer('Number of layer', required=True,
			help='The number of layer on palette'),
		'product_id' : fields.many2one('product.product', 'Product',
			select=1, required=True),
		'ean' : fields.char('EAN', size=14,
			help="The EAN code of the transport unit."),
		'code' : fields.char('Code', size=14,
			help="The code of the transport unit."),
		'weight': fields.float('Palette Weight',
			help='The weight of the empty palette'),
		'weight_ul': fields.float('UL Weight',
			help='The weight of the empty UL'),
		'height': fields.float('Height', help='The height of the palette'),
		'width': fields.float('Width', help='The width of the palette'),
		'length': fields.float('Length', help='The length of the palette'),
	}

	def _get_1st_ul(self, cr, uid, context={}):
		cr.execute('select id from product_ul order by id asc limit 1')
		res = cr.fetchone()
		return (res and res[0]) or False

	_defaults = {
		'rows' : lambda *a : 3,
		'ul' : _get_1st_ul,
	}

	def checksum(ean):
		salt = '31' * 6 + '3'
		sum = 0
		for ean_part, salt_part in zip(ean, salt):
			sum += int(ean_part) * int(salt_part)
		return (10 - (sum % 10)) % 10
	checksum = staticmethod(checksum)

product_packaging()


class product_supplierinfo(osv.osv):
	_name = "product.supplierinfo"
	_description = "Information about a product supplier"
	_columns = {
		'name' : fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
		'product_name': fields.char('Partner product name', size=128),
		'product_code': fields.char('Partner product reference', size=64),
		'sequence' : fields.integer('Sequence'),
		'qty' : fields.integer('Minimal quantity', required=True),
		'product_id' : fields.many2one('product.template', 'Product', required=True, ondelete='cascade', select=True),
		'delay' : fields.integer('Delivery delay', required=True),
		'pricelist_ids': fields.one2many('pricelist.partnerinfo', 'suppinfo_id', 'Pricelist'),
	}
	_defaults = {
		'qty': lambda *a: 0.0,
		'delay': lambda *a: 1,
	}
	_order = 'sequence'
product_supplierinfo()


class pricelist_partnerinfo(osv.osv):
	_name = 'pricelist.partnerinfo'
	_columns = {
		'name': fields.char('Description', size=64),
		'suppinfo_id': fields.many2one('product.supplierinfo', 'Partner Information', required=True, ondelete='cascade'),
		'min_quantity': fields.float('Minimal quantity', required=True),
		'price': fields.float('price', required=True, digits=(16, int(config['price_accuracy']))),
	}
	_order = 'min_quantity asc'
pricelist_partnerinfo()


# vim:noexpandtab:
