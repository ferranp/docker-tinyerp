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
  Calcul de tarifes de recubriment 

  A partir del preu del tractament 61 es calculen la resta de recubriments

"""
import time
import wizard
import netsvc
import pooler 

dates_form = '''<?xml version="1.0"?>
<form string="Recàlul de Tarifes de Recubriments">
    <field name="company_id" colspan="4"/>
    <field name="product_id" colspan="4"/>
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'product_id': {'string': 'Recubriment Origen', 'type': 'many2one', 'relation': 'product.product', 'readonly': True},    
}

dates2_form = '''<?xml version="1.0"?>
<form string="Recàlul de Tarifes de Recubriments">
    <label string="Proces finalitzat"/>
</form>'''

dates2_fields = {
}


class wizard_pricelist_rec_compute(wizard.interface):

    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']

        p_obj = pool.get('product.product')
        s = [('default_code','=','61')]
        p_ids = p_obj.search(cr,uid,s,context=context)
        if p_ids:
            data['form']['product_id'] = p_ids[0]
        
        return data['form']

    def _compute_price(self,product_id,increment):
        pass

    def _compute(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        p_obj = pool.get('product.product')
        t_obj = pool.get('pricelist.rec')
        tl_obj = pool.get('pricelist.rec.line')
        # Busco tarifes base
        s = [('product_id','=',data['form']['product_id'])]
        t_ids = t_obj.search(cr,uid,s,context=context)
        
        s = [('id','<>',data['form']['product_id']),
                    ('per_rec','<>','0')]
        p_ids = p_obj.search(cr,uid,s,context=context)
        for prod in p_obj.browse(cr,uid,p_ids,context=context):
            #print prod.name
            increment = prod.per_rec
            # Buscar tarifes que s'incrementen
            for pl in t_obj.browse(cr,uid,t_ids):
                #print pl.name
                s = [('product_id','=',prod.id)]
                s.append(('long','=',pl.long))
                s.append(('piece_id','=',pl.piece_id.id))
                to_change_id = t_obj.search(cr,uid,s,context=context)
                if to_change_id:
                    change = t_obj.browse(cr,uid,to_change_id[0])
                    # esborro linia anterior
                    for lin in change.line_ids:
                        tl_obj.unlink(cr,uid,lin.id)
                    # Creo noves linies
                    for lin in pl.line_ids:
                        new_lin = {
                            'name': lin.name,
                            'pricelist_rec_id': to_change_id[0],
                            'diameter': lin.diameter,
                            'price': (lin.price * ( 1 + ( increment / 100))),
                        }
                        tl_obj.create(cr,uid,new_lin)
        return {}

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('confirm','Calcular Tarifa')]}
        },
        'confirm': {
            'actions': [_compute], 
            'result': {'type':'form', 'arch':dates2_form, 'fields':dates2_fields, 'state':[('end','Tancar')]}
        },
    }


wizard_pricelist_rec_compute('carreras.pricelist_rec.compute')

