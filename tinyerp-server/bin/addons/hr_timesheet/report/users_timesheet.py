##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: user_timesheet.py 4229 2006-10-13 15:11:17Z ged $
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

def lengthmonth(year, month):
	if month == 2 and ((year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))):
		return 29
	return [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month]

def emp_create_xml(cr, id, som, eom):
	# Computing the attendence by analytical account
	cr.execute(
		"select line.date, (unit_amount * unit.factor) as amount "\
		"from account_analytic_line as line, hr_analytic_timesheet as hr, "\
		"product_uom as unit "\
		"where hr.line_id=line.id "\
		"and product_uom_id = unit.id "\
		"and line.user_id=%d and line.date >= %s and line.date < %s "
		"order by line.date",
		(id, som.strftime('%Y-%m-%d'), eom.strftime('%Y-%m-%d')))
	
	# Sum by day
	month = {}
	for presence in cr.dictfetchall():
		day = int(presence['date'][-2:])
		month[day] = month.get(day, 0.0) + presence['amount']
	
	xml = '''
	<time-element date="%s">
		<amount>%.2f</amount>
	</time-element>
	'''
	time_xml = ([xml % (day, amount) for day, amount in month.iteritems()])
	
	# Computing the employee
	cr.execute("select name from res_users where id=%d", (id,))
	emp = cr.fetchone()[0]
	
	# Computing the xml
	xml = '''
	<employee id="%d" name="%s">
	%s
	</employee>
	''' % (id, toxml(emp), '\n'.join(time_xml))
	return xml

class report_custom(report_rml):
	def create_xml(self, cr, uid, ids, data, context):
	
		# Computing the dates (start of month: som, and end of month: eom)
		som = datetime.date(data['form']['year'], data['form']['month'], 1)
		eom = som + datetime.timedelta(lengthmonth(som.year, som.month))
		date_xml = ['<date month="%s" year="%d" />' % (som.strftime('%B'), som.year), '<days>']
		date_xml += ['<day number="%d" name="%s" />' % (x, som.replace(day=x).strftime('%a')) for x in range(1, lengthmonth(som.year, som.month)+1)]
		date_xml.append('</days>')
		date_xml.append('<cols>2.5cm%s,2cm</cols>\n' % (',0.7cm' * lengthmonth(som.year, som.month)))
		
		emp_xml=''
		for id in data['form']['user_ids'][0][2]:
			emp_xml += emp_create_xml(cr, id, som, eom)

		# Computing the xml
		xml='''<?xml version="1.0" encoding="UTF-8" ?>
		<report>
		%s
		%s
		</report>
		''' % (date_xml, emp_xml)
		return xml

report_custom('report.hr.analytical.timesheet_users', 'hr.employee', '', 'addons/hr_timesheet/report/users_timesheet.xsl')
