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

from osv import fields, osv

def _code_get(self, cr, uid, context={}):
	acc_type_obj = self.pool.get('account.account.type')
	ids = acc_type_obj.search(cr, uid, [])
	res = acc_type_obj.read(cr, uid, ids, ['code', 'name'], context)
	return [(r['code'], r['name']) for r in res]


class account_followup_stat(osv.osv):
	_name = "account_followup.stat"
	_description = "Followup statistics"
	_auto = False
	_columns = {
		'name': fields.many2one('res.partner', 'Partner', readonly=True),
		'account_type': fields.selection(_code_get, 'Account Type', readonly=True),
		'date_move':fields.date('First move', readonly=True),
		'date_move_last':fields.date('Last move', readonly=True),
		'date_followup':fields.date('Latest followup', readonly=True),
		'followup_id': fields.many2one('account_followup.followup.line',
			'Follow Ups', readonly=True, ondelete="cascade"),
		'balance':fields.float('Balance', readonly=True),
		'debit':fields.float('Debit', readonly=True),
		'credit':fields.float('Credit', readonly=True),
	}
	_order = 'date_move'
	def init(self, cr):
		cr.execute("""
			create or replace view account_followup_stat as (
				select
					l.partner_id as id,
					l.partner_id as name,
					min(l.date) as date_move,
					max(l.date) as date_move_last,
					max(l.followup_date) as date_followup,
					max(l.followup_line_id) as followup_id,
					sum(l.debit) as debit,
					sum(l.credit) as credit,
					sum(l.debit - l.credit) as balance,
					a.type as account_type
				from
					account_move_line l
				left join
					account_account a on (l.account_id=a.id)
				where
					l.reconcile_id is NULL and
					a.type in ('receivable', 'payable')
					and a.active
				group by
					l.partner_id, a.type
			)""")
account_followup_stat()



