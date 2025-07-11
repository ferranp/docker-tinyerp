##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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
import pooler
from report import report_sxw

#
# Use period and Journal for selection or resources
#
class account_analytic_journal(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(account_analytic_journal, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'time': time,
			'lines': self._lines,
			'lines_a': self._lines_a,
			'sum_general': self._sum_general,
			'sum_analytic': self._sum_analytic,
		})

	def _lines(self, journal_id, date1, date2):
		self.cr.execute('SELECT DISTINCT move_id FROM account_analytic_line WHERE (date>=%s) AND (date<=%s) AND (journal_id=%d) AND (move_id is not null)', (date1, date2, journal_id,))
		ids = map(lambda x: x[0], self.cr.fetchall())
		return self.pool.get('account.move.line').browse(self.cr, self.uid, ids)

	def _lines_a(self, move_id, journal_id, date1, date2):
		ids = self.pool.get('account.analytic.line').search(self.cr, self.uid, [('move_id','=',move_id), ('journal_id','=',journal_id), ('date','>=',date1), ('date','<=',date2)])
		if not ids:
			return []
		return self.pool.get('account.analytic.line').browse(self.cr, self.uid, ids)
		
	def _sum_general(self, journal_id, date1, date2):
		self.cr.execute('SELECT SUM(debit-credit) FROM account_move_line WHERE id IN (SELECT move_id FROM account_analytic_line WHERE (date>=%s) AND (date<=%s) AND (journal_id=%d) AND (move_id is not null))', (date1, date2, journal_id,))
		return self.cr.fetchall()[0][0] or 0

	def _sum_analytic(self, journal_id, date1, date2):
		self.cr.execute("SELECT SUM(amount) FROM account_analytic_line WHERE date>=%s AND date<=%s AND journal_id=%d", (date1, date2, journal_id))
		res = self.cr.dictfetchone()
		return res['sum'] or 0

report_sxw.report_sxw('report.account.analytic.journal', 'account.analytic.journal', 'addons/account/project/report/analytic_journal.rml',parser=account_analytic_journal)

