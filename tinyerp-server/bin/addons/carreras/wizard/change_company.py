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

  Dialeg per a canviar la companyia del usuari actual

"""
import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Canvi d'empresa">
    <separator string="Canvi de l'empresa actual del usuari" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <newline/>
    <field name="newcompany_id" colspan="4"/>
</form>'''


select_fields = {
    'company_id': {
        'string': 'Empresa actual',
        'type': 'many2one',
        'relation': 'res.company',
        'readonly': True
    },
    'newcompany_id': {
        'string': 'Nova empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'required': True
    },
}

class wizard_change_company(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']
        return data['form']


    def _change(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        newcompany = pool.get('res.company').browse(cr,1,data['form']['newcompany_id'])
        
        if newcompany.parent_id and newcompany.parent_id.id!=1:
            pricelist_company_id=newcompany.parent_id.id
        else:
            pricelist_company_id=newcompany.id
        data = {}
        data['company_id']=newcompany.id
        data['pricelist_company_id']=pricelist_company_id
        user = pool.get('res.users').write(cr,uid,[uid],data)
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Canviar empresa') ]}
        },
        'change': {
            'actions': [_change],
            'result': {'type':'state', 'state':'end'}
        }
    }
wizard_change_company('carreras.change_company')

