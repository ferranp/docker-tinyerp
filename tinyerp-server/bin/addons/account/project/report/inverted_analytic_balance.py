##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import pooler
import time
from report import report_sxw

class account_inverted_analytic_balance(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(account_inverted_analytic_balance, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'time': time,
			'lines_g': self._lines_g,
			'lines_a': self._lines_a,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			'sum_balance': self._sum_balance,
			'sum_quantity': self._sum_quantity,
		})

	def _lines_g(self, accounts, date1, date2):
		ids = map(lambda x: x.id, accounts)
		self.cr.execute("SELECT aa.name AS name, aa.code AS code, sum(aal.amount) AS balance, sum(aal.unit_amount) AS quantity, aa.id AS id \
				FROM account_analytic_line AS aal, account_account AS aa \
				WHERE (aal.general_account_id=aa.id) AND (aal.account_id IN ("+','.join(map(str, ids))+")) AND (date>=%s) AND (date<=%s) AND aa.active \
				GROUP BY aal.general_account_id, aa.name, aa.code, aal.code, aa.id ORDER BY aal.code", (date1, date2))
		res = self.cr.dictfetchall()

		for r in res:
			if r['balance'] > 0:
				r['debit'] = r['balance']
				r['credit'] = 0.0
			elif r['balance'] < 0:
				r['debit'] =  0.0
				r['credit'] = -r['balance']
			else:
				r['debit'] = 0.0
				r['credit'] = 0.0
		return res

	def _lines_a(self, accounts, general_account_id, date1, date2):
		ids = map(lambda x: x.id, accounts)
		self.cr.execute("SELECT sum(aal.amount) AS balance, sum(aal.unit_amount) AS quantity, aaa.code AS code, aaa.name AS name, account_id \
				FROM account_analytic_line AS aal, account_analytic_account AS aaa \
				WHERE aal.account_id=aaa.id AND aal.account_id IN ("+','.join(map(str, ids))+") AND aal.general_account_id=%d AND aal.date>=%s AND aal.date<=%s \
				GROUP BY aal.account_id, general_account_id, aaa.code, aaa.name ORDER BY aal.account_id", (general_account_id, date1, date2))
		res = self.cr.dictfetchall()

		aaa_obj = self.pool.get('account.analytic.account')
		res2 = aaa_obj.read(self.cr, self.uid, ids, ['complete_name'])
		complete_name = {}
		for r in res2:
			complete_name[r['id']] = r['complete_name']
		for r in res:
			r['complete_name'] = complete_name[r['account_id']]
			if r['balance'] > 0:
				r['debit'] = r['balance']
				r['credit'] = 0.0
			elif r['balance'] < 0:
				r['debit'] = 0.0
				r['credit'] = -r['balance']
			else:
				r['debit'] = 0.0
				r['credit'] = 0.0
		return res

	def _sum_debit(self, accounts, date1, date2):
		ids = map(lambda x: x.id, accounts)
		self.cr.execute("SELECT sum(amount) \
				FROM account_analytic_line \
				WHERE account_id IN ("+','.join(map(str, ids))+") AND date>=%s AND date<=%s AND amount>0", (date1, date2))
		return self.cr.fetchone()[0] or 0.0
		
	def _sum_credit(self, accounts, date1, date2):
		ids = map(lambda x: x.id, accounts)
		self.cr.execute("SELECT -sum(amount) \
				FROM account_analytic_line \
				WHERE account_id IN ("+','.join(map(str, ids))+") AND date>=%s AND date<=%s AND amount<0", (date1, date2))
		return self.cr.fetchone()[0] or 0.0

	def _sum_balance(self, accounts, date1, date2):
		debit = self._sum_debit(accounts, date1, date2)
		credit = self._sum_credit(accounts, date1, date2)
		return (debit-credit)

	def _sum_quantity(self, accounts, date1, date2):
		ids = map(lambda x: x.id, accounts)
		self.cr.execute("SELECT sum(unit_amount) \
				FROM account_analytic_line \
				WHERE account_id IN ("+','.join(map(str, ids))+") AND date>=%s AND date<=%s", (date1, date2))
		return self.cr.fetchone()[0] or 0.0

report_sxw.report_sxw('report.account.analytic.account.inverted.balance', 'account.analytic.account', 'addons/account/project/report/inverted_analytic_balance.rml',parser=account_inverted_analytic_balance, header=False)

