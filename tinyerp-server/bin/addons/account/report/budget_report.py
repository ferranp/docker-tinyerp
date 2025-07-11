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

import time
from report import report_sxw
import datetime
import operator

class budget_report(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(budget_report, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'lines': self.lines,
			'budget_total': self.budget_total,
			'post_total': self.post_total,
			'time': time,
		})

	def post_total(self, post_obj, date1, date2):
		def str2date(date_str):
			return datetime.date.fromtimestamp(time.mktime(time.strptime(date_str, '%Y-%m-%d')))
		def interval(d1str, d2str):
			return (str2date(d2str) - str2date(d1str) + datetime.timedelta(days=1)).days
		prev = reduce(lambda x,d: x + d.amount, post_obj.dotation_ids, 0.0)
		period_days = interval(date1, date2)
		for d in post_obj.dotation_ids:
			i = interval(d.period_id.date_start, d.period_id.date_stop)
		total_days = reduce(lambda x,d: x+interval(d.period_id.date_start, d.period_id.date_stop), post_obj.dotation_ids, 0)
		achievements = reduce(lambda x,l: x+l['achievements'], self.lines(post_obj, date1, date2), 0.0)
		return [{'prev': prev, 'prev_period': prev * period_days / total_days, 'achievements': achievements}]

	def budget_total(self, post_objs, date1, date2):
		res = {'prev': 0.0, 'prev_period': 0.0, 'achievements': 0.0}
		for post_obj in post_objs:
			r = self.post_total(post_obj, date1, date2)[0]
			for k in r:
				res[k] += r[k]
		return [res]
		
	def lines(self, post_obj, date1, date2):
		res = []
		for a in post_obj.account_ids:
	 		self.cr.execute("SELECT COALESCE(SUM(debit-credit), 0) FROM account_move_line WHERE account_id=%d AND date>=%s AND date<=%s and state<>'draft'", (a.id, date1, date2))
			achievements = float(self.cr.fetchone()[0]) * (post_obj.sens=='produit' and -1 or 1)
			res.append({'name': a.name, 'code': a.code, 'achievements': achievements})
		return res
report_sxw.report_sxw('report.account.budget', 'account.budget.post', 'addons/account/report/budget_report.rml',parser=budget_report)

