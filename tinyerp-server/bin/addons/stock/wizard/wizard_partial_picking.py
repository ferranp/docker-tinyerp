##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
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
import netsvc
from tools.misc import UpdateableStr, UpdateableDict
import pooler

import wizard
from osv import osv

_moves_arch = UpdateableStr()
_moves_fields = UpdateableDict()

_moves_arch_end = '''<?xml version="1.0"?>
<form string="Packing result">
	<label string="The packing has been successfully made !" colspan="4"/>
</form>'''
_moves_fields_end = {}

def make_default(val):
	def fct(uid, data, state):
		return val
	return fct

def _to_xml(s):
	return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def _get_moves(self, cr, uid, data, context):
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	res = {}

	_moves_fields.clear()
	_moves_arch_lst = ['<?xml version="1.0"?>', '<form string="Make packing">']

	for m in pick.move_lines:
		quantity = m.product_qty
		if m.state<>'assigned':
			quantity = 0

		_moves_arch_lst.append('<field name="move%s" />' % (m.id,))
		_moves_fields['move%s' % m.id] = {
				'string': '%s - %s' % (_to_xml(m.product_id.code or '/'), _to_xml(m.product_id.name)),
				'type' : 'float', 'required' : True, 'default' : make_default(quantity)}

		if (pick.type == 'in') and (m.product_id.cost_method == 'average'):
			price=0
			if hasattr(m, 'purchase_line_id') and m.purchase_line_id:
				price=m.purchase_line_id.price_unit

			currency=0
			if hasattr(pick, 'purchase_id') and pick.purchase_id:
				currency=pick.purchase_id.pricelist_id.currency_id.id

			_moves_arch_lst.append('<group col="6"><field name="uom%s"/>\
					<field name="price%s"/>' % (m.id,m.id,))

			_moves_fields['price%s' % m.id] = {'string': 'Unit Price',
					'type': 'float', 'required': True, 'default': make_default(price)}

			_moves_fields['uom%s' % m.id] = {'string': 'UOM', 'type': 'many2one',
					'relation': 'product.uom', 'required': True,
					'default': make_default(m.product_uom.id)}

			_moves_arch_lst.append('<field name="currency%d"/></group>' % (m.id,))
			_moves_fields['currency%s' % m.id] = {'string': 'Currency',
					'type': 'many2one', 'relation': 'res.currency',
					'required': True, 'default': make_default(currency)}

		_moves_arch_lst.append('<newline/>')
		res.setdefault('moves', []).append(m.id)

	_moves_arch_lst.append('</form>')
	_moves_arch.string = '\n'.join(_moves_arch_lst)
	return res

def _do_split(self, cr, uid, data, context):
	move_obj = pooler.get_pool(cr.dbname).get('stock.move')
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	new_picking = None
	new_moves = []

	complete, too_many, too_few = [], [], []
	for move in move_obj.browse(cr, uid, data['form'].get('moves',[])):
		if move.product_qty == data['form']['move%s' % move.id]:
			complete.append(move)
		elif move.product_qty > data['form']['move%s' % move.id]:
			too_few.append(move)
		else:
			too_many.append(move)

		# Average price computation
		if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
			product_obj = pooler.get_pool(cr.dbname).get('product.product')
			currency_obj = pooler.get_pool(cr.dbname).get('res.currency')
			users_obj = pooler.get_pool(cr.dbname).get('res.users')
			uom_obj = pooler.get_pool(cr.dbname).get('product.uom')

			product = product_obj.browse(cr, uid, [move.product_id.id])[0]
			user = users_obj.browse(cr, uid, [uid])[0]

			qty = data['form']['move%s' % move.id]
			uom = data['form']['uom%s' % move.id]
			price = data['form']['price%s' % move.id]
			currency = data['form']['currency%s' % move.id]

			qty = uom_obj._compute_qty(cr, uid, uom, qty, product.uom_id.id)

			if qty > 0:
				new_price = currency_obj.compute(cr, uid, currency,
						user.company_id.currency_id.id, price)
				new_std_price = ((product.standard_price * product.qty_available)\
						+ (new_price * qty))/(product.qty_available + qty)

				product_obj.write(cr, uid, [product.id],
						{'standard_price': new_std_price})
				move_obj.write(cr, uid, [move.id], {'price_unit': new_price})

	for move in too_few:
		if not new_picking:
			new_picking = pick_obj.copy(cr, uid, pick.id,
					{
						'name' : '%s (splitted)' % pick.name,
						'move_lines' : [],
						'state':'draft'
					})
		new_obj = move_obj.copy(cr, uid, move.id,
				{
					'product_qty' : data['form']['move%s' % move.id],
					'product_uos_qty':data['form']['move%s' % move.id],
					'picking_id' : new_picking,
					'state': 'assigned',
					'move_dest_id': False,
					'price_unit': False,
				})
		move_obj.write(cr, uid, [move.id],
				{
					'product_qty' : move.product_qty - data['form']['move%s' % move.id],
					'product_uos_qty':move.product_qty - data['form']['move%s' % move.id],
				})

	if new_picking:
		move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
		for move in too_many:
			move_obj.write(cr, uid, [move.id],
					{
						'product_qty' : data['form']['move%s' % move.id],
						'product_uos_qty': data['form']['move%s' % move.id],
						'picking_id': new_picking,
					})
	else:
		for move in too_many:
			move_obj.write(cr, uid, [move.id],
					{
						'product_qty': data['form']['move%s' % move.id],
						'product_uos_qty': data['form']['move%s' % move.id]
					})

	# At first we confirm the new picking (if necessary)
	wf_service = netsvc.LocalService("workflow")
	if new_picking:
		wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
	# Then we finish the good picking
	if new_picking:
		pick_obj.action_move(cr, uid, [new_picking])
		wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
		wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
	else:
		pick_obj.action_move(cr, uid, [pick.id])
		wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
	return {}


class partial_picking(wizard.interface):

	states = {
		'init': {
			'actions': [ _get_moves ],
			'result': {'type': 'form', 'arch': _moves_arch, 'fields': _moves_fields,
				'state' : (
					('end', 'Cancel'),
					('split', 'Make Picking')
				)
			},
		},
		'split': {
			'actions': [ _do_split ],
			'result': {'type': 'state', 'state': 'end'},
		},
		'end2': {
			'actions': [ ],
			'result': {'type': 'form', 'arch': _moves_arch_end,
				'fields': _moves_fields_end,
				'state': (
					('end', 'Close'),
				)
			},
		},
	}

partial_picking('stock.partial_picking')

# vim:noexpandtab:
