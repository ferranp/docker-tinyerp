# -*- coding: iso-8859-1 -*-
##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

price_form = '''<?xml version="1.0"?>
<form string="Paid ?">
	<field name="number"/>
</form>'''

price_fields = {
	'number': {'string':'Number of products to produce', 'type':'integer', 'required':True},
}

class wizard_price(wizard.interface):
	states = {
		'init': {
			'actions': [], 
			'result': {'type':'form', 'arch':price_form, 'fields':price_fields, 'state':[('end','Cancel'),('price','Print product price') ]}
		},
		'price': {
			'actions': [],
			'result': {'type':'print', 'report':'product.price', 'state':'end'}
		}
	}
wizard_price('product_price')


