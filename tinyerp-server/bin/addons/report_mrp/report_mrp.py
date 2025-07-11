# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2007 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
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


class report_workcenter_load(osv.osv):
	_name="report.workcenter.load"
	_description="Workcenter Load"
	_auto = False
	_columns = {
		'name': fields.char('Week', size=64, required=True),
		'workcenter_id': fields.many2one('mrp.workcenter', 'Workcenter', required=True),
		'cycle': fields.float('Nbr of cycle'),
		'hour': fields.float('Nbr of hour'),
	}

	def init(self, cr):
		cr.execute("""
			create or replace view report_workcenter_load as (
				SELECT
					min(wl.id) as id,
					to_char(p.date_planned,'YYYY:IW') as name,
					SUM(wl.hour) AS hour,
					SUM(wl.cycle) AS cycle,
					wl.workcenter_id as workcenter_id
				FROM
					mrp_production_workcenter_line wl
					LEFT JOIN mrp_production p
						ON p.id = wl.production_id
				GROUP BY
					wl.workcenter_id,
					to_char(p.date_planned,'YYYY:IW')
			)""")

report_workcenter_load()


class report_mrp_inout(osv.osv):
	_name="report.mrp.inout"
	_description="Stock value variation"
	_auto = False
	_rec_name = 'date'
	_columns = {
		'date': fields.char('Week', size=64, required=True),
		'value': fields.float('Stock value', required=True, digits=(16,2)),
	}

	def init(self, cr):
		cr.execute("""
			create or replace view report_mrp_inout as (
				select
					min(sm.id) as id,
					to_char(sm.date_planned,'YYYY:IW') as date,
					sum(case when (sl.usage='internal') then
						pt.standard_price * sm.product_qty
					else
						0.0
					end - case when (sl2.usage='internal') then
						pt.standard_price * sm.product_qty
					else
						0.0
					end) as value
				from
					stock_move sm
				left join product_product pp
					on (pp.id = sm.product_id)
				left join product_template pt
					on (pt.id = pp.product_tmpl_id)
				left join stock_location sl
					on ( sl.id = sm.location_id)
				left join stock_location sl2
					on ( sl2.id = sm.location_dest_id)
				where
					sm.state in ('waiting','confirmed','assigned')
				group by
					to_char(sm.date_planned,'YYYY:IW')
			)""")

report_mrp_inout()

