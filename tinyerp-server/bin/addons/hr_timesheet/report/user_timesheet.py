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

import datetime

from report.interface import report_rml
from report.interface import toxml 

import pooler

def lengthmonth(year, month):
	if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
		return 29
	return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

class report_custom(report_rml):
	def create_xml(self, cr, uid, ids, data, context):

		# Computing the dates (start of month: som, and end of month: eom)
		som = datetime.date(data['form']['year'], data['form']['month'], 1)
		eom = som + datetime.timedelta(lengthmonth(som.year, som.month))
		date_xml = ['<date month="%s" year="%d" />' % (som.strftime('%B'), som.year), '<days>']
		date_xml += ['<day number="%d" name="%s" />' % (x, som.replace(day=x).strftime('%a')) for x in range(1, lengthmonth(som.year, som.month)+1)]
		date_xml.append('</days>')
		date_xml.append('<cols>2.5cm%s,2cm</cols>\n' % (',0.7cm' * lengthmonth(som.year, som.month)))
		
		# Computing the attendence by analytical account
		cr.execute(
			"select line.date, (unit_amount * unit.factor) as amount, account_id, account.name "\
			"from account_analytic_line as line, hr_analytic_timesheet as hr, "\
			"account_analytic_account as account, product_uom as unit "\
			"where hr.line_id=line.id and line.account_id=account.id "\
			"and product_uom_id = unit.id "\
			"and line.user_id=%d and line.date >= %s and line.date < %s "
			"order by line.date",
			(data['form']['user_id'], som.strftime('%Y-%m-%d'), eom.strftime('%Y-%m-%d')))

		# Sum attendence by account, then by day
		accounts = {}
		for presence in cr.dictfetchall():
			day = int(presence['date'][-2:])
			account = accounts.setdefault((presence['account_id'], presence['name']), {})
			account[day] = account.get(day, 0.0) + presence['amount']
		
		xml = '''
		<time-element date="%s">
			<amount>%.2f</amount>
		</time-element>
		'''
		account_xml = []
		for account, telems in accounts.iteritems():
			aid, aname = account
			aname = pooler.get_pool(cr.dbname).get('account.analytic.account').name_get(cr, uid, [aid], context)
			aname = aname[0][1]

			account_xml.append('<account id="%d" name="%s">' % (aid, toxml(aname)))
			account_xml.append('\n'.join([xml % (day, amount) for day, amount in telems.iteritems()]))
			account_xml.append('</account>')

		# Computing the employee
		cr.execute("select name from res_users where id=%d", (data['form']['user_id'],))
		emp = cr.fetchone()[0]

		# Computing the xml
		xml = '''<?xml version="1.0" encoding="UTF-8" ?>
		<report>
		<employee>%s</employee>
		%s
		</report>
		''' % (toxml(emp), '\n'.join(date_xml) + '\n'.join(account_xml))
		return xml

report_custom('report.hr.analytical.timesheet', 'hr.employee', '', 'addons/hr_timesheet/report/user_timesheet.xsl')

