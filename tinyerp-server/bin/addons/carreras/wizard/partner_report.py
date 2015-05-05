# -*- coding: utf-8 -*-
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
"""
  Llistat de Clients/Proveidors  


"""
import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Llistat d'Intervinents">
    <field name="name" colspan="4" />
    <field name="ref"/>
    <newline/>
    <field name="category_id" />
    <label string="(En blanc totes)" />
</form>'''


select_fields = {
    'name': {
        'string': 'El Nom Conté',
        'type': 'char',
    },
    'ref': {
        'string': 'El NIF Conte',
        'type': 'char',
    },
    'category_id': {
        'string': 'Categoria',
        'type': 'many2one',
        'relation': 'res.partner.category',
    },
}

class wizard_partner_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        return data['form']

        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'carreras.partner_report', 'state':'end'}
        }
    }
    
wizard_partner_report('carreras.partner_report')
