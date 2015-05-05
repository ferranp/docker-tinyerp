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

  Carrega de Tipus de peces
"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de peces">
    <label string="Carrega de tipus de peces" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

class wizard_load_pricelist_piece(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        f = fbackup()
        i = 0
        for lin in f:
            if lin.startswith('^TTPIEZ("'):
                
                code = lin[13:].strip().strip(')')
                name = f.next().strip()
                if not name:
                    continue
                print code,name
                p = {'name':name,'code':code}
                p_id = pool.get('pricelist.piece').search(cr,uid,[('code','=',code)])
                if p_id:
                    p_id = pool.get('pricelist.piece').write(cr,uid,p_id,p)
                else:    
                    p_id = pool.get('pricelist.piece').create(cr,uid,p)

                i = i +1
                if i > 100:
                    cr.commit()
                    print 'COMMIT'
                    i = 0
        print 'Final'
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        }
    }
    
wizard_load_pricelist_piece('carreras.load_pricelist_piece')

