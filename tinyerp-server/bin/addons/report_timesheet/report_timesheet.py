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

class report_timesheet_user(osv.osv):
	_name = "report_timesheet.user"
	_description = "Timesheet per day"
	_auto = False
	_columns = {
		'name': fields.date('Date', readonly=True),
		'user_id':fields.many2one('res.users', 'User', readonly=True),
		'quantity': fields.float('Quantity', readonly=True),
		'cost': fields.float('Cost', readonly=True)
	}
	_order = 'name desc,user_id desc'
	def init(self, cr):
		cr.execute("""
			create or replace view report_timesheet_user as (
				select
					min(l.id) as id,
					l.date as name,
					l.user_id,
					sum(l.unit_amount) as quantity,
					sum(l.amount) as cost
				from
					account_analytic_line l
				where
					user_id is not null
				group by l.date, l.user_id
			)
		""")
report_timesheet_user()

class report_timesheet_account(osv.osv):
	_name = "report_timesheet.account"
	_description = "Timesheet per account"
	_auto = False
	_columns = {
		'name': fields.date('Month', readonly=True),
		'user_id':fields.many2one('res.users', 'User', readonly=True),
		'account_id':fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
		'quantity': fields.float('Quantity', readonly=True),
	}
	_order = 'name desc,account_id desc,user_id desc'
	def init(self, cr):
		cr.execute("""
			create or replace view report_timesheet_account as (
				select
					min(id) as id,
					substring(create_date for 7)||'-01' as name,
					user_id,
					account_id,
					sum(unit_amount) as quantity
				from
					account_analytic_line
				group by
					substring(create_date for 7), user_id, account_id
			)
		""")
report_timesheet_account()


class report_timesheet_account_date(osv.osv):
	_name = "report_timesheet.account.date"
	_description = "Daily timesheet per account"
	_auto = False
	_columns = {
		'name': fields.date('Date', readonly=True),
		'user_id':fields.many2one('res.users', 'User', readonly=True),
		'account_id':fields.many2one('account.analytic.account', 'Analytic Account', readonly=True),
		'quantity': fields.float('Quantity', readonly=True),
	}
	_order = 'name desc,account_id desc,user_id desc'
	def init(self, cr):
		cr.execute("""
			create or replace view report_timesheet_account_date as (
				select
					min(id) as id,
					date as name,
					user_id,
					account_id,
					sum(unit_amount) as quantity
				from
					account_analytic_line
				group by
					date, user_id, account_id
			)
		""")
report_timesheet_account_date()



class report_timesheet_invoice(osv.osv):
	_name = "report_timesheet.invoice"
	_description = "Costs to invoice"
	_auto = False
	_columns = {
		'user_id':fields.many2one('res.users', 'User', readonly=True),
		'account_id':fields.many2one('account.analytic.account', 'Project', readonly=True),
		'manager_id':fields.many2one('res.users', 'Manager', readonly=True),
		'quantity': fields.float('Quantity', readonly=True),
		'amount_invoice': fields.float('To invoice', readonly=True)
	}
	_rec_name = 'user_id'
	_order = 'user_id desc'
	def init(self, cr):
		cr.execute("""
			create or replace view report_timesheet_invoice as (
				select
					min(l.id) as id,
					l.user_id as user_id,
					l.account_id as account_id,
					a.user_id as manager_id,
					sum(l.unit_amount) as quantity,
					sum(l.unit_amount * t.list_price) as revenue
				from account_analytic_line l
					left join hr_timesheet_invoice_factor f on (l.to_invoice=f.id)
					left join account_analytic_account a on (l.account_id=a.id)
					left join product_product p on (l.to_invoice=f.id)
					left join product_template t on (l.to_invoice=f.id)
				where
					l.to_invoice is not null and
					l.invoice_id is null
				group by
					l.user_id,
					l.account_id,
					a.user_id
			)
		""")
report_timesheet_invoice()
