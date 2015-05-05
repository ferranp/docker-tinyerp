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

# 24.10.2014 Afegir camps a les tarifes de clients.

"""
  Tarifes de Vendes
"""
import tools
import ir
import time
import pooler
from tools import config
from osv import fields,osv

class pricelist_kilo(osv.osv):
    _name = "pricelist.kilo"
    _description='Tarifa per kilos i partida'
    _order = "name"
    _columns = {
        'name': fields.char('Descripció', size=64, required=True,select=True),
        #'partner_id': fields.many2one('res.partner', 'Partner', select="1"),
        'company_id': fields.many2one('res.company', 'Empresa', required=True,select="1"),
        'product_id': fields.many2one('product.product', 'Tractament', required=True, ondelete='cascade', select="1"),
        'product_uom': fields.many2one('product.uom', 'Unitat de mesura', required=True),
        'depth': fields.integer('Profunditat'),
        'minimum': fields.float('Mínim',digits=(16, int(config['price_accuracy']))),
        'apply_minimum': fields.boolean('Aplicar mínim'),
        'line_ids': fields.one2many('pricelist.kilo.line', 'pricelist_kilo_id', 'Detall de la tarifa'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }
    
    def find_price_and_min(self,cr,uid,product,depth,quantity=0,company_id=False):
        if not company_id:
            company_id = self.pool.get('res.users').browse(cr, uid, uid).pricelist_company_id.id
        s = [('product_id','=',product)]
        s.append(('depth','=',depth))
        s.append(('company_id','=',company_id))
        tg = self.search(cr,uid,s)
        price = 0.0
        min = 0.0
        if tg:
            tg = self.browse(cr,uid,tg[0])
            min = tg.apply_minimum and tg.minimum or 0.0
            for l in tg.line_ids:
                #print l.quantity
                if l.quantity > quantity and price==0.0:
                    price = l.price
        return price,min

    def get_product_uom(self,cr,uid,product,depth,company_id=False):
        if not company_id:
            company_id = self.pool.get('res.users').browse(cr, uid, uid).pricelist_company_id.id
        s = [('product_id','=',product)]
        s.append(('depth','=',depth))
        s.append(('company_id','=',company_id))
        tg = self.search(cr,uid,s)
        uom = False
        if not tg:
            return False
        tg = self.browse(cr,uid,tg[0])
        return tg.product_uom.id

pricelist_kilo()

class pricelist_kilo_line(osv.osv):
    _name = "pricelist.kilo.line"
    _description='Detall de la tarifa per kilos'
    _order = "quantity"
    _columns = {
        'name': fields.char('Descripció', size=64, select=True),
        'pricelist_kilo_id': fields.many2one('pricelist.kilo', 'Tarifa', required=True, ondelete='cascade'),
        'quantity': fields.float('Quantitat fins a',digits=(16,0),required=True),
        'price': fields.float('Preu',digits=(16,int(config['price_accuracy'])),required=True),
    }
pricelist_kilo_line()

class pricelist_piece(osv.osv):
    _name = "pricelist.piece"
    _description='tipus de peces'
    _order = "code"
    _columns = {
        'name': fields.char('Nom', size=64, required=True,select=True),
        'code': fields.char('Codi', size=16, required=True,select=True),
    }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        if not self.pool.get('res.users').has_groups(cr,uid,uid,['Producció']):
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        ids=self.pool.get('ir.ui.view').search(cr,uid,[('name','=','pricelist.piece.tree.prod')])
        if not ids:
            return {}
        return super(osv.osv, self).fields_view_get(cr, uid, ids[0],view_type,context,toolbar)
pricelist_piece()

class pricelist_rec(osv.osv):
    _name = "pricelist.rec"
    _description='Tarifa per recubriments'
    _order = "name"
    _columns = {
        'name': fields.char('Descripció', size=64, required=True,select=True),
        'company_id': fields.many2one('res.company', 'Empresa', required=True,select="1"),
        'product_id': fields.many2one('product.product', 'Tractament', required=True, ondelete='cascade', select="1"),
        'piece_id': fields.many2one('pricelist.piece', 'Peça', required=True,select="1"),
        'long': fields.float('Longitud'),
        'minimum': fields.float('Mínim',digits=(16,int(config['price_accuracy']))),
        'apply_minimum': fields.boolean('Aplicar mínim'),
        'line_ids': fields.one2many('pricelist.rec.line', 'pricelist_rec_id', 'Detall de la tarifa'),
        'product_uom': fields.many2one('product.uom', 'Unitat de mesura', required=True),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }

    def find_price_and_min(self,cr,uid,product,length,diameter,piece_id,company_id=False):
        if not company_id:
            company_id = self.pool.get('res.users').browse(cr, uid, uid).pricelist_company_id.id
        s = [('product_id','=',product)]
        s.append(('long','>=',length))
        s.append(('company_id','=',company_id))
        s.append(('piece_id','=',piece_id))
        
        tg = self.search(cr,uid,s,order='long')
        price = 0.0
        min = 0.0
        if tg:
            tg = self.browse(cr,uid,tg[0])
            min = tg.apply_minimum and tg.minimum or 0.0
            for l in tg.line_ids:
                if l.diameter >= diameter and price==0.0:
                    price = l.price
        return price,min

pricelist_rec()

class pricelist_rec_line(osv.osv):
    _name = "pricelist.rec.line"
    _description='Detall de la tarifa per recubriments'
    _order = "diameter"
    _columns = {
        'name': fields.char('Descripció', size=64, select=True),
        'pricelist_rec_id': fields.many2one('pricelist.rec', 'Tarifa', required=True, ondelete='cascade'),
        'diameter': fields.float('Diametre',digits=(16,0),required=True),
        'price': fields.float('Preu',digits=(16,int(config['price_accuracy'])),required=True),
    }
pricelist_rec_line()

class pricelist_partner(osv.osv):
    _name = "pricelist.partner"
    _description='Tarifa per Client'
    _order = "name"

    def _customer(self, cr, uid, ids, field_name, arg, context={}):
        ps = self.browse(cr,uid,ids,context=context)
        res = {}
        for p in ps:
           res[p.id] = p.partner_id and p.partner_id.code or ''
        return res

    def _customer_search(self, cr, uid, obj, name, args):
        if not len(args):
            return []
        for arg in args:
            if arg[0] == 'customer' and arg[1] == 'ilike':
                query=  "SELECT p.id FROM pricelist_partner p, res_partner r, res_partner_customer c " +\
                        "WHERE p.partner_id = r.id AND r.id = c.partner_id AND c.name ILIKE '%s%%'" % arg[2]
        cr.execute(query)
        res = cr.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'name': fields.char('Descripció', size=64, required=True,select=True),
        'customer' : fields.function(_customer,string='Codi Client',type='char',method=True,select=True,fnct_search=_customer_search),
        'partner_id': fields.many2one('res.partner', 'Client',select="1"),
        'company_id': fields.many2one('res.company', 'Empresa', required=True,select="1"),
        'product_id': fields.many2one('product.product', 'Tractament', required=True, ondelete='cascade', select="1"),
        'minimum': fields.float('Mínim',digits=(16, int(config['price_accuracy']))),
        'apply_minimum': fields.boolean('Aplicar mínim'),
        'price': fields.float('Preu',digits=(16,int(config['price_accuracy'])),required=True),
        'product_uom': fields.many2one('product.uom', 'Unitat de mesura', required=True),
        'profundity': fields.integer('Profunditat'),
        'date_start':fields.date('Data d\'Inici'),
        'date_end':fields.date('Data Final'),
        'offer': fields.char('Oferta', size=20),
        'date_issued':fields.date('Data Emesa'),
        'authorized': fields.char('Autoritzada', size=20),
        'section': fields.char('Secció', size=20),
        'note': fields.text('Notes'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        if not self.pool.get('res.users').has_groups(cr,uid,uid,['Producció']):
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        if 'active_id' in context:
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        ids=self.pool.get('ir.ui.view').search(cr,uid,[('name','=','pricelist.partner.tree.prod')])
        if not ids:
            return {}
        return super(osv.osv, self).fields_view_get(cr, uid, ids[0],view_type,context,toolbar)

pricelist_partner()

"""
  Tarifes de Compres
"""
class pricelist_supplier(osv.osv):
    _name = "pricelist.supplier"
    _description='Tarifes de Proveïdors'
    _order = "name,product_id,partner_id"

    def _supplier(self, cr, uid, ids, field_name, arg, context={}):
        ps = self.browse(cr,uid,ids,context=context)
        res = {}
        for p in ps:
            res[p.id] = p.partner_id.prov_code or ''
        return res

    def _supplier_search(self, cr, uid, obj, name, args):
        if not len(args):
            return []
        for arg in args:
            if arg[0] == 'supplier' and arg[1] == 'ilike':
                query=  "SELECT p.id FROM pricelist_supplier p, res_partner r, res_partner_supplier s " +\
                        "WHERE p.partner_id = r.id AND r.id = s.partner_id AND s.name ILIKE '%s%%'" % arg[2]
        cr.execute(query)
        res = cr.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'name': fields.char('Descripció', size=64, select=True),
        'product_id': fields.many2one('product.product', 'Producte', required=True, ondelete='cascade', select="1"),
        'partner_id': fields.many2one('res.partner', 'Proveïdor', required=True, select="1"),
        'company_id': fields.many2one('res.company', 'Empresa', required=True, select="1"),
        'supplier' : fields.function(_supplier,string='Codi Proveïdor',type='char',method=True,select=True,fnct_search=_supplier_search),
        'price': fields.float('Preu',digits=(16,int(config['price_accuracy'])),required=True),
        'date_start':fields.date('Data d\'Inici',required=True),
        'date_end':fields.date('Data Final'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }

    def get_current_pricelists(self, cr, uid, product_id, partner_id):
        curr_time=time.strftime('%Y-%m-%d')
        user = self.pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        company_id = user['company_id'][0]
        s=[]
        s.append(('product_id','=',product_id))
        s.append(('partner_id','=',partner_id))
        s.append(('company_id','=',company_id))
        pl_ids=self.search(cr,uid,s)
        ret=[]
        for t in self.browse(cr,uid,pl_ids):
            if not t.date_end or t.date_end >= curr_time:
                ret.append(t)
        return ret

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        pl_pr=[]
        for r in self.read(cr, uid, ids, ['name','product_id','partner_id'], context):
            if r['name']:
                pl_pr.append((r['id'], "%s - %s - %s" % (r['name'],r['product_id'][1], r['partner_id'][1])))
            else:
                pl_pr.append((r['id'], "%s - %s" % (r['product_id'][1], r['partner_id'][1])))
        return pl_pr

    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        ids = self.search(cr, uid, [('name','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('partner_id','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('product_id','=',name)]+ args, limit=limit, context=context)
        if not len(ids):
            ids = self.search(cr, uid, [('partner_id',operator,name)]+ args, limit=limit, context=context)
            ids += self.search(cr, uid, [('product_id',operator,name)]+ args, limit=limit, context=context)
        result = self.name_get(cr, uid, ids, context)
        return result

pricelist_supplier()
