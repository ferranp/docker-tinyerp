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
# 14.06.2010 En alta de fulls de ruta VA (Varis) assignar el tipus d'impost
#            marcat com a "Defecte"
# 02.07.2010 Agafar el percentatge "Defecte" al aplicar el mínim
# 24.10.2014 Validar que la tarifa del client sigui vigent.

"""
  Ordres de venta
"""
import time
import netsvc
from osv import fields, osv
#import memcached as osv
from tools.misc import currency
from tools import config

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime


logger = netsvc.Logger()

class sale_shop(osv.osv):
    _name = "sale.shop"
    _inherit = "sale.shop"

    _columns = {
        'sequence_id': fields.many2one('ir.sequence', "Numerador d'Albarans",
                help="Numerador per als albarans d'aquesta delegació", required=False),
        'quality_charge': fields.many2one('res.users', "Responsable de Qualitat"),
        'address': fields.many2one('res.partner.address', "Adreça"),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        if not self.pool.get('res.users').has_groups(cr,uid,uid,['Producció']):
            return super(osv.osv, self).fields_view_get(cr, uid, view_id,view_type,context,toolbar)
        return {}

sale_shop()

class sale_order(osv.osv):
    _name = "sale.order"
    _inherit = "sale.order"
    _order = 'date_delivery desc, delivery desc, date_order desc, name desc'

    def _default_shop(self,cr,uid,*args):
        """ 
           Valor per defecte de tenda/delegacio segons grups del 
           usuari
        """
        shop_id = False
        user = self.pool.get('res.users').browse(cr,uid,uid)
        for g in user.groups_id:
            ids = self.pool.get('sale.shop').search(cr,uid,[('name','=',g.name)])
            if ids and shop_id:
                return False
            if ids:
                shop_id = ids[0]
            
        return shop_id

    def _get_shop_id(self,cr,uid,ids,field_name,arg,context):
        shop_id= self.pool.get('res.users').read(cr,uid,[uid],['shop_id'])
        res=dict.fromkeys(ids,shop_id)
        return res

    def _product(self, cr, uid, ids, field_name, arg, context={}):
        so = self.browse(cr,uid,ids,context=context)
        res = {}
        for o in so:
            res[o.id] = o.order_line and o.order_line[0].name or ''
        return res

    def _product_search(self, cr, uid, obj, name, args):
        if not len(args):
            return []
        for arg in args:
            if arg[0] == 'product' and arg[1] == 'ilike':
                s=[('name','ilike',arg[2])]
                ids1=self.pool.get('product.product').search(cr, uid,s)
                s=[('default_code','=',arg[2])]
                ids2=self.pool.get('product.product').search(cr, uid,s)
                product_set = ",".join(map(str, ids1+ids2))
                query=  "SELECT so.id FROM sale_order so, sale_order_line sol, product_product p " +\
                        "WHERE so.id = sol.order_id AND p.id = sol.product_id AND " +\
                        "p.id in (%s)" % product_set
        cr.execute(query)
        res = cr.fetchall()
        if not res:
            return [('id', '=', 0)]
        return [('id', 'in', [x[0] for x in res])]

    def _amount_minimum(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for order in self.browse(cr, uid, ids):
            res[order.id] = 0.0
            for line in order.order_line:
                if line.price_min > 0.0 and line.price_min > res[order.id]:
                    res[order.id] = line.price_min
        return res

    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context):
        res = self._amount_lines(cr, uid, ids, field_name, arg, context)
        res_min = self._amount_minimum(cr, uid, ids, field_name, arg, context)
        for id,min in res_min.iteritems():
            if min > res[id] and res[id] > 0:
                res[id]=min
        return res

    def _amount_lines(self, cr, uid, ids, field_name, arg, context):
        return super(sale_order, self)._amount_untaxed(cr, uid, ids, field_name, arg, context)

    def _amount_tax(self, cr, uid, ids, field_name, arg, context):
        res = {}
        cur_obj=self.pool.get('res.currency')
        untaxed=self._amount_untaxed(cr, uid, ids, field_name, arg, context)
        for order in self.browse(cr, uid, ids):
            cur=order.pricelist_id.currency_id
            if not order.order_line[0].tax_id:
                raise osv.except_osv(
                    "Atenció: El full de ruta %s no és correcte" % order.name,
                    "No té els impostos ben assignats.\n"+
                    "Per corregir l'error s'ha de cancel·lar i \n"+
                    "tornar a activar des de l'empresa TT." )
            perc=order.order_line[0].tax_id[0].amount or 0.0
            #perc=order.order_line[0].tax_id and order.order_line[0].tax_id[0].amount or 0.0
            res[order.id]=cur_obj.round(cr, uid, cur, untaxed[order.id]*perc)
        return res

    _columns = {
        'name': fields.char('Full de Ruta', size=64, required=True, select=True, readonly=True, 
                states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Companyia', required=True, select=True, 
                states={'manual':[('readonly',True)],
                        'progress':[('readonly',True)],
                        'invoice_except':[('readonly',True)],
                        'done':[('readonly',True)],
                        'cancel':[('readonly',True)]}),
        'customer_id': fields.many2one('res.partner.customer', 'Codi de client',select=True,
                states={'manual':[('readonly',True)],
                        'progress':[('readonly',True)],
                        'invoice_except':[('readonly',True)],
                        'done':[('readonly',True)],
                        'cancel':[('readonly',True)]}),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=True, select=True, 
                states={'manual':[('readonly',True)],
                        'progress':[('readonly',True)],
                        'invoice_except':[('readonly',True)],
                        'done':[('readonly',True)],
                        'cancel':[('readonly',True)]}),
        'order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines',
                states={'manual':[('readonly',True)],
                        'progress':[('readonly',True)],
                        'invoice_except':[('readonly',True)],
                        'done':[('readonly',True)],
                        'cancel':[('readonly',True)]}),

        'delivery': fields.char('Albarà', size=20, readonly=True, select=True),
        'date_delivery':fields.date('Data de l\'Albarà', select=True,
                states={'progress':[('readonly',True)],
                        'invoice_except':[('readonly',True)],
                        'done':[('readonly',True)],
                        'cancel':[('readonly',True)]}),
        #'date_delivery':fields.date('Data de l\'Albarà', select=True),
        #'delivery_note': fields.text('Observacions de l\'Albarà', readonly=True, states={'draft':[('readonly',False)]}),
        'delivery_note': fields.text('Observacions de l\'Albarà'),

        'partner_invoice_id':fields.many2one('res.partner.address', 'Invoice Address', required=True),
        'partner_order_id':fields.many2one('res.partner.address', 'Ordering Contact', required=True, help="The name and address of the contact that requested the order or quotation."),
        'partner_shipping_id':fields.many2one('res.partner.address', 'Shipping Address', required=True),

        # tractament
        'line_type': fields.selection([('TR','Tractament'),('RE','Recobriment'),('VA','Varis')], 'Tipus de linea', required=True,readonly=True,select=True, states={'draft':[('readonly',False)]}),
        #'product': fields.many2one('product.product','Tractament'),
        #'depth': fields.integer('Profunditat'),

        # totals
        'amount_lines': fields.function(_amount_lines, method=True, string='Suma de les Línies', digits=(16, 2)),
        'amount_minimum': fields.function(_amount_minimum, method=True, string='Import Mínim', digits=(16, 2)),
        'amount_untaxed': fields.function(_amount_untaxed, method=True, string='Import Net', digits=(16, 2)),
        'amount_tax': fields.function(_amount_tax, method=True, string='Taxes'),

        # duresa sol·licitada
        'min_req_hardness': fields.char('Mínim', size=10),
        'max_req_hardness': fields.char('Màxim', size=10),
        # profunditat sol·licitada
        'max_req_depth': fields.char('Mínim', size=10),
        'min_req_depth': fields.char('Màxim', size=10),
        # desc del material
        'stuff_desc': fields.char('Material', size=60),
        'quality_note': fields.text('Observacions de Qualitat'),

        # --- Dades de qualitat ---
        # duresa obtinguda
        'min_obt_hardness': fields.char('Mínim', size=10, readonly=True, states={'draft':[('readonly',False)]}),
        'max_obt_hardness': fields.char('Màxim', size=10, readonly=True, states={'draft':[('readonly',False)]}),
        # profunditat obtinguda
        'max_obt_depth': fields.char('Mínim', size=10, readonly=True, states={'draft':[('readonly',False)]}),
        'min_obt_depth': fields.char('Màxim', size=10, readonly=True, states={'draft':[('readonly',False)]}),

        # descompte comptat
        'cash_discount': fields.float('Descompte Comptat', digits=(16, int(config['price_accuracy']))),
        
        # descompte comptat
        'block': fields.boolean('Bloquejar'),

        # representant
        'agent_id' : fields.many2one('agent.agent', 'Representant'),
        'comission': fields.float('Comissió', digits=(16, 2)),
        'amount_comission': fields.float('Import', digits=(16, 2)),
        'date_comission':fields.date('Liquidació', readonly=True),
        'block_comission': fields.boolean('Bloqueig'),
        'note_comission': fields.text('Observacions'),

        # tractament de la primera linia
        'product' : fields.function(_product,string='Tractament',type='char',method=True,fnct_search=_product_search),
    }
    _defaults = {
        #'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'sale.order'),
        'name': lambda *a: '',
        'shop_id':_default_shop,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
        'line_type': lambda *a: 'VA',
        'cash_discount': lambda *a: 0.0,
        'block': lambda *a: False,
        'shipped': lambda *a: True,
        'comission': lambda *a: 0.0,
        'amount_comission': lambda *a: 0.0,
        'block_comission': lambda *a: False,
    }

    def _check_company(self, cr, uid, ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for so in self.browse(cr, uid, ids):
            if so.company_id.child_ids:
                logger.notifyChannel("info", netsvc.LOG_INFO,"check company")
                raise osv.except_osv(
                    "No es pot crear el Full de Ruta",
                    "L'empresa %s no pot tenir Fulls de Ruta" % so.company_id.name)
                return False
        return True
    
    def _check_lines(self, cr, uid, ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for so in self.browse(cr, uid, ids):
            if so.state not in ['draft','manual']:
                continue
            length = len(so.order_line)
            if length == 0:
                logger.notifyChannel("info", netsvc.LOG_INFO,"check lines")
                raise osv.except_osv(
                    "No es pot crear el Full de Ruta",
                    "El Full de Ruta no té línies")
                return False
            if length != 1 and so.line_type == "TR":
                logger.notifyChannel("info", netsvc.LOG_INFO,"check lines")
                raise osv.except_osv(
                    "No es pot crear el Full de Ruta",
                    "El Full de Ruta té més d'una línia")
                return False
        return True

    def _check_name(self, cr, uid, ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for so in self.browse(cr, uid, ids):
            if so.state not in ['draft','manual']:
                continue
            so_ids=self.search(cr, uid,[('name','=',so.name),('company_id','=',so.company_id.id)])
            if len(so_ids) > 1:
                logger.notifyChannel("info", netsvc.LOG_INFO,"check name")
                raise osv.except_osv(
                    "No es pot crear el Full de Ruta",
                    "Existeix un Full de Ruta amb número %s a l'empresa %s" % 
                        (so.name,so.company_id.name)
                    )
                return False
        return True

    def _check_risc(self, cr, uid, ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        curr_ts= time.strftime('%Y-%m-%d %H:%M:%S')
        for so in self.browse(cr, uid, ids):
            if so.state not in ['draft']:
                continue
            if not so.partner_id.credit_limit:
                continue
            if so.partner_id.block_ts and so.partner_id.block_ts > curr_ts:
                continue
            if so.customer_id.name[1:4]=="000":
                continue
            if so.partner_id.risk <= so.partner_id.credit_limit:
                continue 
            name=so and so.partner_id and so.partner_id.name or ""
            company=so and so.company_id and so.company_id.name or " "
            logger.notifyChannel("info", netsvc.LOG_INFO,"check risk")
            raise osv.except_osv(
                "No es pot realitzar la operació",
                "El client %s supera el crèdit permès a %s" % 
                    (name,company)
                )
            return False
        return True

    def _check_msg(self,cr,uid,ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        #print self.pool.get('res.users').browse(cr, uid, uid).login
        curr_ts= time.strftime('%Y-%m-%d %H:%M:%S')
        for so in self.browse(cr, uid, ids):
            if so.state not in ['draft','manual']:
                continue
            if not so.partner_id.message:
                continue
            if so.partner_id.block_ts and so.partner_id.block_ts > curr_ts:
                continue
            if not so.partner_id.message.block:
                continue
            logger.notifyChannel("info", netsvc.LOG_INFO,"check msg")
            raise osv.except_osv(
                    "No es pot crear el Full de Ruta",
                    "Client bloquejat: %s" % so.partner_id.message.name)
            return False
        return True

    def _check_address(self,cr,uid,ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for so in self.browse(cr, uid, ids):
            if (so.partner_order_id and so.partner_order_id not in so.partner_id.address) or \
               (so.partner_invoice_id and so.partner_invoice_id not in so.partner_id.address) or \
               (so.partner_shipping_id and so.partner_shipping_id not in so.partner_id.address):
                raise osv.except_osv(
                    "El client %s no es correspon amb l'adreça assignada" % (so.partner_id.name),
                    "No es pot canviar el client sense canviar l'adreça")
                return False
        return True

    def _check_shop(self,cr,uid,ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for so in self.browse(cr, uid, ids):
            if so.state not in ['draft','manual']:
                continue
            if self.pool.get('res.users').has_groups(cr,uid,uid,[so.shop_id.name]):
                continue
            user=self.pool.get('res.users').browse(cr,uid,uid)
            logger.notifyChannel("info", netsvc.LOG_INFO,"check shop")
            raise osv.except_osv(
                "No es pot crear el Full de Ruta",
                "L'usuari %s no pot entrar Fulls de Ruta del centre %s" % 
                            (user.name,so.shop_id.name)
                )
            return False
        return True

    def _complete_order(self,cr,uid,ids):
        sol_obj=self.pool.get('sale.order.line')
        sol_ids=sol_obj.search(cr,uid,[('order_id','in',ids)])
        sol_obj._complete_order_line(cr,uid,sol_ids)
        return True

    _constraints = [
        (_check_address, "El client no es correspon amb l'adreça assignada", ['partner_id']),
        (_check_company, "No es poden fer fulles de treball a aquesta empresa", ['company_id']),
        (_check_name, "Full de Ruta duplicat", ['name']),
        (_check_lines, "Numero de linies de tractament incorrecte", ['order_line']),
        (_check_risc, "Crèdit superat", ['partner_id','create_date','write_date']),
        (_check_msg, "Client bloquejat", ['partner_id']),
        (_check_shop, "Centre de treball incorrecte", ['shop_id']),
        (_complete_order, "Error al completar el registre", ['customer_id']),
    ]

    # el full de ruta ha de ser unic PER EMPRESA
    _sql_constraints = [
        ('code_uniq', 'unique (name,company_id)', 'El Full de Ruta ha de ser únic !')
        ]    

    def check_risc(self,cr,uid,partner,company_id=False):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return
        if not partner.credit_limit:
            return
        if partner.block_ts and partner.block_ts > time.strftime('%Y-%m-%d %H:%M:%S'):
            return
        if not company_id:
            company_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        p=self.pool.get('res.partner').browse(cr,uid,partner.id,context={'company_id':company_id})
        #print p.risk,p.credit_limit
        if p.risk <= p.credit_limit:
            return
        
        raise osv.except_osv(
                "Credit Superat",
                "El client supera el crèdit permès")
                #"Límit de crèdit\t%7.2f\n" +
                #"Risc acumulat\t%7.2f") % (int(partner.credit_limit),int(risc)))
        return

    def check_msg(self,cr,uid,partner):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return
        if not partner.message:
            return
        if partner.block_ts and partner.block_ts > time.strftime('%Y-%m-%d %H:%M:%S'):
            return
        if not partner.message.block:
            raise osv.except_osv(
                "Informació Client",partner.message.name
                )
        raise osv.except_osv(
                "Client bloquejat",partner.message.name
                )
        return

    """ Validar que el full de ruta no estigui duplicat """
    def onchange_name(self, cr, uid, ids, name):
        if not name:
            return {}
        so_ids=self.search(cr, uid,[('name','=',name)])
        if len(so_ids) == 0 or so_ids == ids:
            return {}
        raise osv.except_osv(
            "Full de Ruta duplicat",
            "Existeix un altre full de ruta amb la mateixa referència")
        return {}

    """ Al triar un client, es canvia el partner i l'empresa """
    def onchange_customer_id(self, cr, uid, ids, customer, partner, shop_id):
        #print "customer"
        if not customer:
            return {}
        vals={}
        cust = self.pool.get('res.partner.customer').browse(cr,uid,customer)
        if not partner:
            if cust.name[1:4] != "000":
                self.check_msg(cr,uid,cust.partner_id)
                self.check_risc(cr,uid,cust.partner_id,cust.company_id.id)
                vals= super(sale_order, self).onchange_partner_id(cr, uid, ids, partner)['value']
                vals['partner_id']= cust.partner_id.id
            vals['company_id']= cust.company_id.id
            return {'value':vals}

        part= self.pool.get('res.partner').browse(cr,uid,partner)
        customers = part.customer_ids
        ncustomers=len(customers)

        if cust in customers:
            #self.check_msg(cr,uid,part)
            #self.check_risc(cr,uid,part,cust.company_id.id)
            vals['company_id']= cust.company_id.id
            return {'value':vals}

        if cust.name[1:4] != "000":
            self.check_msg(cr,uid,cust.partner_id)
            self.check_risc(cr,uid,cust.partner_id,cust.company_id.id)
            vals= super(sale_order, self).onchange_partner_id(cr, uid, ids, cust.partner_id.id)['value']
            #vals= self.onchange_partner_id(cr, uid, ids, customer, cust.partner_id.id, shop_id)['value']
            vals['partner_id'] = cust.partner_id.id
            vals['company_id'] = cust.company_id.id
            return {'value':vals}
        
        #if ncustomers == 0:
        #    vals['company_id']= cust.company_id.id
        #    return {'value':vals}

        #self.check_msg(cr,uid,part)
        vals['partner_id'] = partner
        vals['company_id'] = cust.company_id.id
        return {'value':vals}

    def onchange_partner_id(self, cr, uid, ids, customer, partner, shop_id):
        #print "partner"
        vals= super(sale_order, self).onchange_partner_id(cr, uid, ids, partner)['value']
        if not partner:
            return {'value':vals}

        part= self.pool.get('res.partner').browse(cr,uid,partner)
        self.check_msg(cr,uid,part)

        customers = part.customer_ids
        ncustomers= len(customers)
        if customer:
            cust = self.pool.get('res.partner.customer').browse(cr,uid,customer)

        if ncustomers:
            #self.check_msg(cr,uid,part)
            if customer and cust in customers:
                #pass
                self.check_risc(cr,uid,part,cust.company_id.id)
            else:
                self.check_risc(cr,uid,part,customers[0].company_id.id)
                vals['customer_id']= customers[0].id
                vals['company_id']= customers[0].company_id.id
            return {'value':vals}

        if not shop_id:
            vals['partner_id']=False
            return {'value':vals}

        shop=self.pool.get('sale.shop').browse(cr,uid,shop_id)
        codes={"Sabadell":"1000","Rubí":"1000","Inducció":"1000","Manresa":"3000","Barcelona":"5000","Hospitalet":"9000"}
        if shop.name not in codes.keys():
            vals['partner_id']= False
            return {'value':vals}

        ids=self.pool.get('res.partner.customer').search(cr,uid,[('name','=',codes[shop.name])])
        if not ids:
            u=self.pool.get('res.users').browse(cr, uid, uid)
            raise osv.except_osv("No es troba el número de comptat",
             "El Centre de Treball %s no pertany a l'empresa %s" % (shop.name,u.company_id.name))
        cust = self.pool.get('res.partner.customer').browse(cr,uid,ids[0])
        vals['customer_id']=cust.id
        vals['company_id']= cust.company_id.id
        return {'value':vals}

    """ Els fulls de ruta sempre estan en estat 'draft' i els albarans en 'manual' """
    def action_wait(self, cr, uid, ids, *args):
        login=self.pool.get('res.users').browse(cr, uid, uid).login
        event_p = self.pool.get('res.partner.event.type').check(cr, uid, 'sale_open')
        event_obj = self.pool.get('res.partner.event')
        for order in self.browse(cr, uid, ids):
            self.check_msg(cr,uid,order.partner_id)
            if order.customer_id.name[1:4]!="000":
                self.check_risc(cr,uid,order.partner_id,order.company_id.id)
            vals={}
            if order.delivery:
                so_ids=self.search(cr, uid,[('delivery','=',order.delivery)])
                if len(so_ids) > 1:
                    logger.notifyChannel("info", netsvc.LOG_INFO,"l'albara ja existeix")
                    raise osv.except_osv("No es pot generar l'albarà",
                                         "El codi d'albarà ja existeix")
                vals['delivery']=order.delivery
            else:
                vals['delivery']=self.pool.get('ir.sequence').get_id(cr, uid, order.shop_id.sequence_id.id)
                so_ids=self.search(cr, uid,[('delivery','=',vals['delivery'])])
                if len(so_ids) > 0:
                    logger.notifyChannel("info", netsvc.LOG_INFO,"comptador incorrecte")
                    raise osv.except_osv("No es pot generar l'albarà",
                                         "El comptador és incorrecte. S'ha de modificar")
            if not order.date_delivery and order.state == "draft" and login != 'batch' and uid != 1:
                vals['date_delivery']=time.strftime('%Y-%m-%d')
            
            """
            if (order.order_policy == 'manual') and (not order.invoice_ids):
                vals['state']='manual'
            else:
                vals['state']='progress'
            """
            vals['state']='manual'
            if order.order_policy != 'manual':
                vals['state']='progress'
            for inv in order.invoice_ids:
                if inv.state != 'cancel':
                    vals['state']='progress'
            
            self.write(cr,uid,[order.id],vals)
            if event_p and login!='batch' and uid !=1:
                event_obj.create(cr, uid, {'name': 'Albarà: '+ vals['delivery'],\
                        'partner_id': order.partner_id.id,\
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),\
                        'user_id': (order.user_id and order.user_id.id) or uid,\
                        'partner_type': 'customer', 'probability': 1.0,\
                        'planned_revenue': order.amount_untaxed})
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in order.order_line])
        return 

    """ Les factures han de tenir la mateixa empresa que la Sale Order """
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['draft','confirmed','done']):
        # abas de començar miro si totes les SO son de la mateixa empresa
        #if self.pool.get('res.users').browse(cr, uid, uid).login == 'batch':
        #    self.write(cr, uid, ids, {'state' : 'progress'})
        #    return {}
        company_id = False
        amount_untaxed = False
        for o in self.browse(cr,uid,ids):
            # Nomes els usuaris del grup Direcció poden facturar albarans de crèdit
            if o.customer_id.name[1:4] != "000":
                if not self.pool.get("res.users").has_groups(cr,uid,uid,["Direcció","Administració"]):
                    raise osv.except_osv(
                        "Procés cancel·lat",
                        "L'usuari no té permís per facturar albarans de crèdit")
            if not company_id:
                company_id = o.company_id.id
            elif company_id != o.company_id.id:
                raise osv.except_osv(
                    "Procés cancel·lat",
                    'Els albarans seleccionats no son tots de la mateixa empresa.')
            if not amount_untaxed:
                amount_untaxed = o.amount_untaxed
            elif amount_untaxed > 0 and o.amount_untaxed < 0 or \
                 amount_untaxed < 0 and o.amount_untaxed > 0 :
                raise osv.except_osv(
                    "Procés cancel·lat",
                    'No es poden generar factures i abonaments alhora.')
            #print o.state
            if o.state not in ['draft','manual','progress']:
                raise osv.except_osv(
                    "Procés cancel·lat",
                    'Albarà ja facturat.')
            # Només es poden facturar fulls de ruta sense num.d'albara
            #  si són varis (VA) amb import negatiu (abonaments)
            if o.delivery:
                continue
            if o.amount_untaxed < 0 and o.line_type=='VA':
                continue
            raise osv.except_osv(
                "Procés cancel·lat",
                "Encara no s'ha generat l'albarà del full de ruta %s." % o.name)

        user_comp_ids = self.pool.get('res.company')._get_child_ids(cr, uid, uid)
        if company_id not in user_comp_ids:
            raise osv.except_osv(
                "Procés cancel·lat",
                "L'usuari no pot fer factures d'albarans d'una altra empresa")
        
        # momentaniament canvio l'empresa de l'usuari a l'empresa de la SO
        comp_old = self.pool.get('res.users').company_get(cr,uid,uid)
        #print 'Canvi de usuari %d -> %d ' % (company_id , comp_old)
        if company_id != comp_old:
            self.pool.get('res.users').write(cr,uid,[uid],{'company_id':company_id})
        res = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states)
        if company_id != comp_old:
            self.pool.get('res.users').write(cr,uid,[uid],{'company_id':comp_old})
        #inv=self.pool.get('account.invoice').browse(cr,uid,res)
        return res

    def _make_invoice(self, cr, uid, order, lines):
        """ Generem la linia especial de descompte i de despeses financeres """
        total_base=0.0
        for line in self.pool.get("account.invoice.line").browse(cr,uid,lines):
            total_base = total_base + line.price_subtotal

        por_fin= False
        por_fac= order.cash_discount

        if order.customer_id and order.customer_id.name[1:4] != "000":
            # % descompte crèdit
            por_fac = order.customer_id.discount_inv
            # % gastos financers
            if order.customer_id.financing_cost:
                por_fin = order.customer_id.financing_cost.percentage

        if por_fac:
            # Descompte de facturació
            imp_fac = round(total_base * por_fac / 100,2)
            taxes = order.partner_id.property_account_discount.tax_ids
            line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                'name': "Descuento",
                'account_id': order.partner_id.property_account_discount.id,
                'price_unit': -imp_fac,
                'quantity': 1,
                'discount': 0.0,
                'uos_id': False,
                'product_id': False,
                'invoice_line_tax_id': [(6,0,[t.id for t in taxes  ])],
                'note': False,
                'account_analytic_id': False,
            })
            lines.append(line_id)
            total_base = total_base - imp_fac

        if por_fin:
            # Ingressos de finançament
            imp_fin = round(total_base * por_fin / 100,2)
            line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                'name': "Gastos Financieros",
                'account_id': order.partner_id.property_account_financing.id,
                'price_unit': imp_fin,
                'quantity': 1,
                'discount': 0.0,
                'uos_id': False,
                'product_id': False,
                'invoice_line_tax_id': False,
                'note': False,
                'account_analytic_id': False,
            })
            lines.append(line_id)

        # Comptats
        # - guardo el partner original per després 
        # - la factura s'ha de generar amb les dades del partner comptat
        order_partner=order.partner_id
        order.partner_id=order.customer_id.partner_id
        
        if not order.customer_id.partner_id.property_account_receivable:
            print order.name,order.delivery
            raise osv.except_osv(
            "Facturació cancel·lada",
            "El client %s no té cap Compte definit per l'empresa %s" % 
                        (order.customer_id.name,order.company_id.name)
            )

        inv_id = super(sale_order, self)._make_invoice(cr, uid, order,lines)
        inv_obj = self.pool.get('account.invoice')

        if order.customer_id and order.customer_id.name[1:4] == "000":
            pt_obj= self.pool.get('account.payment.term')
            pay_term= pt_obj.search(cr,uid,[('type','=','comptat')])[0]
            inv_obj.write(cr,uid,inv_id,{'payment_term': pay_term,
                        'partner_id':order_partner.id})

        # Abonament
        # Els abonaments no es graven com a abonaments, són factures negatives
        #if order.amount_untaxed < 0:
        #    inv_obj.write(cr,uid,inv_id,{'type': 'out_refund'})

        """
        # Recalcular els impostos
        #tax_obj = self.pool.get('account.tax')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv= inv_obj.browse(cr,uid,inv_id)
        for tax_line in inv.tax_line:
            tax_id= tax_obj.search(cr,uid,[('tax_code_id','=',tax_line.tax_code_id.id)])[0]
            tax_data= tax_obj.read(cr,uid,[tax_id],['amount','tax_sign'])[0]
            tax_imp= round(tax_data['amount']*tax_data['tax_sign']*total_base,2)
            inv_tax_obj.write(cr,uid,[tax_line.id],{'amount':tax_imp})
                #{'name':inv.number+" "+tax_line.name,'amount':tax_imp})
        """

        # Diferenciem adreça de contacte i adreça de factura (Fiscal)
        if order.partner_order_id.id != order.partner_invoice_id.id:
            inv_obj.write(cr,uid,inv_id,
                    {'address_contact_id': order.partner_order_id.id })

        inv_obj.compute_date_due(cr,uid,inv_id)
        
        # Numero la factura
        inv_obj.action_number(cr, uid, [inv_id])
        inv_obj.button_reset_taxes(cr,uid,[inv_id])
        return inv_id

    def create(self, cr, uid, vals, context=None):
        cust= self.pool.get('res.partner.customer').browse(cr,uid,vals['customer_id'])
        self.check_risc(cr,uid,cust.partner_id,cust.company_id.id)
        vals['company_id']=cust.company_id.id
        if 'line_type' not in vals:
            vals['line_type']=context['line_type']
        if 'pricelist_id' not in vals or not vals['pricelist_id']:
            vals['pricelist_id']=self.pool.get('product.pricelist').search(cr, uid, [('type','=','sale')])[0]
        if 'partner_order_id' not in vals and 'partner_id' in vals:
            d = super(sale_order, self).onchange_partner_id(cr,uid,[],vals['partner_id'])
            for k in d['value'].keys():
                if k not in vals or not vals[k]:
                    vals[k] = d['value'][k]
        r= super(sale_order, self).create(cr, uid,vals, context=context)
        return r

    def write(self, cr, uid, ids, vals, context={}):
        if 'customer_id' in vals and vals['customer_id']:
            cust = self.pool.get('res.partner.customer').browse(cr,uid,vals['customer_id'])
            vals['company_id']=cust.company_id.id
        return super(sale_order, self).write(cr, uid, ids, vals, context=context)

    # COMISSIONS
    def close_liquidation(self,cr,uid,ids,date):
        self.write(cr,uid,ids,{'date_comission':date})
        return
    def set_comission(self,cr,uid,ids):
        for so in self.browse(cr,uid,ids):
            agent_id=None
            comission=0.0
            amount_comission=0.0
            
            product= so.order_line[0].product_id
            if so.customer_id and so.customer_id.agent_id:
                agent=so.customer_id.agent_id
                for p in agent.product_ids:
                    if p.product_id.id == product.id:
                        comission=p.comission or 0.0
                        agent_id=agent.id
                        break
            
            if not agent_id and product and product.default_agent_id:
                agent_id=product.default_agent_id.id
                comission=product.default_comission or 0.0
            
            self.write(cr,uid,[so.id],
                {'agent_id':agent_id,
                 'comission':comission,
                 'amount_comission':so.amount_untaxed * comission / 100})
        return

"""
    def test_state(self, cr, uid, ids, mode, *args):
        batch_id=self.pool.get('res.users').search(cr,uid,[('login','=','batch')])[0]
        return super(sale_order, self).test_state(cr, batch_id, ids, mode, *args)
    def action_ship_end(self, cr, uid, ids, context={}):
        batch_id=self.pool.get('res.users').search(cr,uid,[('login','=','batch')])[0]
        return super(sale_order, self).action_ship_end(cr, batch_id, ids, context)
"""
sale_order()

class sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = "sale.order.line"
    _order = 'id'

    def _customer_pricelist(self, cr, uid, ids, field_name, arg, context):
        company_id=self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        res = {}
        for l in self.browse(cr, uid, ids):
            res[l.id] = self.get_pricelist_partner_text(cr,uid,l.product_id.id,l.order_id.partner_id.id,company_id)
        return res

    def _default_uom(self, cr, uid, context): 
        if 'line_type' in context: 
            if context['line_type'] == 'RE':
                return self.pool.get('product.uom').search(cr,uid,[('name','=','Unit')])[0]
        return False

    def _default_line_type(self, cr, uid, context): 
        if 'line_type' in context:
            return context['line_type']
        return "VA"

    def _default_name(self, cr, uid, context):
        #print context
        return str(10)

    _defaults = {
        #'name': _default_name,
        'product_uom': _default_uom,
        'line_type': _default_line_type,
        'quantity': lambda *a: 1,
        'kilos': lambda *a: 1,
        'diameter': lambda *a: 1,
        'length': lambda *a: 1,
        'depth': lambda *a: 0,
        'customer_pricelist': lambda *a: "Tarifa General",
    }

    _columns = {
        'line_type': fields.selection([('TR','Tractament'),('RE','Recobriment'),('VA','Varis')], 'Tipus',required=True),
        
        # tractaments
        #'depth': fields.integer('Profunditat',readonly=True),
        'depth': fields.integer('Profunditat'),
        'customer_pricelist': fields.function(_customer_pricelist, method=True, string='Preus Especials', type='char', size=20),
        'pricelist_partner_id': fields.many2one('pricelist.partner','Preu Especial'),

        # recobriments
        'piece_id': fields.many2one('pricelist.piece', 'Peça'),
        'length': fields.float('Longitud', digits=(16,2), ),
        'diameter': fields.float('Diàmetre', digits=(16,2), ),
        'hard_metal': fields.boolean('Metall dur'),
        
        # comuns
        'manual': fields.boolean('Preu Manual',readonly=True),
        'price_min': fields.float('Import Minim', digits=(16, int(config['price_accuracy'])),readonly=True),
        'pricelist_price': fields.float("Preu de la Tarifa",digits=(16,int(config['price_accuracy'])),readonly=True),

        'kilos': fields.float('Kilos', digits=(16,2), ),
        'quantity': fields.float('Quantitat', digits=(16,2), ),
    }

    def generic_taxes(self, cr, uid, order_company):
        s = [('domain','=',"Defecte"),('company_id','=',order_company)]
        print s
        return self.pool.get('account.tax').search(cr,uid,s)

    def get_taxes(self, cr, uid, product, order_company):
        if not product:
            return self.generic_taxes(cr,uid,order_company)
        tax_ids=list()
        for tax in product.taxes_id:
            if tax.company_id.id == order_company:
                tax_ids.append(tax.id)
        return tax_ids

    # Validar preus especials vigents
    def _check_pricelist_partner(self,cr,uid,ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        date = time.strftime('%Y-%m-%d') 
        for sol in self.browse(cr, uid, ids):
            if sol.order_id.state != "draft":
                continue
            if not sol.pricelist_partner_id:
                continue
            if sol.pricelist_partner_id.date_start and sol.pricelist_partner_id.date_start > date or \
               sol.pricelist_partner_id.date_end   and sol.pricelist_partner_id.date_end < date:
                raise osv.except_osv(
                    "La tarifa %s del client no és vigent" % (sol.pricelist_partner_id.name),
                    "No es pot posar aquesta tarifa")
                return False
        return True



    def _complete_order_line(self, cr, uid, ids):
        for sol in self.browse(cr, uid, ids):
            if sol.order_id.state != "draft":
                continue
            delay= sol.product_id and sol.product_id.sale_delay or 0.0
            line_type= sol.order_id.line_type
            taxes= self.get_taxes(cr,uid,sol.product_id,sol.order_id.company_id.id)
            sol_taxes = [tax.id for tax in sol.tax_id]
            if line_type != sol.line_type or delay != sol.delay or taxes != sol_taxes:
                self.write(cr, uid, sol.id, 
                    {'line_type':        line_type,
                    'delay':            delay,
                    'tax_id':           [(6,0,taxes)],
                    })
            if not sol.order_id.quality_note or sol.order_id.quality_note == "":
                if sol.product_id and sol.product_id.description_sale:
                    self.pool.get('sale.order').write(cr,uid,sol.order_id.id,
                        {'quality_note':sol.product_id.description_sale})
        return True

    def _update_manual(self, cr, uid, ids):
        for sol in self.browse(cr, uid, ids):
            if sol.order_id.state != "draft":
                continue
            manual = False
            if sol.order_id.line_type == "TR":
                if sol.product_uom.id != self.pool.get('pricelist.kilo').get_product_uom(cr,uid,sol.product_id.id,sol.depth):
                    manual = True
            if sol.price_unit != sol.pricelist_price:
                manual = True
            if manual != sol.manual:
                self.write(cr, uid, sol.id, {'manual': manual})
        return True

    def _update_quantity_uom(self, cr, uid, ids):
        for sol in self.browse(cr, uid, ids):
            if sol.order_id.state != "draft":
                continue
            if sol.order_id.line_type == "RE":
                product_uom_qty = sol.quantity
            else:
                # sol.order_id.line_type == "VA" o "TR"
                if sol.product_uom.name.upper().startswith('K'):
                    product_uom_qty = sol.kilos
                else:
                    product_uom_qty = sol.quantity
            if product_uom_qty != sol.product_uom_qty:
                self.write(cr, uid, sol.id, {'product_uom_qty': product_uom_qty,'product_uos_qty':product_uom_qty})
        return True

    def _update_prices(self, cr, uid, ids):
        for sol in self.browse(cr, uid, ids):
            if sol.order_id.state != "draft":
                continue
            if sol.order_id.line_type == "TR":
                if sol.pricelist_partner_id:
                    # Tarifa especial de Tractament
                    price = sol.pricelist_partner_id.price
                    min = sol.pricelist_partner_id.apply_minimum and sol.pricelist_partner_id.minimum or 0.0
                else:
                    # Tarifa general de Tractament
                    kilo_obj=self.pool.get('pricelist.kilo')
                    price,min = kilo_obj.find_price_and_min(cr,uid,sol.product_id.id,sol.depth,sol.product_uom_qty)
                discount = 0.0   
            elif sol.order_id.line_type == "RE":
                # Tarifa de Recobriment
                price,min = self.pool.get('pricelist.rec').find_price_and_min(cr,uid,sol.product_id.id,sol.length,sol.diameter,sol.piece_id.id)
                discount = sol.order_id.customer_id and sol.order_id.customer_id.discount or 0.0
                # Metall dur
                if sol.hard_metal:
                    if sol.product_id.hard_metal != 0.0:
                        price = round(price * (1 + (sol.product_id.hard_metal / 100.0)),3)
            else:
                # sol.order_id.line_type == "VA"
                continue
            if sol.pricelist_price != price or sol.price_min != min or sol.discount != discount:
                self.write(cr, uid, sol.id, {'pricelist_price': price, 'price_min': min, 'discount' : discount})
        return True

    def _validate_refund(self, cr, uid, ids):
        if uid==1 or self.pool.get("res.users").has_groups(cr,uid,uid,["Direcció"]):
            return True
        for sol in self.browse(cr, uid, ids):
            if sol.price_subtotal < 0:
                raise osv.except_osv(
                    "Operació no permesa",
                    "L'usuari no pot fer abonaments")
                return False
        return True

    _constraints = [
        (_check_pricelist_partner, "El client no es correspon amb l'adreça assignada", ['pricelist_partner_id']),
        (_complete_order_line, "Error al completar l'albarà", ['product_id','line_type']),
        (_update_prices, "Error al actualitzar el preu de la tarifa", \
          ['product_id','depth','customer_pricelist','pricelist_partner_id', \
           'piece_id','length','diameter','hard_metal']),
        (_update_quantity_uom, "Error al actualitzar la quantitat", ['product_uom','quantity','kilos']),
        (_update_manual, "Error al actualitzar la marca manual", ['product_uom','price_unit']),
        (_validate_refund, "L'usuari no pot fer abonaments", ['product_uom_qty','product_uos_qty','price_unit']),
    ]
    
    def get_pricelist_partner_text(self, cr, uid, product_id, partner_id, company_id): 
        # Busco preus especials vigents
        date = time.strftime('%Y-%m-%d') 
        cr.execute("SELECT pp.id FROM pricelist_partner pp " +\
                "WHERE pp.partner_id = %d " +\
                  "and pp.company_id = %d " +\
                  "and pp.product_id = %d " +\
                  "and (pp.date_start is null or pp.date_start <= %s)" +\
                  "and (pp.date_end is null or pp.date_end >= %s)",
                  (partner_id,company_id,product_id,date,date))
        res = cr.fetchall()
        if not res:
            return "Tarifa General"
        if len(res) == 1:
            return "1 Tarifa Especial"
        return "%d Tarifes Especials" % len(res)

    def product_id_change_tr(self, cr, uid, ids, product_id, qty=0, uom=False, name='', partner_id=False,
                            depth=0,pricelist_partner_id=False,order_company=False, discount=0.0,
                            kilos=1, quantity=1):
        if not product_id:
            return {}
        vals = {}
        # temporal
        vals['name']=self.pool.get('product.product').browse(cr,uid,product_id).partner_ref
        vals['manual'] = False
        
        company_id=self.pool.get('res.users').browse(cr, uid, uid).pricelist_company_id.id

        if pricelist_partner_id:
            # Tarifa especial
            pl = self.pool.get('pricelist.partner').browse(cr,uid,pricelist_partner_id)
            vals['pricelist_price'] = pl.price
            vals['price_unit'] = pl.price
            vals['price_min'] = pl.apply_minimum and pl.minimum or 0.0
            vals['product_uom'] = pl.product_uom.id
            vals['pricelist_partner_id']=pricelist_partner_id
        else:
            # Tarifa general
            kilo_obj=self.pool.get('pricelist.kilo')
            vals['product_uom']= kilo_obj.get_product_uom(cr,uid,product_id,depth)
            qty=self.get_quantity_uom(cr,uid,vals['product_uom'],kilos,quantity)
            if not qty:
                #print vals['product_uom'],kilos,quantity
                return {}
            price,min = kilo_obj.find_price_and_min(cr,uid,product_id,depth,qty)
            #print price,min
            vals['pricelist_price'] = price
            vals['price_unit'] =  price
            vals['price_min'] =  min
            vals['pricelist_partner_id']=False
            vals['customer_pricelist']=self.get_pricelist_partner_text(cr,uid,product_id,partner_id,company_id)
            
        # Calculo totals
        vals['discount']=0.0
        vals.update(self.compute_line(cr,uid,ids,'TR',vals['price_unit'],vals['discount'],quantity,kilos,vals['product_uom']))
        #for i,v in vals.iteritems():
        #    print "%20s -> %s" % (i,v)
        #print "-----------------------------------------------------"
        return {'value':vals}

    def product_id_change_re(self, cr, uid, ids, product_id, qty=0, uom=False, name='', partner_id=False,
                            length=0, diameter=0, piece_id=False, hard_metal=False, customer_id=False,
                            order_company=False, quantity=1):
        if not product_id:
            return {}
        vals = {}
        # temporal
        product=self.pool.get('product.product').browse(cr,uid,product_id)
        vals['name']=product.partner_ref
        vals['manual'] = False
        vals['product_uom']= product.uom_id and product.uom_id.id
        
        # busco tarifa general
        price,min = self.pool.get('pricelist.rec').find_price_and_min(cr,uid,product_id,length,diameter,piece_id)

        if customer_id:
            vals['discount'] = self.pool.get('res.partner.customer').browse(cr,uid,customer_id).discount
        else:
            vals['discount'] = 0.0

        if hard_metal:
            # recarrec metall dur
            por_hard_metal = self.pool.get('product.product').browse(cr,uid,product_id).hard_metal
            if por_hard_metal != 0.0:
                price = price * (1 + (por_hard_metal / 100.0))

        vals['pricelist_price'] = price
        vals['price_unit'] =  price
        vals['price_min'] =  min

        # Calculo totals
        vals.update(self.compute_line(cr,uid,ids,'RE',vals['price_unit'],vals['discount'],quantity))
        #for i,v in vals.iteritems():
        #    print "%20s -> %s" % (i,v)
        #print "-----------------------------------------------------"
        
        return {'value':vals}


    def product_id_change_all(self, cr, uid, ids, line_type, product_id, qty=0, uom=False, name='', partner_id=False,
                            length=0, diameter=0, piece_id=False, hard_metal=False, customer_id=False,
                            depth=0,pricelist_partner_id=False,order_company=False, discount=0.0,
                            kilos=1, quantity=1):
        if line_type == 'TR':
            return self.product_id_change_tr(cr,uid,ids,product_id,qty,uom,name,partner_id,
                                    depth,pricelist_partner_id,order_company,discount,kilos,quantity)
        elif line_type == 'RE':
            return self.product_id_change_re(cr,uid,ids,product_id,qty,uom,name,partner_id,
                                    length,diameter,piece_id,hard_metal,customer_id,order_company,quantity)
        if product_id == False:
            return {}
        raise osv.except_osv(
                "S'ignora el tractament",
                "Full de Ruta Varis")


    def quantity_change(self,cr,uid,ids,line_type,price_unit,pricelist_price,discount=0.0,quantity=1,kilos=1,product_uom=False):
        vals = self.compute_line(cr,uid,ids,line_type,price_unit,discount,quantity,kilos,product_uom)
        #for i,v in vals.iteritems():
        #    print "%20s -> %s" % (i,v)
        #print "-----------------------------------------------------"
        return {'value':vals}

    def manual_change(self,cr,uid,ids,line_type,price_unit,pricelist_price,discount=0.0,quantity=1,product_uom=False,kilos=1,product_id=False,depth=0):
        vals={'manual':False}
        if line_type == 'VA':
            vals['manual']=True
        if line_type == 'TR':
            kilo_obj=self.pool.get('pricelist.kilo')
            if product_uom != kilo_obj.get_product_uom(cr,uid,product_id,depth):
                vals['manual']=True
        #if discount != 0.0:
        #    vals['manual']=True
        if price_unit != pricelist_price:
            vals['manual']=True
        vals.update(self.compute_line(cr,uid,ids,line_type,price_unit,discount,quantity,kilos,product_uom))
        #for i,v in vals.iteritems():
        #    print "%20s -> %s" % (i,v)
        #print "-----------------------------------------------------"
        return {'value':vals}

    def get_quantity_uom(self,cr,uid,product_uom,kilos,quantity):
        if not product_uom:
            return False
        fields=self.pool.get('product.uom').read(cr,uid,[product_uom],['name'])
        if not fields or 'name' not in fields[0]:
            return False
        if fields[0]['name'].upper().startswith('K'):
            return kilos
        else:
            return quantity

    def compute_line(self,cr,uid,ids,line_type,price_unit,discount,quantity,kilos=0,product_uom=False):
        
        #print price_unit 
        #print (1 - (discount / 100.0))
        #print price_unit * (1 - (discount / 100.0))
        price_net= round(price_unit * (1 - (discount / 100.0)),3)
        price_subtotal= round(price_net * quantity ,2)
        #print price_net
        if line_type == 'VA':
            ret= {
                'quantity'       : quantity,
                'price_unit'     : price_unit,
                'discount'       : discount,
                'product_uom_qty': quantity,
                'price_net'      : price_net,
                'price_subtotal' : price_subtotal,
            }
        if line_type == 'RE':
            ret= {
                'quantity'       : quantity,
                'price_unit'     : price_unit,
                'discount'       : discount,
                'product_uom_qty': quantity,
                'price_net'      : price_net,
                'price_subtotal' : price_subtotal,
            }
        if line_type == 'TR':
            qty=self.get_quantity_uom(cr,uid,product_uom,kilos,quantity)
            if not qty:
                return {}
            price_subtotal= round(price_net * qty ,2)
            ret= {
                'kilos'          : kilos,
                'quantity'       : quantity,
                'price_unit'     : price_unit,
                'discount'       : discount,
                'product_uom_qty': qty,
                'product_uom'    : product_uom,
                'price_net'      : price_net,
                'price_subtotal' : price_subtotal,
            }
        return ret


    def create_carreras_invoice_lines(self, cr, uid, ids, context={}):
        """
        def _get_line_qty(line):
            if (line.order_id.invoice_quantity=='order') or not line.procurement_id:
                return line.product_uos_qty or line.product_uom_qty
            else:
                return self.pool.get('mrp.procurement').quantity_get(cr, uid, line.procurement_id.id, context)
        """
        create_ids = []
        for line in self.browse(cr, uid, ids, context):
            if not line.invoiced:
                if line.product_id:
                    a =  line.product_id.product_tmpl_id.property_account_income.id
                    if not a:
                        a = line.product_id.categ_id.property_account_income_categ.id
                    if not a:
                        raise osv.except_osv('Error !', 'There is no income account defined for this product: "%s" (id:%d)' % (line.product_id.name, line.product_id.id,))
                else:
                    a = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category', context=context)
                # He comentat aquesta part perque sempre s'agafi l'import calculat a
                # l'albarà, sinó al calcular una altra vegada pot donar diferent i donar
                # error al confirmar la factura
                # Això passa pels 3 decimals
                """
                uosqty = _get_line_qty(line)
                uos_id = (line.product_uos and line.product_uos.id) or line.product_uom.id
                pu = line.price_unit
                if line.product_uos_qty:
                    pu = round(pu * line.product_uom_qty / line.product_uos_qty, int(config['price_accuracy']))
                """
                uosqty = 1
                uos_id = (line.product_uos and line.product_uos.id) or line.product_uom.id
                pu=line.price_subtotal
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
                    'name': line.name,
                    'account_id': a,
                    'price_unit': pu,
                    'quantity': uosqty,
                    'discount': 0,
                    'uos_id': uos_id,
                    'product_id': line.product_id.id or False,
                    'invoice_line_tax_id': [(6,0,[x.id for x in line.tax_id])],
                    'note': line.notes,
                    'account_analytic_id': line.order_id.project_id.id,
                })
                cr.execute('insert into sale_order_line_invoice_rel (order_line_id,invoice_id) values (%d,%d)', (line.id, inv_id))
                self.write(cr, uid, [line.id], {'invoiced':True})
                create_ids.append(inv_id)
        return create_ids

    def invoice_line_create(self,cr,uid,ids,context={}):
        if ids:
            order=self.browse(cr,uid,ids[0]).order_id
            if order.block:
                return []
        create_ids=self.create_carreras_invoice_lines(cr, uid, ids, context)
        if not create_ids:
            return create_ids
        #print "invoice_line_create",create_ids
        #order=self.browse(cr,uid,ids[0]).order_id
        #print order.name,order.delivery,order.partner_id.name,order.customer_id.name
        #print order.amount_lines,order.amount_minimum
        if order.amount_lines >= order.amount_minimum:
            return create_ids
        
        if order.amount_untaxed < 0:
            # Tractar el abonaments com a factures negatives
            return create_ids
            #il_obj=self.pool.get('account.invoice.line')
            #for val in il_obj.read(cr,uid,create_ids,['price_unit']):
            #    il_obj.write(cr,uid,[val['id']],{'price_unit': -val['price_unit']})
            #return create_ids

        # crear una linia per aplicar el mínim
        ail=self.pool.get("account.invoice.line").browse(cr,uid,create_ids[0])
        taxes=self.generic_taxes(cr,uid,order.company_id.id)
        inv_id = self.pool.get('account.invoice.line').create(cr, uid, {
            'name': "Aplicar Mínimo",
            'account_id': ail.account_id.id,
            'price_unit': (order.amount_minimum - order.amount_lines),
            'quantity': 1,
            'discount': 0.0,
            'uos_id': False,
            'product_id': False,
            #'invoice_line_tax_id': [(6,0,[t.id for t in taxes  ])],
            'invoice_line_tax_id': [(6,0,taxes)],
            'note': False,
            'account_analytic_id': False,
        })
        create_ids.append(inv_id)
        #print "invoice_line_create",inv_id,"->",create_ids
        return create_ids

sale_order_line()
