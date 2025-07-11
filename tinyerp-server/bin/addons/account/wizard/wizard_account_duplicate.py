##############################################################################
#
# Copyright (c) 2007 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
import pooler

duplicate_form = '''<?xml version="1.0"?>
<form string="Duplicate account charts">
	<field name="company_id"/>
</form>'''

duplicate_fields = {
	'company_id': {'string': 'Company', 'type': 'many2one', 'relation': 'res.company', 'required': True},
}

def _do_duplicate(self, cr, uid, data, context):
	account_obj = pooler.get_pool(cr.dbname).get('account.account')
	account_obj.copy(cr, uid, data['id'], data['form'], context=context)
	return {}

class wizard_account_duplicate(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type': 'form', 'arch': duplicate_form, 'fields': duplicate_fields, 'state': (('end', 'Cancel'), ('duplicate', 'Duplicate'))},
		},
		'duplicate': {
			'actions': [_do_duplicate],
			'result': {'type': 'state', 'state': 'end'},
		},
	}
wizard_account_duplicate('account.wizard.account.duplicate')
