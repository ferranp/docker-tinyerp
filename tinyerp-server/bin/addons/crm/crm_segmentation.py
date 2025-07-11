##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from osv import fields,osv,orm

import crm_operators


class crm_segmentation(osv.osv):
	'''
		A segmentation is a tool to automatically assign categories on partners.
		These assignations are based on criterions.
	'''
	_name = "crm.segmentation"
	_description = "Partner Segmentation"
	_columns = {
		'name': fields.char('Name', size=64, required=True, help='The name of the segmentation.'),
		'description': fields.text('Description'),
		'categ_id': fields.many2one('res.partner.category', 'Partner Category', required=True, help='The partner category that will be added to partners that match the segmentation criterions after computation.'),
		'exclusif': fields.boolean('Exclusive', help='Check if the category is limited to partners that match the segmentation criterions. If checked, remove the category from partners that doesn\'t match segmentation criterions'),
		'state': fields.selection([('not running','Not Running'),('running','Running')], 'Execution State', readonly=True),
		'partner_id': fields.integer('Max Partner ID processed'),
		'segmentation_line': fields.one2many('crm.segmentation.line', 'segmentation_id', 'Criteria', required=True),
		'som_interval': fields.integer('Days per Periode', help="A period is the average number of days between two cycle of sale or purchase for this segmentation. It's mainly used to detect if a partner has not purchased or buy for a too long time, so we suppose that his state of mind has decreased because he probably bought goods to another supplier. Use this functionnality for recurring businesses."),
		'som_interval_max': fields.integer('Max Interval', help="The computation is made on all events that occured during this interval, the past X periods."),
		'som_interval_decrease': fields.float('Decrease (0>1)', help="If the partner has not purchased (or buied) during a period, decrease the state of mind by this factor. It\'s a multiplication"),
		'som_interval_default': fields.float('Default (0=None)', help="Default state of mind for period preceeding the 'Max Interval' computation. This is the starting state of mind by default if the partner has no event."),
	}
	_defaults = {
		'partner_id': lambda *a: 0,
		'state': lambda *a: 'not running',
		'som_interval_max': lambda *a: 3,
		'som_interval_decrease': lambda *a: 0.8,
		'som_interval_default': lambda *a: 0.5
	}

	def process_continue(self, cr, uid, ids, start=False):
		categs = self.read(cr,uid,ids,['categ_id','exclusif','partner_id'])
		for categ in categs:
			if start:
				if categ['exclusif']:
					cr.execute('delete from res_partner_category_rel where category_id=%d', (categ['categ_id'][0],))
			id = categ['id']
			cr.execute('select id from crm_segmentation_line where segmentation_id=%d', (id,))
			line_ids = [x[0] for x in cr.fetchall()]
			cr.execute('select id from res_partner order by id limit 100 offset %d', (categ['partner_id'],))
			partners = cr.fetchall()
			ok = []
			for (pid,) in partners:
				if self.pool.get('crm.segmentation.line').test(cr, uid, line_ids, pid):
					ok.append(pid)

			for partner_id in ok:
				cr.execute('insert into res_partner_category_rel (category_id,partner_id) values (%d,%d)', (categ['categ_id'][0],partner_id))
			cr.commit()

			if len(partners)==100:
				self.write(cr, uid, [id], {'partner_id':categ['partner_id']+100})
				self.process_continue(cr, uid, [id])
			self.write(cr, uid, [id], {'state':'not running', 'partner_id':0})
			cr.commit()
		return True

	def process_stop(self, cr, uid, ids, *args):
		return self.write(cr, uid, ids, {'state':'not running', 'partner_id':0})

	def process_start(self, cr, uid, ids, *args):
		self.write(cr, uid, ids, {'state':'running', 'partner_id':0})
		return self.process_continue(cr, uid, ids, start=True)
crm_segmentation()

class crm_segmentation_line(osv.osv):
	_name = "crm.segmentation.line"
	_description = "Segmentation line"
	_columns = {
		'name': fields.char('Rule Name', size=64, required=True),
		'segmentation_id': fields.many2one('crm.segmentation', 'Segmentation'),
		'expr_name': fields.selection([('sale','Sale Amount'),('som','State of Mind'),('purchase','Purchase Amount')], 'Control Variable', size=64, required=True),
		'expr_operator': fields.selection([('<','<'),('=','='),('>','>')], 'Operator', required=True),
		'expr_value': fields.float('Value', required=True),
		'operator': fields.selection([('and','Mandatory Expression'),('or','Optional Expression')],'Mandatory / Optionnal', required=True),
	}
	_defaults = {
		'expr_name': lambda *a: 'sale',
		'expr_operator': lambda *a: '>',
		'operator': lambda *a: 'and'
	}
	def test(self, cr, uid, ids, partner_id):
		expression = {'<': lambda x,y: x<y, '=':lambda x,y:x==y, '>':lambda x,y:x>y}
		ok = False
		lst = self.read(cr, uid, ids)
		for l in lst:
			if l['expr_name']=='som':
				datas = self.pool.get('crm.segmentation').read(cr, uid, [l['segmentation_id'][0]], ['som','som_interval','som_interval_max','som_interval_default', 'som_interval_decrease'])
				value = crm_operators.som(cr, uid, partner_id, datas[0])
			elif l['expr_name']=='sale':
				cr.execute('select sum(l.price_unit*l.quantity) from account_invoice_line l left join account_invoice i on (l.invoice_id=i.id) where i.partner_id=%d', (partner_id,))
				value = cr.fetchone()[0] or 0.0
			elif l['expr_name']=='purchase':
				cr.execute('select sum(l.price_unit*l.quantity) from account_invoice_line l left join account_invoice i on (l.invoice_id=i.id) where i.partner_id=%d', (partner_id,))
				value = cr.fetchone()[0] or 0.0
			res = expression[l['expr_operator']](value, l['expr_value'])
			if (not res) and (l['operator']=='and'):
				return False
			if res:
				return True
		return True
crm_segmentation_line()



