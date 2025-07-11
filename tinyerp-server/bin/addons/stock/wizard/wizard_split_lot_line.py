##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import wizard
import netsvc
import pooler

import time
from osv import osv
from tools.misc import UpdateableStr

arch = UpdateableStr()
fields = {}

def make_default(val):
	def fct(obj, cr, uid):
		return val
	return fct

def _get_moves(self, cr, uid, data, context):
	pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
	pick = pick_obj.browse(cr, uid, [data['id']])[0]
	res = {}
	fields.clear()
	arch_lst = ['<?xml version="1.0"?>', '<form string="Split lines">', '<label string="Indicate here the quantity of the new line. A quantity of zero will not split the line." colspan="4"/>']
	for m in [line for line in pick.move_lines]:
		quantity = m.product_qty
		arch_lst.append('<field name="move%s" />\n<newline />' % (m.id,))
		fields['move%s' % m.id] = {'string' : m.product_id.name, 'type' : 'float', 'required' : True, 'default' : make_default(quantity)}
		res.setdefault('moves', []).append(m.id)
	arch_lst.append('</form>')
	arch.string = '\n'.join(arch_lst)
	return res

def _split_lines(self, cr, uid, data, context):
	move_obj = pooler.get_pool(cr.dbname).get('stock.move')
	for move in move_obj.browse(cr, uid, data['form']['moves']):
		quantity = data['form']['move%s' % move.id]
		if 0 < quantity < move.product_qty:
			new_qty = move.product_qty - quantity
			new_uos_qty = new_qty / move.product_qty * move.product_uos_qty
			new_obj = move_obj.copy(cr, uid, move.id, {'product_qty' : new_qty, 'product_uos_qty': new_uos_qty, 'state':move.state})
			uos_qty = quantity / move.product_qty * move.product_uos_qty
			move_obj.write(cr, uid, [move.id], {'product_qty' : quantity, 'product_uos_qty': uos_qty})
	return {}

class wizard_split_move(wizard.interface):
	states = {
		'init': {
			'actions': [_get_moves],
			'result': {'type':'form', 'arch':arch, 'fields':fields, 'state':[('end','Cancel'),('split','Split')]}
		},
		'split': {
			'actions': [_split_lines],
			'result': {'type':'state', 'state':'end'}
		}
	}
wizard_split_move('stock.move.split')

