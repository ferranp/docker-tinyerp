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
import tools
import ir
import pooler
import time 
from osv import fields,osv
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

"""
  Taula de Representants
"""
class agent(osv.osv):
    _name = "agent.agent"
    _description = "Representants"

    _columns = {
        'name' : fields.char('Nom',size=64,required=True,select="1"),
        'user_id' : fields.many2one('res.users', 'Usuari'),
        'partner_id': fields.many2one('res.partner','Intervinent'),
        'code' : fields.char('Codi',size=10,required=True),
        'city' : fields.char('Ciutat',size=64,required=True),
        'product_ids': fields.one2many('agent.product', 'agent_id', 'Tractaments',select=True),
    }

    _order = "code"

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        agents=[]
        for r in self.read(cr, uid, ids, ['code','name'], context):
            agents.append((r['id'], "[%s] %s" % (r['code'], r['name'])))
        return agents

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, uid, [('name','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('code','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('name',operator,name)]+ args, limit=limit, context=context)
            ids += self.search(cr, uid, [('code',operator,name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, uid, ids, context)
        return result

agent()

class agent_product(osv.osv):
    _name = "agent.product"
    _description = "Percentatges per Tractament i Representant"

    _columns = {
        'product_id' : fields.many2one('product.product', 'Tractament', required=True, domain=[('categ_id','like','Vendes')]),
        'agent_id' : fields.many2one('agent.agent', 'Representant', required=True),
        'comission': fields.float('Comissió', digits=(16, 2), required=True),
    }

    _order = "product_id,agent_id"
    _defaults = {
    }

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        ag_pr=[]
        for r in self.read(cr, uid, ids, ['product','agent'], context):
            ag_pr.append((r['id'], "%s - %s" % (r['product'], r['agent'])))
        return ag_pr

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, uid, [('product','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('agent','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('product',operator,name)]+ args, limit=limit, context=context)
            ids += self.search(cr, uid, [('agent',operator,name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, uid, ids, context)
        return result

agent_product()
