# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

_transaction_form = '''<?xml version="1.0"?>
<form string="ReObrir Periode">
	<separator string="Estàs segur ?" colspan="4"/>
	<field name="sure"/>
</form>'''

_transaction_fields = {
	'sure': {'string':'Marca la casella', 'type':'boolean'},
}

def _data_save(self, cr, uid, data, context):
	mode = 'draft'
	if data['form']['sure']:
		for id in data['ids']:
			cr.execute('update account_journal_period set state=%s where period_id=%d', (mode, id))
			cr.execute('update account_period set state=%s where id=%d', (mode, id))
	return {}

class wiz_journal_close(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel·lar'),('close','ReObrir Periode')]}
		},
		'close': {
			'actions': [_data_save],
			'result': {'type': 'state', 'state':'end'}
		}
	}
wiz_journal_close('account.period.reopen')

