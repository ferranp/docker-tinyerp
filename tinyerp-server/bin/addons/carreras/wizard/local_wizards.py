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
  Obre finestres amb les fulles de treballa de la 
  delegacio del usuari

"""
import time
import wizard
import pooler
import tools

class local_wizard(wizard.interface):
    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        s = [('res_model','=','sale.order'),('name','=',self._wiz_values['act'])]
        ids = pool.get('ir.actions.act_window').search(cr,uid,s)
        act = pool.get('ir.actions.act_window').read(cr,uid,ids)
        view_ids = act[0]['view_ids']
        views = act[0]['views']
        
        if act[0]['domain']:
            domain = eval(act[0]['domain'])
        else:
            domain = []
        if act[0]['context']:
            context = eval(act[0]['context'])
        else:
            cntext = {}
        user = pool.get('res.users').browse(cr,uid,uid)
        names = None
        name =  self._wiz_values['default_name']
        if user.groups_id:
            names = [ "'%s'" % x.name for x in user.groups_id]
            if len(names):
                s_names = ",".join(names)
                cr.execute('select id,name from sale_shop where name in (%s)' % s_names)
                shops = cr.fetchall()
                if len(shops) == 1:
                    name = self._wiz_values['name'] % shops[0][1]
                    domain.append(('shop_id','=',shops[0][0]))
                    context['shop_id'] = shops[0][0]
                
        ret= {
            #'domain': domain,
            'name': name,
            'view_type': self._wiz_values['view_type'],
            'view_mode': self._wiz_values['view_mode'],
            'res_model': self._wiz_values['res_model'],
            #'view_ids': view_ids,
            'views': views,
            'context': str(context),
            'domain': str(domain),
            #'action_window_id': self._wiz_values['ir_model_data'],
            'type': 'ir.actions.act_window',
        }
        print ret
        return ret
    states = {
        'init': {
            'actions': [], 
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        },
    }

class wizard_sale_order_local_TR(local_wizard):
    _wiz_values = {
        'default_name' : 'Consulta de Fulls de Ruta de Tractament',
        'name': 'Consulta de Fulls de Ruta de Tractament (%s)', 
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'sale.order',
        'act': 'Consulta de Fulls de Ruta de Tractament',
        }
wizard_sale_order_local_TR('carreras.sale.order.local_TR')

class wizard_sale_order_local_RE(local_wizard):
    _wiz_values = {
        'default_name' : 'Consulta de Fulls de Ruta de Recobriment',
        'name': 'Consulta de Fulls de Ruta de Recobriment (%s)', 
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'sale.order',
        'act': 'Consulta de Fulls de Ruta de Recobriment',
        }
wizard_sale_order_local_RE('carreras.sale.order.local_RE')

class wizard_sale_order_local_quality(local_wizard):
    _wiz_values = {
        'default_name' : 'Entrada de Dades de Qualitat',
        'name': 'Entrada de Dades de Qualitat a %s', 
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'sale.order',
        'act': 'Entrada de Dades de Qualitat',
        }         
wizard_sale_order_local_quality('carreras.sale.order.local_quality')

class wizard_delivery_local(local_wizard):
    _wiz_values = {
        'default_name' : "Consulta i Reimpressió d'Albarans",
        'name': "Consulta i Reimpressió d'Albarans a %s", 
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'sale.order',
        'act': "Consulta i Reimpressió d'Albarans",
        }         
wizard_delivery_local('carreras.delivery.local')

class wizard_delivery_local(local_wizard):
    _wiz_values = {
        'default_name' : "Consulta i Reimpressió d'Albarans Històrics",
        'name': "Consulta i Reimpressió d'Albarans Històrics a %s", 
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'sale.order',
        'act': "Consulta i Reimpressió d'Albarans Històrics",
        }         
wizard_delivery_local('carreras.delivery.histo.local')

