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

import pooler
import time
from mx import DateTime
import netsvc
from osv import osv

def _procure_confirm(self, cr, uid, schedule_cycle=1.0, po_cycle=1.0,\
		po_lead=1.0, security_lead=50.0, picking_lead=1.0, user_id=False,\
		use_new_cursor=False, context=None):
	'''
	use_new_cursor: False or the dbname
	'''
	if not context:
		context={}

	if use_new_cursor:
		cr = pooler.get_db(use_new_cursor).cursor()
	wf_service = netsvc.LocalService("workflow")

	cr.execute('select id from mrp_procurement where state=%s order by date_planned', ('exception',))
	ids = map(lambda x:x[0], cr.fetchall())
	for id in ids:
		wf_service.trg_validate(uid, 'mrp.procurement', id, 'button_restart', cr)
	if use_new_cursor:
		cr.commit()

	po_time = po_cycle + po_lead
	maxdate = DateTime.now() + DateTime.RelativeDateTime(days=schedule_cycle + security_lead)
	start_date = time.strftime('%Y-%m-%d, %Hh %Mm %Ss')
	offset = 0
	report = []
	report_total = 0
	report_except = 0
	report_later = 0
	ids = [1]
	while len(ids):
		cr.execute('select id from mrp_procurement where state=%s and procure_method=%s order by date_planned limit 500 offset %d', ('confirmed','make_to_order',offset))
		ids = map(lambda x:x[0], cr.fetchall())
		for proc in pooler.get_pool(cr.dbname).get('mrp.procurement').browse(cr, uid, ids):
			if proc.product_id.supply_method=='produce':
				wf_service.trg_validate(uid, 'mrp.procurement', proc.id, 'button_check', cr)
			else:
				if (maxdate + DateTime.RelativeDateTime(days=(proc.product_id.seller_delay or 0 + po_time))).strftime('%Y-%m-%d')>=proc.date_planned:
					wf_service.trg_validate(uid, 'mrp.procurement', proc.id, 'button_check', cr)
				else:
					offset+=1
					report_later += 1
			cr.execute('select name,state from mrp_procurement where id=%d', (proc.id,))
			name,state = cr.fetchone()
			if state=='exception':
				report.append('PROC %d: on order - %3.2f %-5s - %s' % (proc.id,proc.product_qty,proc.product_uom.name, proc.product_id.name))
				report_except += 1
			report_total +=1
			if use_new_cursor:
				cr.commit()

	offset = 0
	ids = [1]
	while len(ids):
		ids = pooler.get_pool(cr.dbname).get('mrp.procurement').search(cr, uid, [('state','=','confirmed'),('procure_method','=','make_to_stock')], offset=offset)
		for proc in pooler.get_pool(cr.dbname).get('mrp.procurement').browse(cr, uid, ids):
			if (maxdate + DateTime.RelativeDateTime(days=picking_lead)).strftime('%Y-%m-%d') >= proc.date_planned:
				wf_service.trg_validate(uid, 'mrp.procurement', proc.id, 'button_check', cr)
				cr.execute('select name,state from mrp_procurement where id=%d', (proc.id,))
				name,state = cr.fetchone()
				if state=='exception':
					report.append('PROC %d: from stock - %3.2f %-5s - %s' % (proc.id,proc.product_qty,proc.product_uom.name, proc.product_id.name,))
					report_except +=1
			else:
				report_later +=1
			report_total +=1
			if use_new_cursor:
				cr.commit()
		offset += len(ids)
	end_date = time.strftime('%Y-%m-%d, %Hh %Mm %Ss')
	if user_id:
		request = pooler.get_pool(cr.dbname).get('res.request')
		summary = '''Here is the procurement scheduling report.

Computation Started; %s
Computation Finnished; %s

Total procurement: %d
Exception procurement: %d
Not run now procurement: %d

Exceptions;
'''% (start_date,end_date,report_total, report_except,report_later)
		summary += '\n'.join(report)
		request.create(cr, uid,
			{'name' : "Procurement calculation report.",
				'act_from' : user_id,
				'act_to' : user_id,
				'body': summary,
			})
	if use_new_cursor:
		cr.commit()
		cr.close()
	return {}

def create_automatic_op(cr, uid, context=None):
	if not context:
		context={}
	product_obj = pooler.get_pool(cr.dbname).get('product.product')
	proc_obj = pooler.get_pool(cr.dbname).get('mrp.procurement')
	warehouse_obj = pooler.get_pool(cr.dbname).get('stock.warehouse')
	wf_service = netsvc.LocalService("workflow")

	cr.execute('select id from stock_warehouse')
	warehouses = [x for x, in cr.fetchall()]
	cr.execute('select id from product_product')
	products_id = [x for x, in cr.fetchall()]
	products = dict(zip(products_id, product_obj.browse(cr, uid, products_id, context)))
	for warehouse in warehouses:
		v_stock = product_obj._product_virtual_available(cr, uid, products_id, None, {'warehouse': warehouse})
		cr.execute("select lot_stock_id from stock_warehouse")
		location_ids_str = ','.join([str(id) for id, in cr.fetchall()])
		stock_locations = warehouse_obj.read(cr, uid, [warehouse], ['lot_input_id', 'lot_stock_id'])[0]
		for prod_id, available in v_stock.items():
			if available >= 0:
				continue
			newdate = DateTime.now() + DateTime.RelativeDateTime(days=products[prod_id].seller_delay)
			if products[prod_id].supply_method == 'buy':
				location_id = stock_locations['lot_input_id'][0]
			elif products[prod_id].supply_method == 'produce':
				location_id = stock_locations['lot_stock_id'][0]
			else:
				continue
			proc_id = proc_obj.create(cr, uid, {
				'name': 'PROC:Automatic OP for product:%s' % products[prod_id].name,
				'origin': 'SCHEDULER',
				'date_planned': newdate.strftime('%Y-%m-%d'),
				'product_id': prod_id,
				'product_qty': -available,
				'product_uom': products[prod_id].uom_id.id,
				'location_id': location_id,
				'procure_method': 'make_to_order',
				})
			wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
			wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_check', cr)


def _procure_orderpoint_confirm(self, cr, uid, automatic=False,\
		use_new_cursor=False, context=None, user_id=False):
	'''
	use_new_cursor: False or the dbname
	'''
	if not context:
		context={}
	if use_new_cursor:
		cr = pooler.get_db(use_new_cursor).cursor()
	pool = pooler.get_pool(cr.dbname)
	orderpoint_obj = pool.get('stock.warehouse.orderpoint')
	location_obj = pool.get('stock.location')
	procurement_obj = pool.get('mrp.procurement')
	request_obj = pool.get('res.request')
	wf_service = netsvc.LocalService("workflow")
	report = []
	offset = 0
	ids = [1]
	if automatic:
		create_automatic_op(cr, uid, context=context)
	while ids:
		cr.execute('SELECT id ' \
				'FROM stock_warehouse_orderpoint ' \
				'WHERE active OFFSET %d LIMIT 100', (offset,))
		ids = map(lambda x: x[0], cr.fetchall())
		for op in orderpoint_obj.browse(cr, uid, ids):
			#if op.procurement_id and op.procurement_id.purchase_id:
			#	if (op.procurement_id.purchase_id.state=='confirmed'):
			#		#
			#		# TODO: Should write a request with this warning
			#		#
			#		continue
			#	elif op.procurement_id.purchase_id.state=='draft':
			#		wf_service = netsvc.LocalService("workflow")
			#		wf_service.trg_validate(uid, 'purchase.order',
			#				op.procurement_id.purchase_id.id, 'purchase_cancel', cr)
			try:
				prods = location_obj._product_virtual_get(cr, uid,
						op.warehouse_id.lot_stock_id.id, [op.product_id.id],
						{'uom': op.product_uom.id})[op.product_id.id]
				if prods < op.product_min_qty:
					# order the quantity necessary to get to max(min_qty, max_qty)
					qty = max(op.product_min_qty, op.product_max_qty)-prods
					reste = qty % op.qty_multiple
					if reste>0:
						qty += op.qty_multiple-reste
					newdate = DateTime.now() + DateTime.RelativeDateTime(
							days=op.product_id.seller_delay)
					if op.product_id.supply_method == 'buy':
						location_id = op.warehouse_id.lot_input_id
					elif op.product_id.supply_method == 'produce':
						location_id = op.warehouse_id.lot_stock_id
					else:
						continue
					proc_id = procurement_obj.create(cr, uid, {
						'name': 'OP:'+str(op.id),
						'date_planned': newdate.strftime('%Y-%m-%d'),
						'product_id': op.product_id.id,
						'product_qty': qty,
						'product_uom': op.product_uom.id,
						'location_id': op.warehouse_id.lot_input_id.id,
						'procure_method': 'make_to_order',
						'origin': op.name
					})
					wf_service.trg_validate(uid, 'mrp.procurement', proc_id,
							'button_confirm', cr)
					wf_service.trg_validate(uid, 'mrp.procurement', proc_id,
							'button_check', cr)
					orderpoint_obj.write(cr, uid, [op.id],
							{'procurement_id': proc_id})
			except Exception, e:
				report.append('OP %d:\n%s\n' % (op.id, str(e)))
		offset += len(ids)
		if use_new_cursor:
			cr.commit()
	if user_id and report:
		request_obj.create(cr, uid, {
			'name': 'Orderpoint report.',
			'act_from': user_id,
			'act_to': user_id,
			'body': '\n'.join(report)
			})
	if use_new_cursor:
		cr.commit()
		cr.close()
	return {}


