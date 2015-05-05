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

# 29.05.2009 Poder modificar sempre l'intervinent i l'adreça de facturació de
#            les factures de clients i proveïdors
# 14.06.2010 Refer el càlcul de l'import de l'impost per poder fer correctament
#            el canvi de IVA (i l'arrodoniment que originalment no ananva bé)

import tools
import ir
import pooler
import netsvc

from osv import fields,osv
#import memcached as osv
from decimal import Decimal

class account_invoice(osv.osv):

    _name = "account.invoice"
    _inherit = "account.invoice"
    _order = "date_invoice desc,number"

    def _get_reference_type(self, cursor, user, context=None):
        return [('none', 'Número de Registre')]

    
    def _amount_untaxed(self, cr, uid, ids, name, args, context={}):
        # arrodonir correctament
        id_set=",".join(map(str,ids))
        #cr.execute("SELECT s.id,COALESCE(SUM(l.price_unit*l.quantity*(100-l.discount))/100.0,0)::decimal(16,2) AS amount FROM account_invoice s LEFT OUTER JOIN account_invoice_line l ON (s.id=l.invoice_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
        cr.execute("SELECT s.id,COALESCE(SUM(l.price_unit*l.quantity*(100-l.discount)/100.0::decimal(16,2)),0) AS amount FROM account_invoice s LEFT OUTER JOIN account_invoice_line l ON (s.id=l.invoice_id) WHERE s.id IN ("+id_set+") GROUP BY s.id")
        res=dict(cr.fetchall())
        return res


    """
    def _amount_total(self, cr, uid, ids, name, args, context={}):
        untax = self._amount_untaxed(cr, uid, ids, name, args, context)
        tax = self._amount_tax(cr, uid, ids, name, args, context)
        res = {}
        for id in ids:
            res[id] = untax.get(id,0.0) + tax.get(id,0.0)
        return res
    """
    """
    def _amount_tax(self, cr, uid, ids, name, args, context={}):
        id_set=",".join(map(str,ids))
        cr.execute("SELECT s.id,COALESCE(SUM(l.amount),0)::decimal(16,2) AS amount FROM account_invoice s LEFT OUTER JOIN account_invoice_tax l ON (s.id=l.invoice_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
        res=dict(cr.fetchall())
        return res
    """
    """
    def _account_code(self, cr, uid, ids, name, args, context={}):
        res = {}
        for inv in self.pool.get('account.account').read(cr,uid,ids,['code']):
            res[inv['id']]=inv['code']
        return res
            
    """
    
    _columns = {
        'reference_type': fields.selection(_get_reference_type, 'Reference Type',
            required=True),
        'sequence_id': fields.many2one('ir.sequence', "Numerador de Factures",
                help="Numerador de factures d'aquesta factura", readonly=True, required=False),
        'date_supplier': fields.date('Data del proveïdor'),
        #'amount_total': fields.function(_amount_total, method=True, string='Total', store=True),
        'amount_untaxed': fields.function(_amount_untaxed, method=True, digits=(16,2),string='Untaxed'),
        #'amount_tax': fields.function(_amount_tax, method=True, string='Tax', store=True),
        #'account_code': fields.function(_account_code, method=True, string='Compte'),
        #'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'draft':[('readonly',False)]}),
        #'invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=False),
        #'tax_line': fields.one2many('account.invoice.tax', 'invoice_id', 'Tax Lines', readonly=True, states={'draft':[('readonly',False)]}),
        #'tax_line': fields.one2many('account.invoice.tax', 'invoice_id', 'Tax Lines', readonly=False),
        'partner_id': fields.many2one('res.partner', 'Partner', change_default=True, required=True),
        'address_contact_id': fields.many2one('res.partner.address', 'Contact Address'),
        'address_invoice_id': fields.many2one('res.partner.address', 'Invoice Address', required=True),
    }

    #def _get_company(self, cr, uid, context):
    #    return self.pool.get('res.users').company_get( cr, uid, uid )

    # _defaults = {
    #   'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'account.invoice.manual'),
    #}

    def _check_company(self, cr, uid, ids):
        lines = self.browse(cr, uid, ids)
        for i in lines:
            for child in i.company_id.child_ids:
                return False
        return True

    def _check_address(self,cr,uid,ids):
        if uid==1 or self.pool.get('res.users').browse(cr, uid, uid).login == "batch":
            return True
        for inv in self.browse(cr, uid, ids):
            if inv.account_id.code[5:8] != '000':
                if (inv.address_contact_id and inv.address_contact_id not in inv.partner_id.address) or \
                   (inv.address_invoice_id and inv.address_invoice_id not in inv.partner_id.address):
                    raise osv.except_osv(
                        "El client %s no es correspon amb l'adreça assignada" % (inv.partner_id.name),
                        "S'ha d'assignar a la factura una adreça del client")
                    return False
        return True

    _sql_constraints = [
        ('ref_uniq', 'unique (reference,company_id,type)', 'El Registre ha de ser únic !'),
        ('number_uniq', 'unique (number,company_id)', 'Existeix una factura amb el mateix número !'),
        ]

    _constraints = [
        (_check_address, "El client no es correspon amb l'adreça assignada", ['partner_id']),
        (_check_company, "No es poden fer factures a aquesta empresa", ['company_id']),
    ]

    def action_move_create(self, cr, uid, ids, *args):
        ap=self.pool.get('account.period')
        for inv in self.browse(cr,uid,ids):
            #date_reference= \
            #    inv.type=='out_invoice' and inv.date_invoice or inv.date_supplier
            if not inv.period_id:
                #ap_ids=ap.find(cr,uid,date_reference)
                ap_ids=ap.find(cr,uid,inv.date_invoice)
                self.write(cr,uid,[inv.id],{'period_id':ap_ids[0]})
        if not super(account_invoice, self).action_move_create(cr, uid, ids, *args):
            return False
        pt_obj= self.pool.get('account.payment.term')
        ml_obj= self.pool.get('account.move.line')
        mv_obj= self.pool.get('account.move')
        pay_comptat= pt_obj.search(cr,uid,[('type','=','comptat')])[0]
        for inv in self.browse(cr,uid,ids):
            #if inv.type != 'out_invoice':
            #    continue
            if inv.type not in ['in_invoice','out_invoice']:
                continue
            #print inv.amount_total,"----------------------"
            # Partides vives generades
            lines=[]
            for line in inv.move_id.line_id:
                if line.account_id == inv.account_id:
                    lines.append((line.id,line.date_maturity))
            # Calcular el venciments
            if inv.type=='out_invoice':
                if inv.payment_term and inv.payment_term.id != pay_comptat:
                    context={}
                    if inv.type == 'out_invoice':
                        context = {"partner_id" : inv.partner_id.id}
                    dates = pt_obj.compute(cr, uid, inv.payment_term.id, \
                        inv.amount_total, date_ref=inv.date_invoice, context=context)
                else:
                    dates = [ (inv.date_due,inv.amount_total) ]
                # Ha de quadrar en factures de clients
            if inv.type=='in_invoice':
                # En factures de proveidors es posa el venciment informat
                # (si és una factura d'un únic venciment)
                if len(lines) == 1:
                    dates = [ (inv.date_due,inv.amount_total) ]
                else:
                    dates = pt_obj.compute(cr, uid, inv.payment_term.id, \
                        inv.amount_total, date_ref=inv.date_invoice, context={})
                    # canvi de referencia
                    #    inv.amount_total, date_ref=inv.date_supplier, context={})
            if len(dates) != len(lines):
                return False
            # Gravar els venciments
            dates.sort(lambda x,y: cmp(x[0],y[0]))
            lines.sort(lambda x,y: cmp(x[1],y[1]))
            mv_obj.write(cr, uid, [inv.move_id.id], {'state':'draft'})
            for d,l in zip(dates,lines):
                if inv.type=='out_invoice':
                    ml_obj.write(cr,uid,[l[0]],{'date_maturity':d[0],
                        'debit': d[1]>0 and d[1],'credit':d[1]<0 and -d[1]})
                else:
                    ml_obj.write(cr,uid,[l[0]],{'date_maturity':d[0],
                        'debit': d[1]<0 and -d[1],'credit':d[1]>0 and d[1]})
            #print inv.move_id.state
            #if inv.move_id.state != 'posted':
            mv_obj.write(cr, uid, [inv.move_id.id], {'state':'posted'})
            
            if inv.type != 'out_invoice':
                continue
            # Es marca la data ultima factura
            if inv.date_invoice > inv.partner_id.last_invoice:
                self.pool.get('res.partner').write(cr,uid,inv.partner_id.id,\
                        {'last_invoice':inv.date_invoice})
        return True

    def action_number(self, cr, uid, ids, *args):
        #print ids
        invoices=filter(lambda x: not x['number'],self.read(cr,uid,ids,['number']))
        #print invoices
        for invoice in invoices:
            inv=self.browse(cr,uid,invoice['id'])
            if inv.type not in ['in_invoice','out_invoice']:
                # per aqui no passa mai
                super(account_invoice, self).action_number(cr, uid, [inv.id], *args)
                continue
            if inv.type == 'in_invoice':
                self.write(cr,uid,inv.id,{'number':str(inv.id)})
                ref = inv.reference
            if inv.type == 'out_invoice':
                if not inv.partner_id.customer_ids:
                    sequence_id=inv.company_id.cash_sequence_id.id
                else:
                    sequence_id=inv.company_id.credit_sequence_id.id
                if inv.amount_untaxed < 0:
                    sequence_id=inv.company_id.refund_sequence_id.id
                number=self.pool.get('ir.sequence').get_id(cr, uid, sequence_id)
                ref = self._convert_ref(cr, uid, number)
                self.write(cr,uid,inv.id,{'name':number,'number':number,'sequence_id':sequence_id})
            move_id=inv.move_id and inv.move_id.id or None
            cr.execute('UPDATE account_move_line SET ref=%s WHERE move_id=%d and ref is null', (ref, move_id))
            cr.execute('UPDATE account_analytic_line SET ref=%s FROM account_move_line WHERE account_move_line.move_id=%d AND account_analytic_line.move_id=account_move_line.id', (ref, move_id))
        return True

    #def _inv_get(self, cr, uid, order, context={}):
        # informo la data de venciment
        #print "hola"
        #inv_obj = self.pool.get('account.invoice')
        #inv = inv_obj.browse(cr,uid,res)
        #if not inv.date_due:
        #    if inv.payment_term:
        #        context = {"partner_id" : inv.partner_id.id}
        #        dates = self.pool.get('account.payment.term').compute(cr, uid, \
        #                            inv.payment_term.id,inv.amount_total, \
        #                            date_ref=date_invoice, context=context )
        #        if dates and dates[0]:
        #            inv_obj.write(cr,uid,inv.id,{'date_due': dates[0][0] })

    # Calcula la data de venciment
    def compute_date_due(self, cr, uid, inv_id):
        inv = self.browse(cr,uid,inv_id)
        if not inv.payment_term:
            return False
        context = {"partner_id" : inv.partner_id.id}
        date_reference= inv.date_invoice
        # canvi de referencia
        #date_reference= \
        #    inv.type=='out_invoice' and inv.date_invoice or inv.date_supplier
        dates = self.pool.get('account.payment.term').compute(cr, uid, \
                            inv.payment_term.id,inv.amount_total, \
                            date_ref=date_reference, context=context )
        if not dates or not dates[0]:
            return False
        self.write(cr,uid,inv.id,{'date_due': dates[0][0] })
        return True

    def action_cancel_all(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            # signal invoice_cancel de account_invoice
            wf_service.trg_validate(uid, 'account.invoice', id, 'invoice_cancel', cr)
        so_obj=self.pool.get('sale.order')
        so_ids=so_obj.search(cr,uid,[('invoice_ids','in',ids)])
        for id in so_ids:
            # signal invoice_cancel de sale_order
            wf_service.trg_validate(uid, 'sale.order', id, 'invoice_cancel', cr)
        # metode action_cancel_draft de sale_order
        so_obj.action_cancel_draft(cr,uid,so_ids)
        for id in so_ids:
            # signal order_confirm de sale_order
            wf_service.trg_validate(uid, 'sale.order', id, 'order_confirm', cr)
        return True

    def name_get(self, cr, uid, ids, context={}):
        if not len(ids):
            return []
        types = {
                'out_invoice': 'C: ',
                'out_refund': 'C: ',
                'in_invoice': 'P: ',
                'in_refund': 'P: ',
                }
        invs=[]
        for r in self.read(cr, uid, ids, ['number','type','amount_untaxed','reference'], context, load='_classic_write'):
            if r['type'] in ('in_invoice','in_refund'):
                invs.append((r['id'], (r['amount_untaxed'] < 0 and 'A' or 'F') + types[r['type']] + (r['reference'] or ' ')))
            else:
                invs.append((r['id'], (r['amount_untaxed'] < 0 and 'A' or 'F') + types[r['type']] + (r['number'] or ' ')))
        return invs

    def onchange_partner_id(self, cr, uid, ids, type, partner_id):
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id)
        if type not in ('in_invoice', 'in_refund'):
            return result
        # forma de pagament al proveidor
        result['value']['payment_term']=False
        if partner_id:
            p = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if p.property_supplier_payment_term:
                result['value']['payment_term'] = p.property_supplier_payment_term.id
        return result
    
    def unlink(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids, context):
            if obj.type == 'out_invoice' and obj.state != 'cancel':
                raise osv.except_osv('No es pot eliminar !', 'Només es poden eliminar les factures cancel·lades!')
            if obj.type == 'in_invoice' and obj.move_id.id:
                raise osv.except_osv('No es pot eliminar !', "S'ha d'esborrar l'assentament de la factura abans!")
        return super(osv.osv, self).unlink(cr, uid, ids)

account_invoice()

class account_invoice_line(osv.osv):

    #def _get_company(self, cr, uid, context):
    #    return self.pool.get('res.users').company_get( cr, uid, uid )

    _name = "account.invoice.line"
    _inherit = "account.invoice.line"

    def _amount_line(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        res = {}
        for line in self.browse(cr, uid, ids):
            res[line.id] = round(line.price_unit * line.quantity * (1-(line.discount or 0.0)/100.0),2)
            #d= Decimal(str(line.price_unit * line.quantity * (1-(line.discount or 0.0)/100.0)))
            #print res[line.id]
            #print d
            #print round(d,2)
        return res

    _columns = {
        'price_subtotal': fields.function(_amount_line, method=True, string='Subtotal'),
    }
    
    def _query_get(self, cr, uid, obj='l', context={}):
        if not 'fiscalyear' in context:
            context['fiscalyear'] = self.pool.get('account.fiscalyear').find(cr, uid, exception=False)
        if context.get('periods', False):
            ids = ','.join([str(x) for x in context['periods']])
            return obj+".active AND "+obj+".state<>'draft' AND "+obj+".period_id in (SELECT id from account_period WHERE fiscalyear_id=%d AND id in (%s))" % (context['fiscalyear'], ids)
        else:
            return obj+".active AND "+obj+".state<>'draft' AND "+obj+".period_id in (SELECT id from account_period WHERE fiscalyear_id=%d)" % (context['fiscalyear'],)

    def move_line_get(self, cr, uid, invoice_id, context={}):
        res = super(account_invoice_line, self).move_line_get(cr, uid, invoice_id, context)
        #logger= netsvc.Logger()
        #logger.notifyChannel("info", netsvc.LOG_INFO,res)
        #logger.notifyChannel("info", netsvc.LOG_INFO,acc_ids)
        # intentar agrupar linies amb el mateix compte
        acc_ids = set([x['account_id'] for x in res])
        inv = self.pool.get('account.invoice').browse(cr,uid,invoice_id,context)
        for acc in acc_ids:
            orig = None
            res2 = res[:]
            for line in res2:
                if line['account_id'] ==  acc:
                    if not orig:
                        orig = line
                        if inv.type == 'out_invoice':
                            orig['name'] = "%s Factura de Venda" % inv.name
                        elif inv.type == 'in_invoice':
                            orig['name'] = "%s Factura de Compra" % inv.name
                        else:
                            orig['name'] = inv.name
                        #orig['name'] = "Venta factura %s" % inv.number
                    else:
                        orig['price'] += line['price']
                        res.remove(line)
        #print res
        return res

account_invoice_line()

class account_invoice_tax(osv.osv):
    _name = "account.invoice.tax"
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
        cur = inv.currency_id
        for line in inv.invoice_line:
            #print ">>>",line.invoice_line_tax_id
            for tax in tax_obj.compute(cr, uid, line.invoice_line_tax_id, (line.price_unit* (1-(line.discount or 0.0)/100.0)), line.quantity, inv.address_invoice_id.id, line.product_id, inv.partner_id):
                print tax
                val={}
                val['invoice_id'] = inv.id
                val['name'] = "%s %s" % (inv.name,tax['name'])
                val['amount'] = cur_obj.round(cr, uid, cur, tax['amount'])
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = round(tax['price_unit'] * line['quantity']*10,1)/10

                if inv.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = val['base'] * tax['base_sign']
                    val['tax_amount'] = val['amount'] * tax['tax_sign']
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = val['base'] * tax['ref_base_sign']
                    val['tax_amount'] = val['amount'] * tax['ref_tax_sign']
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                #print "-------------------------------"
                #for key,value in val.iteritems():
                #    print '  ',key,value
                
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'],tax['id'])
                #key=tax['id']
                #print key
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    #tax_grouped[key]['amount'] += val['amount']
                    #tax_grouped[key]['tax_amount'] += val['tax_amount']
                    
                    # es recalcula l'import de l'impost a partir de la nova base
                    tax_data= tax_obj.read(cr,uid,[tax['id']],['amount','tax_sign'])[0]
                    tax_grouped[key]['amount']=round(tax_data['amount']*tax_data['tax_sign']*tax_grouped[key]['base_amount'],2)
                    tax_grouped[key]['tax_amount']=round(tax_data['amount']*tax_data['tax_sign']*tax_grouped[key]['base'],2)
        
        # s'agrupen els impostors com es feia originalment
        tax_grouped2 = {}
        for key,value in tax_grouped.iteritems():
            key2=(key[0],key[1],key[2])
            if not key2 in tax_grouped2:
                tax_grouped2[key2] = value
            else:
                tax_grouped2[key2]['base'] += value['base']
                tax_grouped2[key2]['base_amount'] += value['base_amount']
                tax_grouped2[key2]['amount'] += value['amount']
                tax_grouped2[key2]['tax_amount'] += value['tax_amount']
        """
        for key,value in tax_grouped.iteritems():
                print '  ',key,value
        print "1 **************************************"
        for key,value in tax_grouped.iteritems():
            print 'tax_code_id',key[0]
            print 'base_code_id',key[1]
            print 'account_id',key[2]
            for i,j in value.iteritems():
                print "  ",i,j
        """
        """
        # recalcular els impostos
        #tax_obj = self.pool.get('account.tax')
        for key,value in tax_grouped.iteritems():
            # es busquen les dades de l'impost 'account.tax' a partir del
            # compte comptable de l'impost 'account_collected_id'
            account_id = key[2]
            tax_id= tax_obj.search(cr,uid,[('account_collected_id','=',account_id)])[0]
            tax_data= tax_obj.read(cr,uid,[tax_id],['amount','tax_sign'])[0]
            tax_grouped[key]['amount']=round(tax_data['amount']*tax_data['tax_sign']*value['base_amount'],2)
            tax_grouped[key]['tax_amount']=round(tax_data['amount']*tax_data['tax_sign']*value['base'],2)
        """
        """
        print "2 **************************************"
        for key,value in tax_grouped.iteritems():
            print 'tax_code_id',key[0]
            print 'base_code_id',key[1]
            print 'account_id',key[2]
            for i,j in value.iteritems():
                print "  ",i,j
        """
        
        return tax_grouped2

    """
    def move_line_get(self, cr, uid, invoice_id):
        res = []
        cr.execute('SELECT * FROM account_invoice_tax WHERE invoice_id=%d', (invoice_id,))
        for t in cr.dictfetchall():
            res.append({
                'type':'tax',
                'name':t['name'],
                'price_unit': t['amount'],
                'quantity': 1,
                'price': t['amount'] or 0.0,
                'account_id': t['account_id'],
                'tax_code_id': t['tax_code_id'],
                'tax_amount': t['tax_amount']
            })
        return res
    """

account_invoice_tax()
