# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
"""
  Tarifes de preus especifiques

"""
import tools
import ir
import pooler
from tools import config
from osv import fields,osv


class product_family(osv.osv):
    _name = 'product.family'
    _description = "Famílies de Productes"
    _order = 'name'

    _columns = {
        'name': fields.char('Codi',size=64),
        'description': fields.char('Descripció',size=64),
    }

product_family()

class product_department(osv.osv):
    _name = 'product.department'
    _description = "Departaments"
    _order = 'name'

    _columns = {
        'name': fields.char('Codi',size=64),
        'description': fields.char('Descripció',size=64),
    }

product_department()

class product_uom(osv.osv):
    _name = 'product.uom'
    _inherit = "product.uom"

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        if not self.pool.get('res.users').has_groups(cr,uid,uid,['Producció']):
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        ids=self.pool.get('ir.ui.view').search(cr,uid,[('name','=','carreras.product.uom.tree.prod')])
        if not ids:
            return {}
        return super(osv.osv, self).fields_view_get(cr, uid, ids[0],view_type,context,toolbar)

product_uom()


class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"

    _columns = {
        'hard_metal': fields.float('% Rec. Metall Dur',digits=(6,2)),
        'default_agent_id' : fields.many2one('agent.agent', 'Representant per defecte'),
        'default_comission': fields.float('Comissió', digits=(16, 2),),
        'agent_ids' : fields.one2many('agent.product', 'product_id','Representants'),
        'family_id' : fields.many2one('product.family', 'Família'),
        'department_id' : fields.many2one('product.department', 'Departament'),
        'per_rec': fields.float('% Recàlcul',digits=(6,2)),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        if not self.pool.get('res.users').has_groups(cr,uid,uid,['Producció']):
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        ids=self.pool.get('ir.ui.view').search(cr,uid,[('name','=','carreras.product.product.tree.prod')])
        if not ids:
            return {}
        return super(osv.osv, self).fields_view_get(cr, uid, ids[0],view_type,context,toolbar)

product_product()

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"

    def _default_categ(self,cr,uid,context,*args):
        if 'categ_id' in context and context['categ_id'] == 'Compres':
            categ = self.pool.get('product.category').search(cr, uid, [('name','=','Compres')])
        else:
            categ = self.pool.get('product.category').search(cr, uid, [('name','=','Vendes')])
        if not categ:
            return False
        return categ[0]

    _defaults = {
        'categ_id': _default_categ,
        'type': lambda *a: 'service',
    }
product_template()
