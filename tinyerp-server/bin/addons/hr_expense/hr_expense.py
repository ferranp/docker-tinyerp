##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: hr.py 3751 2006-08-09 13:15:36Z mvd $
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

from mx import DateTime
import time

from osv import fields, osv

def _employee_get(obj,cr,uid,context={}):
	ids = obj.pool.get('hr.employee').search(cr, uid, [('user_id','=', uid)])
	if ids:
		return ids[0]
	return False

class hr_expense_expense(osv.osv):
	def copy(self, cr, uid, id, default=None, context={}):
		if not default: default = {}
		default.update( {'invoice_id':False,'date_confirm':False,'date_valid':False,'user_valid':False})
		return super(hr_expense_expense, self).copy(cr, uid, id, default, context)

	def _amount(self, cr, uid, ids, field_name, arg, context):
		id_set = ",".join(map(str, ids))
		cr.execute("SELECT s.id,COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount FROM hr_expense_expense s LEFT OUTER JOIN hr_expense_line l ON (s.id=l.expense_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
		res = dict(cr.fetchall())
		return res

	def _get_currency(self, cr, uid, context):
		user = self.pool.get('res.users').browse(cr, uid, [uid])[0]
		if user.company_id:
			return user.company_id.currency_id.id
		else:
			return self.pool.get('res.currency').search(cr, uid, [('rate','=',1.0)])[0]

	_name = "hr.expense.expense"
	_description = "Expense"
	_columns = {
		'name': fields.char('Expense Sheet', size=128, required=True),
		'id': fields.integer('Sheet ID', readonly=True),
		'ref': fields.char('Reference', size=32),
		'date': fields.date('Date'),
		'journal_id': fields.many2one('account.journal', 'Force Journal'),
		'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
		'user_id': fields.many2one('res.users', 'User', required=True),
		'date_confirm': fields.date('Date Confirmed'),
		'date_valid': fields.date('Date Valided'),
		'user_valid': fields.many2one('res.users', 'Validation User'),
		'account_move_id': fields.many2one('account.move', 'Account Move'),
		'line_ids': fields.one2many('hr.expense.line', 'expense_id', 'Expense Lines'),
		'note': fields.text('Note'),
		'amount': fields.function(_amount, method=True, string='Total Amount'),
		'invoice_id': fields.many2one('account.invoice', 'Invoice'),
		'currency_id': fields.many2one('res.currency', 'Currency', required=True),

		'state': fields.selection([
			('draft', 'Draft'),
			('confirm', 'Waiting confirmation'),
			('accepted', 'Accepted'),
			('invoiced', 'Invoiced'),
			('paid', 'Reimbursed'),
			('canceled', 'Canceled')],
			'State', readonly=True),
	}
	_defaults = {
		'date' : lambda *a: time.strftime('%Y-%m-%d'),
		'state': lambda *a: 'draft',
		'employee_id' : _employee_get,
		'user_id' : lambda cr,uid,id,c={}: id,
		'currency_id': _get_currency,
	}
	def expense_confirm(self, cr, uid, ids, *args):
		#for exp in self.browse(cr, uid, ids):
		self.write(cr, uid, ids, {
			'state':'confirm',
			'date_confirm': time.strftime('%Y-%m-%d')
		})
		return True

	def expense_accept(self, cr, uid, ids, *args):
		self.write(cr, uid, ids, {
			'state':'accepted',
			'date_valid':time.strftime('%Y-%m-%d'),
			'user_valid': uid,
			})
		return True

	def expense_canceled(self, cr, uid, ids, *args):
		self.write(cr, uid, ids, {'state':'canceled'})
		return True

	def expense_paid(self, cr, uid, ids, *args):
		self.write(cr, uid, ids, {'state':'paid'})
		return True

	def action_invoice_create(self, cr, uid, ids):
		res = False
		for exp in self.browse(cr, uid, ids):
			lines = []
			for l in exp.line_ids:
				tax_id = []
				if l.product_id:
					acc = l.product_id.product_tmpl_id.property_account_expense.id
					if not acc:
						acc = l.product_id.categ_id.property_account_expense_categ.id
					tax_id = [x.id for x in l.product_id.supplier_taxes_id]
				else:
					acc = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category')
				lines.append((0, False, {
					'name': l.name,
					'account_id': acc,
					'price_unit': l.unit_amount,
					'quantity': l.unit_quantity,
					'uos_id': l.uom_id.id,
					'product_id': l.product_id and l.product_id.id or False,
					'invoice_line_tax_id': tax_id and [(6, 0, tax_id)] or False,
					'account_analytic_id': l.analytic_account.id,
				}))
			if not exp.employee_id.address_id:
				raise osv.except_osv('Error !', 'The employee must have a contact address')
			acc = exp.employee_id.address_id.partner_id.property_account_payable.id
			inv = {
				'name': exp.name,
				'reference': self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice'),
				'account_id': acc,
				'type': 'in_invoice',
				'partner_id': exp.employee_id.address_id.partner_id.id,
				'address_invoice_id': exp.employee_id.address_id.id,
				'address_contact_id': exp.employee_id.address_id.id,
				'origin': exp.name,
				'invoice_line': lines,
				'price_type': 'tax_included',
				'currency_id': exp.currency_id.id,
			}
			if exp.journal_id:
				inv['journal_id']=exp.journal_id.id
			inv_id = self.pool.get('account.invoice').create(cr, uid, inv, {'type':'in_invoice'})
			self.pool.get('account.invoice').button_compute(cr, uid, [inv_id], {'type':'in_invoice'}, set_total=True)
			self.write(cr, uid, [exp.id], {'invoice_id': inv_id, 'state': 'invoiced'})
			res = inv_id
		return res
hr_expense_expense()


class hr_expense_line(osv.osv):
	_name = "hr.expense.line"
	_description = "Expense Line"
	def _amount(self, cr, uid, ids, field_name, arg, context):
		if not len(ids):
			return {}
		id_set = ",".join(map(str, ids))
		cr.execute("SELECT l.id,COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount FROM hr_expense_line l WHERE id IN ("+id_set+") GROUP BY l.id ")
		res = dict(cr.fetchall())
		return res

	_columns = {
		'name': fields.char('Short Description', size=128, required=True),
		'date_value': fields.date('Date', required=True),
		'expense_id': fields.many2one('hr.expense.expense', 'Expense', ondelete='cascade', select=True),
		'total_amount': fields.function(_amount, method=True, string='Total'),
		'unit_amount': fields.float('Unit Price', readonly=True, states={'draft':[('readonly',False)]}),
		'unit_quantity': fields.float('Quantities', readonly=True, states={'draft':[('readonly',False)]}),
		'product_id': fields.many2one('product.product', 'Product', readonly=True, states={'draft':[('readonly',False)]}),
		'uom_id': fields.many2one('product.uom', 'UoM', readonly=True, states={'draft':[('readonly',False)]}),
		'description': fields.text('Description'),
		'analytic_account': fields.many2one('account.analytic.account','Analytic account'),
		'ref': fields.char('Reference', size=32),
		'sequence' : fields.integer('Sequence'),
	}
	_defaults = {
		'unit_quantity': lambda *a: 1,
		'date_value' : lambda *a: time.strftime('%Y-%m-%d'),
	}
	_order = "sequence"
	def onchange_product_id(self, cr, uid, ids, product_id, uom_id, context={}):
		v={}
		if product_id:
			product=self.pool.get('product.product').browse(cr,uid,product_id, context=context)
			v['name']=product.name
			v['unit_amount']=product.standard_price
			if not uom_id:
				v['uom_id']=product.uom_id.id
		return {'value':v}

hr_expense_line()

# vim:tw=0:noexpandtab
