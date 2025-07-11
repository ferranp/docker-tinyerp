##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: sale.py 1005 2005-07-25 08:41:42Z nicoe $
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

from osv import fields,osv

import time
import mx.DateTime

class report_account_analytic_planning(osv.osv):
	_name = "report_account_analytic.planning"
	_description = "Planning"
	_columns = {
		'name': fields.char('Planning Name', size=32, required=True),
		'user_id': fields.many2one('res.users', 'Responsible', required=True),
		'date_from':fields.date('Start date', required=True),
		'date_to':fields.date('End date', required=True),
		'line_ids': fields.one2many('report_account_analytic.planning.line', 'planning_id', 'Planning lines'),
		'stat_ids': fields.one2many('report_account_analytic.planning.stat', 'planning_id', 'Planning analysis', readonly=True),
		'stat_user_ids': fields.one2many('report_account_analytic.planning.stat.user', 'planning_id', 'Planning by user', readonly=True),
		'stat_account_ids': fields.one2many('report_account_analytic.planning.stat.account', 'planning_id', 'Planning by account', readonly=True),
	}
	_defaults = {
		'name': lambda *a: time.strftime('%Y-%m-%d'),
		'date_from': lambda *a: time.strftime('%Y-%m-01'),
		'date_to': lambda *a: (mx.DateTime.now()+mx.DateTime.RelativeDateTime(months=1,day=1,days=-1)).strftime('%Y-%m-%d'),
		'user_id': lambda self,cr,uid,c: uid
	}
	_order = 'date_from desc'
report_account_analytic_planning()

class report_account_analytic_planning_line(osv.osv):
	_name = "report_account_analytic.planning.line"
	_description = "Planning Line"
	_rec_name = 'user_id'
	_columns = {
		'account_id':fields.many2one('account.analytic.account', 'Analytic account', required=True),
		'planning_id': fields.many2one('report_account_analytic.planning', 'Planning', required=True, ondelete='cascade'),
		'user_id': fields.many2one('res.users', 'User'),
		'amount': fields.float('Quantity', required=True),
		'amount_unit':fields.many2one('product.uom', 'Qty UoM', required=True),
		'note':fields.text('Note', size=64),
	}
	_order = 'user_id,account_id'
report_account_analytic_planning_line()

class report_account_analytic_planning_stat_account(osv.osv):
	_name = "report_account_analytic.planning.stat.account"
	_description = "Planning account stat"
	_rec_name = 'account_id'
	_auto = False
	_log_access = False
	_columns = {
		'planning_id': fields.many2one('report_account_analytic.planning', 'Planning'),
		'account_id': fields.many2one('account.analytic.account', 'Analytic Account', required=True),
		'quantity': fields.float('Quantity', required=True)
	}
	def init(self, cr):
		cr.execute("""
			create or replace view report_account_analytic_planning_stat_account as (
				select
					min(l.id) as id,
					l.account_id as account_id,
					sum(l.amount*u.factor) as quantity,
					l.planning_id
				from
					report_account_analytic_planning_line l
				left join
					product_uom u on (l.amount_unit = u.id)
				group by
					planning_id, account_id
			)
		""")
report_account_analytic_planning_stat_account()

class report_account_analytic_planning_stat(osv.osv):
	_name = "report_account_analytic.planning.stat"
	_description = "Planning stat"
	_rec_name = 'user_id'
	_auto = False
	_log_access = False
	def _sum_amount_real(self, cr, uid, ids, name, args, context):
		result = {}
		for line in self.browse(cr, uid, ids, context):
			if line.user_id:
				cr.execute('select sum(unit_amount) from account_analytic_line where user_id=%d and account_id=%d and date>=%s and date<=%s', (line.user_id.id,line.account_id.id,line.planning_id.date_from,line.planning_id.date_to))
			else:
				cr.execute('select sum(unit_amount) from account_analytic_line where account_id=%d and date>=%s and date<=%s', (line.account_id.id,line.planning_id.date_from,line.planning_id.date_to))
			result[line.id] = cr.fetchone()[0]
		return result
	def _sum_amount_tasks(self, cr, uid, ids, name, args, context):
		result = {}
		for line in self.browse(cr, uid, ids, context):
			where = ''
			if line.user_id:
				where='user_id='+str(line.user_id.id)+' and '
			cr.execute('''select
					sum(planned_hours)
				from
					project_task
				where
				'''+where+'''
					project_id in (select id from project_project where category_id=%d) and
					date_close>=%s and
					date_close<=%s''', (
				line.account_id.id,
				line.planning_id.date_from,
				line.planning_id.date_to)
			)
			result[line.id] = cr.fetchone()[0]
		return result
	_columns = {
		'planning_id': fields.many2one('report_account_analytic.planning', 'Planning'),
		'user_id': fields.many2one('res.users', 'User'),
		'manager_id': fields.many2one('res.users', 'Manager'),
		'account_id': fields.many2one('account.analytic.account', 'Account', required=True),
		'sum_amount': fields.float('Planned hours', required=True),
		'sum_amount_real': fields.function(_sum_amount_real, method=True, string='Timesheet'),
		'sum_amount_tasks': fields.function(_sum_amount_tasks, method=True, string='Tasks'),
	}
	_order = 'planning_id,user_id'
	def init(self, cr):
		cr.execute("""
			create or replace view report_account_analytic_planning_stat as (
				select
					min(l.id) as id,
					l.user_id as user_id,
					a.user_id as manager_id,
					l.account_id as account_id,
					sum(l.amount*u.factor) as sum_amount,
					l.planning_id
				from
					report_account_analytic_planning_line l
				left join
					account_analytic_account a on (a.id = l.account_id)
				left join
					product_uom u on (l.amount_unit = u.id)
				group by
					l.planning_id, l.user_id, l.account_id, a.user_id
			)
		""")
report_account_analytic_planning_stat()

class report_account_analytic_planning_stat_user(osv.osv):
	_name = "report_account_analytic.planning.stat.user"
	_description = "Planning user stat"
	_rec_name = 'user_id'
	_auto = False
	_log_access = False
	_columns = {
		'planning_id': fields.many2one('report_account_analytic.planning', 'Planning', required=True),
		'user_id': fields.many2one('res.users', 'User'),
		'quantity': fields.float('Quantity', required=True)
	}
	def init(self, cr):
		cr.execute("""
			create or replace view report_account_analytic_planning_stat_user as (
				select
					min(l.id) as id,
					l.user_id as user_id,
					sum(l.amount*u.factor) as quantity,
					l.planning_id
				from
					report_account_analytic_planning_line l
				left join
					product_uom u on (l.amount_unit = u.id)
				group by
					planning_id, user_id
			)
		""")
report_account_analytic_planning_stat_user()
