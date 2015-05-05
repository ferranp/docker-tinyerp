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

class purchase_order(osv.osv):
    _name = "purchase.order"
    _inherit = "purchase.order"

    def _default_location(self,cr,uid,*args):
        location = self.pool.get('stock.location').search(cr,uid,[('usage','=','internal')])
        if not location:
            return False
        return location[0]

    def _default_name(self,cr,uid,*args):
        company_id=self.pool.get('res.users').browse(cr, uid, uid).company_id
        if not company_id.purchase_sequence_id:
            return False
        return self.pool.get('ir.sequence').get_id(cr, uid, company_id.purchase_sequence_id.id)

    _columns = {
        'date_reception':fields.date('Data de Recepció'),
        'date_delivery':fields.date('Data de l\'Albarà'),
        'date_term_delivery':fields.date('Plaç d\'Entrega'),
        'form_delivery': fields.char('Forma d\'Enviament', size=64),
        'ports': fields.selection([('P', 'Pagats'), ('D', 'Deguts')],'Ports',required=True),
        'creator' : fields.many2one('res.users', 'Creador', readonly=True),
        'aproved': fields.char('Aprovat per', size=64),
        'destination' : fields.many2one('sale.shop', 'Entrega a'),
    }

    def wkf_confirm_order(self, cr, uid, ids, context={}):
        for po in self.browse(cr, uid, ids):
            if not po.partner_ref or not po.date_delivery or not po.date_reception:
                raise osv.except_osv('No es pot confirmar la comanda !', 
                    "S'han de completar les Dades de Recepció:\n- Albarà\n- Data de l'albarà\n- Data de recepció")
                
        for po in self.browse(cr, uid, ids):
            if self.pool.get('res.partner.event.type').check(cr, uid, 'purchase_open'):
                name='Comanda: %s'+po.name
                self.pool.get('res.partner.event').create(cr, uid, {'name':name, 'partner_id':po.partner_id.id, 'date':time.strftime('%Y-%m-%d %H:%M:%S'), 'user_id':uid, 'partner_type':'retailer', 'probability': 1.0, 'planned_cost':po.amount_untaxed})
        current_name = self.name_get(cr, uid, ids)[0][1]
        for id in ids:
            self.write(cr, uid, [id], {
                'state' : 'confirmed',
                'date_approve' : time.strftime("%Y-%m-%d"),
                'validator' : uid})
        return True

    _defaults = {
        'location_id': _default_location,
        'creator' : lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid).id,
        'invoice_method': lambda *a: 'manual',
        'name': _default_name,
        #'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.order'),
    }

    def _check_partner(self, cr, uid, ids):
        for po in self.browse(cr, uid, ids):
            if not po.partner_id or not po.partner_id.prov_code:
                raise osv.except_osv("Proveïdor incorrecte en la comanda %s" % po.name,
                 "El proveïdor no està definit en aquesta empresa")
                return False
        return True

    _constraints = [
        (_check_partner, "El proveïdor no està definit en aquesta empresa", ['partner_id']),
    ]

    """
    def create(self, cr, uid, vals, context=None):
        if 'pricelist_id' not in vals or not vals['pricelist_id']:
            vals['pricelist_id']=self.pool.get('product.pricelist').search(cr, uid, [('type','=','purchase')])[0]
        r= super(purchase_order, self).create(cr, uid,vals, context=context)
        return r
    """

    def onchange_partner_id(self, cr, uid, ids, part):
        if part:
            partner=self.pool.get('res.partner').browse(cr,uid,part)
            if not partner.prov_code:
                raise osv.except_osv("Proveïdor incorrecte",
                 "El proveïdor no està definit en aquesta empresa")
        vals= super(purchase_order, self).onchange_partner_id(cr, uid, ids, part)
        vals['value']['pricelist_id']=self.pool.get('product.pricelist').search(cr, uid, [('type','=','purchase')])[0]
        return vals

purchase_order()

class purchase_order_line(osv.osv):
    _name = "purchase.order.line"
    _inherit = "purchase.order.line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        cur_obj=self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, line.price_unit * line.product_qty * (1 -  line.discount / 100))
        return res

    """
    def _pricelist(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        pl_obj=self.pool.get('pricelist.supplier')
        res = {}
        for line in self.browse(cr, uid, ids):
            ts=pl_obj.get_current_pricelists(cr,uid,line.product_id.id,line.order_id.partner_id.id)
            if len(ts) == 0:
                res[line.id]="No s'ha trobat cap tarifa"
            elif len(ts) == 1:
                res[line.id]=pl_obj.name_get(cr,uid,[ts[0].id])[0][1][0:64]
            else:
                res[line.id]="S'han trobat %d tarifes" % len(ts)
        return res
    """

    def _pricelist_text(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        pl_obj=self.pool.get('pricelist.supplier')
        res = {}
        for line in self.browse(cr, uid, ids):
            ts=pl_obj.get_current_pricelists(cr,uid,line.product_id.id,line.order_id.partner_id.id)
            if len(ts) == 0:
                res[line.id]="No s'ha trobat cap tarifa"
            elif len(ts) == 1:
                res[line.id]=""
            else:
                res[line.id]="S'han trobat %d tarifes" % len(ts)
        return res

    def _order_partner(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        p_obj=self.pool.get('res.partner')
        res = {}
        for line in self.browse(cr, uid, ids):
            buf=p_obj.name_get(cr,uid,[line.order_id.partner_id.id])[0]
            res[line.id]=len(buf) and buf[1] or ""
        return res

    def _date_order(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id]=line.order_id.date_order
        return res

    def _date_reception(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id]=line.order_id.date_reception
        return res

    def _partner_ref(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id]=line.order_id.partner_ref
        return res

    _columns = {
        'discount': fields.float('Descompte', required=True, digits=(16,2)),
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal'),
        'pricelist_text': fields.function(_pricelist_text, type='char',method=True, string='Tarifa', size=64),
        'pricelist': fields.many2one('pricelist.supplier', 'Tarifa',),
        'partner': fields.function(_order_partner, type='char',method=True, string='Proveïdor', size=64),
        'date_order': fields.function(_date_order, type='date',method=True, string='Data'),
        'partner_ref': fields.function(_partner_ref, type='char',method=True, string='Albarà', size=64),
        'date_reception': fields.function(_date_reception, type='date',method=True, string='Data Recepció'),
    }

    _defaults = {
        'discount': lambda *a: 0.0,
    }

    _order = "order_id desc"

    def product_id_change(self, cr, uid, ids, pricelist, product, qty, uom,
            partner_id, date_order=False):
        if not pricelist:
            raise osv.except_osv('No hi ha Proveïdor !', "S'ha de seleccionar un proveïdor abans d'escollir els productes.")
        ret=super(purchase_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom,partner_id, date_order)
        vals=ret['value']
        
        #buscar tarifa
        pl_obj=self.pool.get('pricelist.supplier')
        ts=pl_obj.get_current_pricelists(cr,uid,product,partner_id)
        if len(ts) == 0:
            vals['pricelist_text']="No s'ha trobat cap tarifa"
            vals['pricelist']=False
            vals['price_unit']=0
        elif len(ts) == 1:
            vals['pricelist_text']=""
            #vals['pricelist']=pl_obj.name_get(cr,uid,[ts[0].id])[0][1][0:64]
            vals['pricelist']=ts[0].id
            vals['price_unit']=ts[0].price
        else:
            vals['pricelist_text']="S'han trobat %d tarifes" % len(ts)
            vals['pricelist']=False
            vals['price_unit']=0
        ret['value']=vals
        return ret

purchase_order_line()
