##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
from osv import fields
from osv import osv


class hr_employee(osv.osv):
	_name = "hr.employee"
	_inherit = "hr.employee"
	_columns = {
		'product_id': fields.many2one('product.product', 'Product'),
		'journal_id': fields.many2one('account.analytic.journal', 'Analytic Journal')
	}
hr_employee()


class hr_analytic_timesheet(osv.osv):
	_name = "hr.analytic.timesheet"
	_table = 'hr_analytic_timesheet'
	_description = "Timesheet line"
	_inherits = {'account.analytic.line': 'line_id'}
	_order = "id desc"
	_columns = {
		'line_id' : fields.many2one('account.analytic.line', 'Analytic line', ondelete='cascade'),
	}

	def unlink(self, cr, uid, ids, context={}):
		toremove = {}
		for obj in self.browse(cr, uid, ids, context):
			toremove[obj.line_id.id] = True
		self.pool.get('account.analytic.line').unlink(cr, uid, toremove.keys(), context)
		return super(hr_analytic_timesheet, self).unlink(cr, uid, ids, context)


	def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount, unit, context={}):
		res = {}
		if prod_id and unit_amount:
			res = self.pool.get('account.analytic.line').on_change_unit_amount(cr, uid, id, prod_id, unit_amount,unit, context)
		return res

	def _getEmployeeProduct(self, cr, uid, context):
		emp_obj = self.pool.get('hr.employee')
		emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id', uid))])
		if emp_id:
			emp=emp_obj.browse(cr, uid, emp_id[0], context)
			if emp.product_id:
				return emp.product_id.id
		return False

	def _getEmployeeUnit(self, cr, uid, context):
		emp_obj = self.pool.get('hr.employee')
		emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id', uid))])
		if emp_id:
			emp=emp_obj.browse(cr, uid, emp_id[0], context)
			if emp.product_id:
				return emp.product_id.uom_id.id
		return False

	def _getGeneralAccount(self, cr, uid, context):
		emp_obj = self.pool.get('hr.employee')
		emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id', uid))])
		if emp_id:
			emp = self.pool.get('hr.employee').browse(cr, uid, emp_id[0], context=context)
			if bool(emp.product_id):
				a =  emp.product_id.product_tmpl_id.property_account_expense.id
				if not a:
					a = emp.product_id.categ_id.property_account_expense_categ.id
				if a:
					return a
		return False

	def _getAnalyticJournal(self, cr, uid, context):
		emp_obj = self.pool.get('hr.employee')
		emp_id = emp_obj.search(cr, uid, [('user_id', '=', context.get('user_id', uid))])
		if emp_id:
			emp = self.pool.get('hr.employee').browse(cr, uid, emp_id[0], context=context)
			if emp.journal_id:
				return emp.journal_id.id
		return False


	_defaults = {
		'product_uom_id' : _getEmployeeUnit,
		'product_id' : _getEmployeeProduct,
		'general_account_id' : _getGeneralAccount,
		'journal_id' : _getAnalyticJournal,
		'date' : lambda self,cr,uid,ctx: ctx.get('date', time.strftime('%Y-%m-%d')),
		'user_id' : lambda obj, cr, uid, ctx : ctx.get('user_id', uid),
	}


	def on_change_user_id(self, cr, uid, ids, user_id):
		if not user_id:
			return {}
		return {'value' : {
			'product_id' : self._getEmployeeProduct(cr,user_id, context= {}),
			'product_uom_id' : self._getEmployeeUnit(cr, user_id, context= {}),
			'general_account_id' :self. _getGeneralAccount(cr, user_id, context= {}),
			'journal_id' : self._getAnalyticJournal(cr, user_id, context= {}),
						   }}



hr_analytic_timesheet()
