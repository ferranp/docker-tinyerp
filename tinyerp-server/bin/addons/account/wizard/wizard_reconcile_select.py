##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import wizard

_journal_form = '''<?xml version="1.0"?>
<form string="%s">
	<field name="account_id"/>
</form>''' % ('Reconciliation',)

_journal_fields = {
	'account_id': {'string':'Account', 'type':'many2one', 'relation':'account.account','domain': [('reconcile','=',1)], 'required':True},
}

def _action_open_window(self, cr, uid, data, context):
	return {
		'domain': "[('account_id','=',%d),('reconcile_id','=',False),('state','<>','draft')]" % data['form']['account_id'],
		'name': 'Reconciliation',
		'view_type': 'form',
		'view_mode': 'tree,form',
		'view_id': False,
		'res_model': 'account.move.line',
		'type': 'ir.actions.act_window'
	}

class wiz_rec_select(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type': 'form', 'arch':_journal_form, 'fields':_journal_fields, 'state':[('end','Cancel'),('open','Open for reconciliation')]}
		},
		'open': {
			'actions': [],
			'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
		}
	}
wiz_rec_select('account.move.line.reconcile.select')

