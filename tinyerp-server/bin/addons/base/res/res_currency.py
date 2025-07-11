# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: account.py 1005 2005-07-25 08:41:42Z nicoe $
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
import netsvc
from osv import fields, osv
import ir

from tools.misc import currency

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

class res_currency(osv.osv):
	def _current_rate(self, cr, uid, ids, name, arg, context={}):
		res={}
		if 'date' in context:
			date=context['date']
		else:
			date=time.strftime('%Y-%m-%d')
		for id in ids:
			cr.execute("SELECT currency_id, rate FROM res_currency_rate WHERE currency_id = %d AND name <= '%s' ORDER BY name desc LIMIT 1" % (id, date))
			if cr.rowcount:
				id, rate=cr.fetchall()[0]
				res[id]=rate
			else:
				res[id]=0
		return res
	_name = "res.currency"
	_description = "Currency"
	_columns = {
		'name': fields.char('Currency', size=32, required=True),
		'code': fields.char('Code', size=3),
		'rate': fields.function(_current_rate, method=True, string='Current rate', digits=(12,6),
			help='The rate of the currency to the currency of rate 1'),
		'rate_ids': fields.one2many('res.currency.rate', 'currency_id', 'Rates'),
		'accuracy': fields.integer('Computational Accuracy'),
		'rounding': fields.float('Rounding factor', digits=(12,6)),
		'active': fields.boolean('Active'),
	}
	_defaults = {
		'active': lambda *a: 1,
	}
	_order = "code"

	def round(self, cr, uid, currency, amount):
		return round(amount / currency.rounding) * currency.rounding

	def is_zero(self, cr, uid, currency, amount):
		return abs(self.round(cr, uid, currency, amount)) < currency.rounding

	def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount, round=True, context={}):
		if not from_currency_id:
			from_currency_id = to_currency_id
		xc=self.browse(cr, uid, [from_currency_id,to_currency_id], context=context)
		from_currency = (xc[0].id == from_currency_id and xc[0]) or xc[1]
		to_currency = (xc[0].id == to_currency_id and xc[0]) or xc[1]
		if from_currency['rate'] == 0 or to_currency['rate'] == 0:
			date = context.get('date', time.strftime('%Y-%m-%d'))
			if from_currency['rate'] == 0:
				code = from_currency.code
			else:
				code = to_currency.code
			raise osv.except_osv('Error', 'No rate found \n' \
					'for the currency: %s \n' \
					'at the date: %s' % (code, date))
		if to_currency_id==from_currency_id:
			if round:
				return self.round(cr, uid, to_currency, from_amount)
			else:
				return from_amount
		else:
			if round:
				return self.round(cr, uid, to_currency, from_amount * to_currency.rate/from_currency.rate)
			else:
				return (from_amount * to_currency.rate/from_currency.rate)
	def name_search(self, cr, uid, name, args=[], operator='ilike', context={}, limit=80):
		args2 = args[:]
		if name:
			args += [('name', operator, name)]
			args2 += [('code', operator, name)]
		ids = self.search(cr, uid, args, limit=limit)
		ids += self.search(cr, uid, args2, limit=limit)
		res = self.name_get(cr, uid, ids, context)
		return res
res_currency()

class res_currency_rate(osv.osv):
	_name = "res.currency.rate"
	_description = "Currency Rate"
	_columns = {
		'name': fields.date('Date', required=True, select=True),
		'rate': fields.float('Rate', digits=(12,6), required=True,
			help='The rate of the currency to the currency of rate 1'),
		'currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
	}
	_defaults = {
		'name': lambda *a: time.strftime('%Y-%m-%d'),
	}
	_order = "name desc"
res_currency_rate()
