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

import wizard
import datetime

form='''<?xml version="1.0"?>
<form string="Choose">
	<field name="date_from"/>
	<field name="date_to"/>
	<field name="journal_ids" colspan="3"/>
	<field name="employee_ids" colspan="3"/>
</form>'''

class wizard_report(wizard.interface):
	def _date_from(*a):
		return datetime.datetime.today().strftime('%Y-%m-1')
	def _date_to(*a):
		return datetime.datetime.today().strftime('%Y-%m-%d')

	fields={
		'date_from':{
			'string':'From',
			'type':'date',
			'required':True,
			'default':_date_from,
		},
		'date_to':{
			'string':'To',
			'type':'date',
			'required':True,
			'default':_date_to,
		},
		'journal_ids':{
			'string':'Journal',
			'type':'many2many',
			'relation':'account.analytic.journal',
			'required':True,
		},
		'employee_ids':{
			'string':'Employee',
			'type':'many2many',
			'relation':'res.users',
			'required':True,
		},
	}

	states={
		'init':{
			'actions':[],
			'result':{'type':'form', 'arch':form, 'fields':fields, 'state':[('end', 'Cancel'), ('report', 'Print')]}
		},
		'report':{
			'actions':[],
			'result':{'type':'print', 'report':'account.analytic.profit', 'state':'end'}
		}
	}
wizard_report('account.analytic.profit')
