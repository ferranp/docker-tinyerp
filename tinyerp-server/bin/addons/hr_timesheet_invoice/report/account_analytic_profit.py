##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting FROM its eventual inadequacies AND bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees AND support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it AND/or
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

from report import report_sxw
import pooler

class account_analytic_profit(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(account_analytic_profit, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'lines': self._lines,
			'user_ids': self._user_ids,
			'journal_ids': self._journal_ids,
			'line': self._line,
		})
	def _user_ids(self, lines):
		user_obj=pooler.get_pool(self.cr.dbname).get('res.users')
		ids=list(set([b.user_id.id for b in lines]))
		res=user_obj.browse(self.cr, self.uid, ids)
		return res

	def _journal_ids(self, form, user_id):
		line_obj=pooler.get_pool(self.cr.dbname).get('account.analytic.line')
		journal_obj=pooler.get_pool(self.cr.dbname).get('account.analytic.journal')
		line_ids=line_obj.search(self.cr, self.uid, [
			('date', '>=', form['date_from']),
			('date', '<=', form['date_to']),
			('journal_id', 'in', form['journal_ids'][0][2]),
			('user_id', '=', user_id),
			])
		ids=list(set([b.journal_id.id for b in line_obj.browse(self.cr, self.uid, line_ids)]))
		res=journal_obj.browse(self.cr, self.uid, ids)
		return res

	def _line(self, form, journal_ids, user_ids):
		pool=pooler.get_pool(self.cr.dbname)
		line_obj=pool.get('account.analytic.line')
		product_obj=pool.get('product.product')
		price_obj=pool.get('product.pricelist')
		ids=line_obj.search(self.cr, self.uid, [
				('date', '>=', form['date_from']),
				('date', '<=', form['date_to']),
				('journal_id', 'in', journal_ids),
				('user_id', 'in', user_ids),
				])
		res={}
		for line in line_obj.browse(self.cr, self.uid, ids):
			if line.to_invoice:
				id=line.to_invoice.id
				name=line.to_invoice.name
				discount=line.to_invoice.factor
			else:
				if line.account_id.pricelist_id:
					name="Fixed Price"
					discount=0.0
					id=0
				else:
					name="/"
					discount=1.0
					id = -1
			if line.account_id.pricelist_id:
				pl=line.account_id.pricelist_id.id
				price=price_obj.price_get(self.cr, self.uid, [pl], line.product_id.id, line.unit_amount or 1.0, line.account_id.partner_id.id)[pl]
			else:
				price=0.0
			if id not in res:
				res[id]={'name': name, 'amount': 0, 'cost':0, 'unit_amount':0,}
			res[id]['amount']+=round(price * line.unit_amount * (1-(discount or 0.0)/100.0), 2)
			res[id]['cost']+=line.amount
			res[id]['unit_amount']+=line.unit_amount
		for id in res:
			res[id]['profit']=res[id]['amount']+res[id]['cost']
			res[id]['eff']=abs(round(res[id]['amount'] / res[id]['cost'] * 100, 2))
		return res.values()

	def _lines(self, form):
		line_obj=pooler.get_pool(self.cr.dbname).get('account.analytic.line')
		ids=line_obj.search(self.cr, self.uid, [
			('date', '>=', form['date_from']),
			('date', '<=', form['date_to']),
			('journal_id', 'in', form['journal_ids'][0][2]),
			('user_id', 'in', form['employee_ids'][0][2]),
			])
		res=line_obj.browse(self.cr, self.uid, ids)
		return res

report_sxw.report_sxw('report.account.analytic.profit', 'account.analytic.line', 'addons/hr_timesheet_invoice/report/account_analytic_profit.rml', parser=account_analytic_profit)
