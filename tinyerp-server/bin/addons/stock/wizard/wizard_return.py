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
import pooler
from tools.misc import UpdateableStr

import netsvc
import time

arch=UpdateableStr()
fields={}

def make_default(val):
	def fct(obj, cr, uid):
		return val
	return fct

def _get_returns(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	pick_obj=pool.get('stock.picking')
	pick=pick_obj.browse(cr, uid, [data['id']])[0]
	res={}
	fields.clear()
	arch_lst=['<?xml version="1.0"?>', '<form string="Return lines">', '<label string="Indicate here the quantity of the return line." colspan="4"/>']
	for m in [line for line in pick.move_lines]:
		quantity=m.product_qty
		arch_lst.append('<field name="return%s"/>\n<newline/>' % (m.id,))
		fields['return%s' % m.id]={'string':m.product_id.name, 'type':'float', 'required':True, 'default':make_default(quantity)}
		res.setdefault('returns', []).append(m.id)
	arch_lst.append('<field name="invoice_state"/>\n<newline/>')
	if pick.invoice_state=='invoiced':
		new_invoice_state='2binvoiced'
	else:
		new_invoice_state=pick.invoice_state
	fields['invoice_state']={'string':'Invoice state', 'type':'selection', 'default':make_default(new_invoice_state), 'selection':[('2binvoiced', 'to be invoiced'), ('none', 'None')]}
	arch_lst.append('</form>')
	arch.string='\n'.join(arch_lst)
	return res

def _create_returns(self, cr, uid, data, context):
	pool = pooler.get_pool(cr.dbname)
	move_obj = pool.get('stock.move')
	pick_obj = pool.get('stock.picking')
	uom_obj = pool.get('product.uom')

	pick=pick_obj.browse(cr, uid, [data['id']])[0]
	new_picking=None
	date_cur=time.strftime('%Y-%m-%d %H:%M:%S')

	for move in move_obj.browse(cr, uid, data['form'].get('returns',[])):
		if not new_picking:
			if pick.type=='out':
				new_type='in'
			elif pick.type=='in':
				new_type='out'
			else:
				new_type='internal'
			new_picking=pick_obj.copy(cr, uid, pick.id, {'name':'%s (return)' % pick.name,
					'move_lines':[], 'state':'draft', 'type':new_type, 'loc_move_id':False,
					'date':date_cur, 'invoice_state':data['form']['invoice_state'],})
		if pick.loc_move_id:
			new_location=pick.loc_move_id.id
		else:
			new_location=move.location_dest_id.id

		new_move=move_obj.copy(cr, uid, move.id, {
			'product_qty': data['form']['return%s' % move.id],
			'product_uos_qty': uom_obj._compute_qty(cr, uid, move.product_uom.id,
				data['form']['return%s' % move.id], move.product_uos.id),
			'picking_id':new_picking, 'state':'draft',
			'location_id':new_location, 'location_dest_id':move.location_id.id,
			'date':date_cur, 'date_planned':date_cur,})
	if new_picking:
		wf_service = netsvc.LocalService("workflow")
		if new_picking:
			wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
		pick_obj.force_assign(cr, uid, [new_picking], context)
	return new_picking

def _action_open_window(self, cr, uid, data, context):
	res=_create_returns(self, cr, uid, data, context)
	if not res:
		return {}
	return {
		'domain': "[('id', 'in', ["+str(res)+"])]",
		'name': 'Packing List',
		'view_type':'form',
		'view_mode':'tree,form',
		'res_model':'stock.picking',
		'view_id':False,
		'type':'ir.actions.act_window',
	}

class wizard_return_picking(wizard.interface):
	states={
		'init':{
			'actions':[_get_returns],
			'result':{'type':'form', 'arch':arch, 'fields':fields, 'state':[('end','Cancel'),('return','Return')]}
		},
		'return':{
			'actions':[],
			'result':{'type':'action', 'action':_action_open_window, 'state':'end'}
		}
	}
wizard_return_picking('stock.return.picking')
