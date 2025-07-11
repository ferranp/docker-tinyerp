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

import wizard
import netsvc

_spread_form = '''<?xml version="1.0"?>
<form string="Spread">
	<field name="fiscalyear"/>
	<newline/>
	<field name="quantity"/>
	<field name="amount"/>
</form>'''

_spread_fields = {
	'fiscalyear': {'string':'Fiscal Year', 'type':'many2one', 'relation':'account.fiscalyear', 'required':True},
	'quantity': {'string':'Quantity', 'type':'float', 'digits':(16,2)},
	'amount': {'string':'Amount', 'type':'float', 'digits':(16,2)},
}

class wizard_account_analytic_budget_spread(wizard.interface):
	def _spread(self, cr, uid, data, context):
		service = netsvc.LocalService("object_proxy")
		form = data['form']
		res = service.execute(cr.dbname, uid, 'account.analytic.budget.post', 'spread', data['ids'], form['fiscalyear'], form['quantity'], form['amount'])
		return {}
		
	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':_spread_form, 'fields':_spread_fields, 'state':[('end','Cancel'),('spread','Spread')]}
		},
		'spread': {
			'actions': [_spread],
			'result': {'type':'state', 'state':'end'}
		}
	}
wizard_account_analytic_budget_spread('account.analytic.budget.spread')

