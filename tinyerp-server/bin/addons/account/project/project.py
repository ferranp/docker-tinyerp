##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import time
import operator

from osv import fields
from osv import osv

#
# Model definition
#

class account_analytic_account(osv.osv):
	_name = 'account.analytic.account'
	_description = "Analytic Accounts"

	def _credit_calc(self, cr, uid, ids, name, arg, context={}):
		acc_set = ",".join(map(str, ids))
		cr.execute("SELECT a.id, COALESCE(SUM(l.amount),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id) WHERE l.amount<0 and a.id IN (%s) GROUP BY a.id" % acc_set)
		r= dict(cr.fetchall())
		for i in ids:
			r.setdefault(i,0.0)
		return r

	def _debit_calc(self, cr, uid, ids, name, arg, context={}):
		
		acc_set = ",".join(map(str, ids))
		cr.execute("SELECT a.id, COALESCE(SUM(l.amount),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id) WHERE l.amount>0 and a.id IN (%s) GROUP BY a.id" % acc_set)
		r= dict(cr.fetchall())
		for i in ids:
			r.setdefault(i,0.0)
		return r



	def _balance_calc(self, cr, uid, ids, name, arg, context={}):
		ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
		acc_set = ",".join(map(str, ids2))
		cr.execute("SELECT a.id, COALESCE(SUM(l.amount),0) FROM account_analytic_account a LEFT JOIN account_analytic_line l ON (a.id=l.account_id) WHERE a.id IN (%s) GROUP BY a.id" % acc_set)
		res = {}
		for account_id, sum in cr.fetchall():
			res[account_id] = sum
			
		cr.execute("SELECT a.id, r.currency_id FROM account_analytic_account a INNER JOIN res_company r ON (a.company_id = r.id) where a.id in (%s)" % acc_set)

		currency= dict(cr.fetchall())

		res_currency= self.pool.get('res.currency')
		for id in ids:
			for child in self.search(cr, uid, [('parent_id', 'child_of', [id])]):
				if child <> id:
					res.setdefault(id, 0.0)
					if  currency[child]<>currency[id] :
						res[id] += res_currency.compute(cr, uid, currency[child], currency[id], res.get(child, 0.0), context=context)
					else:
						res[id] += res.get(child, 0.0)

		cur_obj = res_currency.browse(cr,uid,currency.values(),context)
		cur_obj = dict([(o.id, o) for o in cur_obj])
		for id in ids:
			res[id] = res_currency.round(cr,uid,cur_obj[currency[id]],res.get(id,0.0)) 

		return dict([(i, res[i]) for i in ids ])

	def _quantity_calc(self, cr, uid, ids, name, arg, context={}):
		#XXX must convert into one uom
		ids2 = self.search(cr, uid, [('parent_id', 'child_of', ids)])
		acc_set = ",".join(map(str, ids2))
		cr.execute('SELECT a.id, COALESCE(SUM(l.unit_amount), 0) \
				FROM account_analytic_account a \
					LEFT JOIN account_analytic_line l ON (a.id = l.account_id) \
				WHERE a.id IN ('+acc_set+') GROUP BY a.id')
		res = {}
		for account_id, sum in cr.fetchall():
			res[account_id] = sum

		for id in ids:
			for child in self.search(cr, uid, [('parent_id', 'child_of', [id])]):
				if child <> id:
					res.setdefault(id, 0.0)
					res[id] += res.get(child, 0.0)
		return dict([(i, res[i]) for i in ids])

	def name_get(self, cr, uid, ids, context={}):
		if not len(ids):
			return []
		reads = self.read(cr, uid, ids, ['name','parent_id'], context)
		res = []
		for record in reads:
			name = record['name']
			if record['parent_id']:
				name = record['parent_id'][1]+' / '+name
			res.append((record['id'], name))
		return res

	def _complete_name_calc(self, cr, uid, ids, prop, unknow_none, unknow_dict):
		res = self.name_get(cr, uid, ids)
		return dict(res)

	def _get_company_currency(self, cr, uid, ids, field_name, arg, context={}):
		result = {}
		for rec in self.browse(cr, uid, ids, context):
			result[rec.id] = (rec.company_id.currency_id.id,rec.company_id.currency_id.code) or False
		return result

	_columns = {
		'name' : fields.char('Account name', size=64, required=True),
		'complete_name': fields.function(_complete_name_calc, method=True, type='char', string='Account Name'),
		'code' : fields.char('Account code', size=24),
		'active' : fields.boolean('Active'),
		'type': fields.selection([('view','View'), ('normal','Normal')], 'Account type'),
		'description' : fields.text('Description'),
		'parent_id': fields.many2one('account.analytic.account', 'Parent analytic account', select=2),
		'child_ids': fields.one2many('account.analytic.account', 'parent_id', 'Childs Accounts'),
		'line_ids': fields.one2many('account.analytic.line', 'account_id', 'Analytic entries'),
		'balance' : fields.function(_balance_calc, method=True, type='float', string='Balance'),
		'debit' : fields.function(_debit_calc, method=True, type='float', string='Debit'),
		'credit' : fields.function(_credit_calc, method=True, type='float', string='Credit'),
		'quantity': fields.function(_quantity_calc, method=True, type='float', string='Quantity'),
		'quantity_max': fields.float('Maximal quantity'),
		'partner_id' : fields.many2one('res.partner', 'Associated partner'),
		'contact_id' : fields.many2one('res.partner.address', 'Contact'),
		'user_id' : fields.many2one('res.users', 'Account Manager'),
		'date_start': fields.date('Date Start'),
		'date': fields.date('Date End'),
		'company_id': fields.many2one('res.company', 'Company', required=True),
		'company_currency_id': fields.function(_get_company_currency, method=True, type='many2one', relation='res.currency', string='Currency'),
		'state': fields.selection([('draft','Draft'), ('open','Open'), ('pending','Pending'), ('close','Close'),], 'State', required=True),
	}

	def _default_company(self, cr, uid, context={}):
		user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
		if user.company_id:
			return user.company_id.id
		return self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
	_defaults = {
		'active' : lambda *a : True,
		'type' : lambda *a : 'normal',
		'company_id': _default_company,
		'state' : lambda *a : 'draft',
		'user_id' : lambda self,cr,uid,ctx : uid
	}

	def check_recursion(self, cr, uid, ids, parent=None):
		return super(account_analytic_account, self).check_recursion(cr, uid, ids, parent=parent)

	_order = 'parent_id desc,code'
	_constraints = [
		(check_recursion, 'Error! You can not create recursive account.', ['parent_id'])
	]

	def create(self, cr, uid, vals, context=None):
		parent_id = vals.get('parent_id', 0)
		if ('code' not in vals or not vals['code']) and not parent_id:
			vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'account.analytic.account')
		return super(account_analytic_account, self).create(cr, uid, vals, context=context)

	def copy(self, cr, uid, id, default=None, context={}):
		if not default:
			default = {}
		default['code'] = False
		return super(account_analytic_account, self).copy(cr, uid, id, default, context=context)


	def on_change_parent(self, cr, uid, id, parent_id):
		if not parent_id:
			return {}
		parent = self.read(cr, uid, [parent_id], ['partner_id','code'])[0]
		childs = self.search(cr, uid, [('parent_id', '=', parent_id), ('active', 'in', [True, False])])
		numchild = len(childs)
		if parent['partner_id']:
			partner = parent['partner_id'][0]
		else:
			partner = False
		res = {'value' : {'code' : '%s - %03d' % (parent['code'] or '', numchild + 1),}}
		if partner:
			res['value']['partner_id'] = partner
		return res

	def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
		if not args:
			args=[]
		if not context:
			context={}
		account = self.search(cr, uid, [('code', '=', name)]+args, limit=limit, context=context)
		if not account:
			account = self.search(cr, uid, [('name', 'ilike', '%%%s%%' % name)]+args, limit=limit, context=context)
			newacc = account
			while newacc:
				newacc = self.search(cr, uid, [('parent_id', 'in', newacc)]+args, limit=limit, context=context)
				account+=newacc
		return self.name_get(cr, uid, account, context=context)

account_analytic_account()


class account_analytic_journal(osv.osv):
	_name = 'account.analytic.journal'
	_columns = {
		'name' : fields.char('Journal name', size=64, required=True),
		'code' : fields.char('Journal code', size=8),
		'active' : fields.boolean('Active'),
		'type': fields.selection([('sale','Sale'), ('purchase','Purchase'), ('cash','Cash'), ('general','General'), ('situation','Situation')], 'Type', size=32, required=True, help="Gives the type of the analytic journal. When a document (eg: an invoice) needs to create analytic entries, Tiny ERP will look for a matching journal of the same type."),
		'line_ids' : fields.one2many('account.analytic.line', 'journal_id', 'Lines'),
	}
	_defaults = {
		'active': lambda *a: True,
		'type': lambda *a: 'general',
	}
account_analytic_journal()


# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------

class account_analytic_budget_post(osv.osv):
	_name = 'account.analytic.budget.post'
	_description = 'Budget item'
	_columns = {
		'code': fields.char('Code', size=64, required=True),
		'name': fields.char('Name', size=256, required=True),
		'sens': fields.selection( [('charge','Charge'), ('produit','Product')], 'Direction', required=True),
		'dotation_ids': fields.one2many('account.analytic.budget.post.dotation', 'post_id', 'Expenses'),
		'account_ids': fields.many2many('account.analytic.account', 'account_analytic_budget_rel', 'budget_id', 'account_id', 'Accounts'),
	}
	_defaults = {
		'sens': lambda *a: 'produit',
	}

	def spread(self, cr, uid, ids, fiscalyear_id=False, quantity=0.0, amount=0.0):

		dobj = self.pool.get('account.analytic.budget.post.dotation')
		for o in self.browse(cr, uid, ids):
			# delete dotations for this post
			dobj.unlink(cr, uid, dobj.search(cr, uid, [('post_id','=',o.id)]))

			# create one dotation per period in the fiscal year, and spread the total amount/quantity over those dotations
			fy = self.pool.get('account.fiscalyear').browse(cr, uid, [fiscalyear_id])[0]
			num = len(fy.period_ids)
			for p in fy.period_ids:
				dobj.create(cr, uid, {'post_id': o.id, 'period_id': p.id, 'quantity': quantity/num, 'amount': amount/num})
		return True
account_analytic_budget_post()

class account_analytic_budget_post_dotation(osv.osv):
	_name = 'account.analytic.budget.post.dotation'
	_description = "Budget item endowment"
	_columns = {
		'name': fields.char('Name', size=64),
		'post_id': fields.many2one('account.analytic.budget.post', 'Item', select=True),
		'period_id': fields.many2one('account.period', 'Period'),
		'quantity': fields.float('Quantity', digits=(16,2)),
		'amount': fields.float('Amount', digits=(16,2)),
	}
account_analytic_budget_post_dotation()
