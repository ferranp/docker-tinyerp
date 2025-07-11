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

import ir
import os, time
import netsvc

import random
import StringIO

import tools
import pooler

from report.render import render 
from report.interface import report_int
from pychart import *

theme.use_color = 1
#theme.scale = 2
random.seed(0)

class external_pdf(render):
	def __init__(self, pdf):
		render.__init__(self)
		self.pdf = pdf
		self.output_type='pdf'
		
	def _render(self):
		return self.pdf

class report_custom(report_int):
	def create(self, cr, uid, ids, datas, context={}):
		assert len(ids), 'You should provide some ids!'
		responsible_data = {}
		responsible_names = {}
		data = []
		minbenef = 999999999999999999999
		maxbenef = 0

		cr.execute('select probability, planned_revenue, planned_cost, user_id, res_users.name as name from crm_case left join res_users on (crm_case.user_id=res_users.id) where crm_case.id in ('+','.join(map(str,ids))+') order by user_id')
		res = cr.dictfetchall()

		for row in res:
			proba = row['probability'] or 0
			cost = row['planned_cost'] or 0
			revenue = row['planned_revenue'] or 0
			userid = row['user_id'] or 0
		
			benefit = revenue - cost
			if benefit > maxbenef:
				maxbenef = benefit
			if benefit < minbenef:
				minbenef = benefit
			
			tuple = (proba * 100,  benefit)
			responsible_data.setdefault(userid, [])
			responsible_data[userid].append(tuple)

			tuple = (proba * 100, cost, benefit)
			data.append(tuple)

			responsible_names[userid] = (row['name'] or '/').replace('/','//')

		minbenef -= maxbenef * 0.05
		maxbenef *= 1.2
		
		ratio = 0.5
		minmaxdiff2 = (maxbenef - minbenef)/2
		
		for l in responsible_data.itervalues():
			for i in range(len(l)):
				percent, benef = l[i]
				proba = percent/100

				current_ratio = 1 + (ratio-1) * proba
				
				newbenef = minmaxdiff2 + ((benef - minbenef - minmaxdiff2) * current_ratio)
				
				l[i] = (percent, newbenef)

#TODO:
#-group by "categorie de probabilites ds graphe du haut"
#-echelle variable

		pdf_string = StringIO.StringIO()
		can = canvas.init(fname=pdf_string, format='pdf')
		
		chart_object.set_defaults(line_plot.T, line_style=None)
		
		xaxis = axis.X(label=None, format="%d%%", tic_interval=20)
		yaxis = axis.Y()

		ar = area.T(
			size = (300,200),
			y_grid_interval = 10000,
			y_grid_style=None,
			x_range = (0,100),
			y_range = (minbenef, maxbenef),
			x_axis = xaxis,
			y_axis = None,
			legend = legend.T()
		)

		for k, d in responsible_data.iteritems():
			fill = fill_style.Plain(bgcolor=color.T(r=random.random(), g=random.random(), b=random.random()))
			tick = tick_mark.Square(size=6, fill_style=fill)
			ar.add_plot(line_plot.T(label=responsible_names[k], data=d, tick_mark=tick))

		ar.draw(can)

		# second graph (top right)
		ar = area.T(legend = legend.T(),
					size = (200,100),
					loc=(100,250),
					x_grid_interval = lambda min, max: [40,60,80,100], 
					x_grid_style=line_style.gray70_dash1,
					x_range = (33, 100),
					x_axis = axis.X(label=None, minor_tic_interval=lambda min,max: [50, 70, 90], format=lambda x: ""),
					y_axis=axis.Y(label="Planned amounts"))

		bar_plot.fill_styles.reset();
		plot1=bar_plot.T(label="Cost", data=data, fill_style=fill_style.red)
		plot2=bar_plot.T(label="Revenue", data=data, hcol=2, stack_on = plot1, fill_style=fill_style.blue)

		ar.add_plot(plot1, plot2)

		ar.draw(can)

		# diagonal "pipeline" lines
		can.line(line_style.black, 0, 200, 300, 150)
		can.line(line_style.black, 0, 0, 300, 50)

		# vertical lines
		ls = line_style.T(width=0.4, color=color.gray70, dash=(2,2))
		for x in range(120, 300, 60):
			can.line(ls, x, 0, x, 250)

		# draw arrows to the right
		a = arrow.fat1
		for y in range(60,150,10):
			a.draw([(285,y), (315,y)], can=can)

		# close canvas so that the file is written to "disk"
		can.close()

		self.obj = external_pdf(pdf_string.getvalue())
		self.obj.render()

		pdf_string.close()
		return (self.obj.pdf, 'pdf')

report_custom('report.crm.case')

