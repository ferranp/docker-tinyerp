##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: gantt_report.py 1005 2005-07-25 08:41:42Z nicoe $
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

import StringIO

from report.render import render
from report.interface import report_int

from mx import DateTime
import time

from pychart import *
import pychart.legend

import _burndown

class external_pdf(render):
	def __init__(self, pdf):
		render.__init__(self)
		self.pdf = pdf
		self.output_type='pdf'
	def _render(self):
		return self.pdf

def burndown_chart(cr, uid, tasks_id, date_start, date_stop):
	latest = False
	cr.execute('select id,date_start,state,planned_hours from project_task where id in ('+','.join(map(str,tasks_id))+') order by date_start')
	tasks = cr.fetchall()
	cr.execute('select id,date_close,state,planned_hours*progress/100 from project_task where id in ('+','.join(map(str,tasks_id))+') and state in (%s,%s) order by date_close', ('progress','done'))
	tasks2 = cr.fetchall()
	current_date = date_start
	total = 0
	done = 0
	result = []
	while current_date<=date_stop:
		while len(tasks) and tasks[0][1] and tasks[0][1][:10]<=current_date:
			total += tasks.pop(0)[3]
		while len(tasks2) and tasks2[0][1] and tasks2[0][1][:10]<=current_date:
			t2 = tasks2.pop(0)
			if t2[2]<>'cancel':
				done += t2[3]
			else:
				total -= t2[3]
		result.append( (int(time.mktime(time.strptime(current_date,'%Y-%m-%d'))), total-done) )
		current_date = (DateTime.strptime(current_date, '%Y-%m-%d') + DateTime.RelativeDateTime(days=1)).strftime('%Y-%m-%d')
		if not len(tasks) and not len(tasks2):
			break
	result.append( (int(time.mktime(time.strptime(date_stop,'%Y-%m-%d'))), 0) )
	return result

class report_tasks(report_int):
	def create(self, cr, uid, ids, datas, context={}):
		io = StringIO.StringIO()

		if 'date_start' not in datas:
			cr.execute('select min(date_start) from project_task where id in ('+','.join(map(str,ids))+')')
			dt = cr.fetchone()[0]
			if dt:
				datas['date_start'] = dt[:10]
			else:
				datas['date_start'] = time.strftime('%Y-%m-%d')
		if 'date_stop' not in datas:
			cr.execute('select max(date_start),max(date_close) from project_task where id in ('+','.join(map(str,ids))+')')
			res = cr.fetchone()
			datas['date_stop'] = (res[0] and res[0][:10]) or time.strftime('%Y-%m-%d')
			if res[1] and datas['date_stop']<res[1]:
				datas['date_stop'] = res[1][:10]

		date_to_int = lambda x: int(x.ticks())
		int_to_date = lambda x: '/a60{}'+DateTime.localtime(x).strftime('%d/%m/%Y')

		datas = _burndown.compute_burndown(cr, uid, ids, datas['date_start'], datas['date_stop'])

		canv = canvas.init(fname=io, format='pdf')
		canv.set_author("Tiny ERP")

		max_hour = reduce(lambda x,y: max(y[1],x), datas, 0)

		date_to_int = lambda x: int(x.ticks())
		int_to_date = lambda x: '/a60{}'+DateTime.localtime(x).strftime('%d %m %Y')

		def _interval_get(*args):
			result = []
			for i in range(20):
				d = DateTime.localtime(datas[0][0] + (((datas[-1][0]-datas[0][0])/20)*(i+1)))
				res = DateTime.DateTime(d.year, d.month, d.day).ticks()
				if (not result) or result[-1]<>res:
					result.append(res)
			return result

		ar = area.T(x_grid_style=line_style.gray50_dash1,
			x_axis=axis.X(label="Date", format=int_to_date),
			y_axis=axis.Y(label="Burndown Chart - Planned Hours"),
			x_grid_interval=_interval_get,
			x_range = (datas[0][0],datas[-1][0]),
			y_range = (0,max_hour),
			legend = None,
			size = (680,450))
		ar.add_plot(line_plot.T(data=datas))
		ar.draw(canv)
		canv.close()

		self.obj = external_pdf(io.getvalue())
		self.obj.render()
		return (self.obj.pdf,'pdf')
report_tasks('report.project.tasks.burndown')
