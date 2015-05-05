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
  Dades per a la generacio de la norma 58
"""
class account_receivable_norma58(osv.osv):
    _name = "account.receivable.norma58"
    _description = "Dades per a la Norma 58"
    
    _columns = {
        'name' : fields.char('Descripcio',size=64,required=True,select="1"),
        'presentador' : fields.char('NIF Presentador',size=9,required=True),
        'suf_pre' : fields.char('Sufix Presentador',size=3,required=True),
        'nom_pre' : fields.char('Nom Presentador',size=64,required=True),
        'ordenant' : fields.char('NIF Ordenant',size=9,required=True),
        'suf_ord' : fields.char('Sufix Ordenant',size=3,required=True),
        'nom_ord' : fields.char('Nom Ordenant',size=64,required=True),
        'ent_rec' : fields.char('Entitat receptora.',size=4,required=True),
        'ofi_rec' : fields.char('Oficina receptora.',size=4,required=True),
        'cod_ine' : fields.char('Codi INE',size=4,required=True),
        'bank_acc' : fields.char('Compte',size=64,required=True,help="Format xxxx.xxxx.xx.xxxxxxxxxx"),
        'ident1' : fields.char('Codi Identificació 1',size=20,required=True),
        'ident2' : fields.char('Codi Identificació 2',size=20,required=True),
    }

account_receivable_norma58()

class receivable_channel(osv.osv):
    _name = "account.receivable.channel"
    _description = "Canals de Cobrament"

    def _get_risc(self, cr, uid, ids, field_name, arg, context={}):
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        rec_obj=self.pool.get('account.receivable')
        rem_obj=self.pool.get('account.receivable.remittance')
        date = time.strftime('%Y-%m-%d')
        res = {}
        for p in self.browse(cr, uid, ids):
            risc=0
            s = [('state','=','received'),
                ('channel_id','=',p.id),
                ('company_id','child_of',[company_id])]
            rem_ids = rem_obj.search(cr,uid,s)
            s = [('remittance_id','in',rem_ids)]
            rec_ids = rec_obj.search(cr,uid,s)
            for rec in rec_obj.browse(cr,uid,rec_ids):
                if rec.date_risk >= date:
                    risc = risc + rec.amount
            res[p.id] = risc
        return res

    _columns = {
        'name' : fields.char('Descripcio',size=64,required=True,select="1"),
        'code' : fields.char('Compte Vista',size=23,select="1"),
        'company_id': fields.many2one('res.company', 'Empresa',select="1",required=True),
        'norma_58_id': fields.many2one('account.receivable.norma58', 'Norma 58',select="1",required=True),
        'days': fields.integer('Dies de risc'),
        'risk' : fields.function(_get_risc,string='Risc Total',type='float', obj=False, method=True,),
        'supplier_account_id':fields.many2one('account.account', 'Compte Proveidor',required=True, ondelete="cascade", domain=[('type','=','payable')]),
        'cash_account_id':fields.many2one('account.account', 'Compte Caixa',required=True, ondelete="cascade", domain=[('type','=','cash')]),
    }

    _order = "name,code"
    _defaults = {
    }

    def get_risk_by_date(self, cr, uid, ids, *args):
        company_id = self.pool.get('res.users').browse(cr, uid, uid).company_id.id
        rec_obj=self.pool.get('account.receivable')
        rem_obj=self.pool.get('account.receivable.remittance')
        date = time.strftime('%Y-%m-%d')
        mxdate = mx.DateTime.strptime(date, '%Y-%m-%d')
        res = {}
        for p in self.browse(cr, uid, ids):
            risc={}
            s = [('state','=','received'),
                ('channel_id','=',p.id),
                ('company_id','child_of',[company_id])]
            rem_ids = rem_obj.search(cr,uid,s)
            s = [('remittance_id','in',rem_ids)]
            rec_ids = rec_obj.search(cr,uid,s)
            for rec in rec_obj.browse(cr,uid,rec_ids):
                if rec.date_risk >= date:
                    if rec.date_risk not in risc:
                        risc[rec.date_risk]=0
                    risc[rec.date_risk] = risc[rec.date_risk] + rec.amount
            res[p.id]= risc
        return res

receivable_channel()

""" 
  Remeses de clients (remittance)
"""
class account_receivable_remittance(osv.osv):
    _name = "account.receivable.remittance"
    _description = "Remeses"

    def _get_sequence(self,cr,uid,ids):
        lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'account.remittance'),


    def _get_amount(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        id_set=",".join(map(str,ids))
        #cr.execute("SELECT s.id,COALESCE(SUM(l.amount + l.expenses),0)::decimal(16,2) AS amount FROM account_receivable_remittance s LEFT OUTER JOIN account_receivable l ON (s.id=l.remittance_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
        cr.execute("SELECT s.id,COALESCE(SUM(l.amount),0)::decimal(16,2) AS amount FROM account_receivable_remittance s LEFT OUTER JOIN account_receivable l ON (s.id=l.remittance_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
        res=dict(cr.fetchall())
        return res

    def _num_rec(self, cr, uid, ids, prop, unknow_none,unknow_dict):
        id_set=",".join(map(str,ids))
        cr.execute("SELECT s.id,count(*) FROM account_receivable_remittance s LEFT OUTER JOIN account_receivable l ON (s.id=l.remittance_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
        res=dict(cr.fetchall())
        return res

    def _get_types(self, cr, uid, context={}):
        obj = self.pool.get('account.payment.term.type')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        res = [(r['code'], r['name']) for r in res]
        return res

    def _check_company(self, cr, uid, ids):
        lines = self.browse(cr, uid, ids)
        for so in lines:
            if so.company_id.child_ids:
                return False
        return True

    _columns = {
        'name' : fields.char('Descripcio',size=64,select="1",readonly=True,states={'draft':[('readonly',False)],}),
        'company_id': fields.many2one('res.company', 'Empresa',required=True),
        'receivable_ids': fields.one2many('account.receivable','remittance_id','Efectes',readonly=True,states={'draft':[('readonly',False)]}),
        'note': fields.text('Nota'),
        'amount': fields.function(_get_amount, method=True, string='Import',select="1"),
        'num_receivables': fields.function(_num_rec, method=True, string='Numero efectes'),
        'channel_id': fields.many2one('account.receivable.channel', 'Banc'),
        'state': fields.selection([('draft','Esborrany'),('pending','Pendent'), ('received','Comptabilitzat')], 'Estat', required=True, readonly=True,select="1"),
        'date': fields.date('Data', required=True,select="1"),
        'move_id': fields.many2one('account.move', 'Assentament'),
        'type' : fields.selection(_get_types, 'Tipus',size=10, required=True,select="1"),
    }
    _order = "name,id desc"
    
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }
    _constraints = [
        (_check_company, "No es poden fer remeses a aquesta empresa", ['company_id']),
    ]

    def onchange_type(self, cr, uid, id, type, context={}):
        return {'domain':{'receivable_ids':"[('type','=',type),('state','=','pending')]"}}

    def _mark_receivables(self, cr, uid, id, receivables):
        r_obj = self.pool.get('account.receivable')
        r_ids = r_obj.search(cr,uid,[('remittance_id','=',id)])
        to_clear = []
        to_write = []
        for i in r_ids:
            if i not in receivables:
                to_clear.append(i)
        for i in receivables:
            if i not in r_ids:
                to_write.append(i)
        if len(to_clear):
            r_obj.write(cr,uid,to_clear,{'remittance_id':False})
        if len(to_write):
            r_obj.write(cr,uid,to_write,{'remittance_id':id})
        
    def write(self, cr, uid, ids, vals, context={}):
        if 'receivable_ids' in vals:
            for op,resource,receivable_ids in vals['receivable_ids']:
                if op == 6:
                    self._mark_receivables(cr, uid, ids[resource], receivable_ids)
        return super(osv.osv, self).write(cr, uid, ids, vals, context)

    def _validate_remittance(self, cr, uid, remittance, msg="No es pot crear la remesa"):
        if not remittance.company_id:
            raise osv.except_osv(msg,
                "La remesa no té cap empresa definida")
        if not remittance.company_id.remittance_sequence_id:
            raise osv.except_osv(msg,
                "L'empresa de la remesa %s no té cap numerador de remeses assignat."
                % remittance.company_id.name)
    
        for rec in remittance.receivable_ids:
            if rec.type != remittance.type:
                raise osv.except_osv(msg,
                    "Els efectes han de ser del mateix tipus que la remesa")
            ccc=""
            if rec.bank_id:
                ccc = rec.bank_id.acc_number
            else:
                if rec.partner_id:
                    par = self.pool.get('res.partner').browse(cr,uid,[rec.partner_id.id])[0]
                    if par.bank_ids and len(par.bank_ids):
                        ccc = par.bank_ids[0].acc_number
            if remittance.type != 'gir' and remittance.type != 'impagat':
                continue
            if len(ccc) == 0:
                continue
            fccc = ccc.strip().replace('.','').replace('-','')
            if len(fccc) == 20 and fccc.isdigit():
                continue
            if rec.bank_id:
                raise osv.except_osv(msg,
                                     "CCC de càrrec (%s) de l'efecte %s incorrecte" % (ccc,rec.name))
            else:
                raise osv.except_osv(msg,
                                     "CCC de càrrec (%s) del client %s incorrecte" % (ccc,rec.partner_id.code))
                
        return True

    def button_create(self, cr, uid, ids, context={}):
        for rem in self.browse(cr, uid, ids):
            self._validate_remittance(cr, uid, rem)
            rec_ids= map(lambda x: x.id, rem.receivable_ids)
            self.pool.get('account.receivable').write(cr,uid,rec_ids,{'state':'posted'})
            w ={'state':'pending'}
            if not rem.name or rem.name == "":
                w['name']=self.pool.get('ir.sequence').get_id(cr, uid, 
                    rem.company_id.remittance_sequence_id)
            self.write(cr,uid,rem.id,w)
        return True

    def button_cancel(self, cr, uid, ids, context={}):
        for rem in self.browse(cr,uid,ids):
            for e in rem.receivable_ids:
                self.pool.get('account.receivable').write(cr,uid,e.id,{'state':'pending','remittance_id':False})
        self.write(cr,uid,ids,{'state':'draft'})
        return True

    def _unmark_receivables(self, cr, uid, id):
        r_obj = self.pool.get('account.receivable')
        r_ids = r_obj.search(cr,uid,[('remittance_id','=',id)])
        r_obj.write(cr,uid,r_ids,{'state':'pending'})

    def unlink(self, cr, uid, ids):
        for id in ids:
            self._unmark_receivables(cr,uid,id)
        return super(account_receivable_remittance, self).unlink(cr, uid, ids)


account_receivable_remittance()

""" 
  Efectes de clients (receivables)
"""
class account_receivable(osv.osv):
    _name = "account.receivable"
    _description = "Efectes"

    def _get_types(self, cr, uid, context={}):
        obj = self.pool.get('account.payment.term.type')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        res = [(r['code'], r['name']) for r in res]
        return res
    
    def _get_currency(self, cr, uid, context):
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, [uid])[0]
        if user.company_id:
            return user.company_id.currency_id.id
        else:
            return pooler.get_pool(cr.dbname).get('res.currency').search(cr, uid, [('rate','=',1.0)])[0]

    _columns = {
        'name' : fields.char('Efecte',size=64,required=True,select=True),
        'ref' : fields.char('Referencia',size=64,select="1"),
        'company_id': fields.many2one('res.company', 'Empresa',select="1",required=True),
        'account_id': fields.many2one('account.account', 'Compte Comptable',select="1", required=True, ondelete="cascade", states={'reconciled':[('readonly',True)]}, domain=[('type','<>','receivable')]),
        'state': fields.selection([('draft','Esborrany'),('pending','Pendent'),('posted','Remesat'), ('received','Cobrat')], 'Estat', required=True, readonly=True, select=True),
        'type' : fields.selection(_get_types, 'Tipus',size=10, required=True,select=True),
        'date': fields.date('Data', required=True,select=True),
        'amount': fields.float('Import', digits=(16,2),select=True ),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'expenses': fields.float('Despeses', digits=(16,2), ),
        'amount_original': fields.float('Import Original', digits=(16,2), ),
        'invoice_id': fields.many2one('account.invoice', 'Factura', change_default=True),
        'date_maturity': fields.date('Venciment',required=True,select=True),
        'date_risk': fields.date('Venciment del risc'),
        'partner_id': fields.many2one('res.partner', 'Intervinent', change_default=True, readonly=True, states={'draft':[('readonly',False)]}, ),
        'address_invoice_id': fields.many2one('res.partner.address', 'Adreça de pagament', readonly=True, states={'draft':[('readonly',False)]}),
        'bank_id': fields.many2one('res.partner.bank', 'Banc de pagament'),
        'remittance_id': fields.many2one('account.receivable.remittance', 'Remesa',readonly=True),
        'note': fields.text('Nota'),
        'move_id': fields.many2one('account.move', 'Assentament',readonly=True),
        'unpaid': fields.selection([('normal','Normal'),('unpaid','Impagat')], 'Impagat', required=True, readonly=True),
        'morositat': fields.selection([('normal','Normal'), ('moros','Morós')], 'Morositat', required=True),
        'xec' : fields.char('Xec',size=20),
        'ccc1' : fields.char('Banc',size=4),
        'ccc2' : fields.char('Oficina',size=4),
        'ccc3' : fields.char('Control',size=2),
        'ccc4' : fields.char('Compte',size=10),
    }

    _order = "name,id desc"
    _defaults = {
        'name': lambda self,cr,uid,context={}: self.pool.get('ir.sequence').get(cr, uid, 'account.receivable'),
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
        'unpaid': lambda *a: 'normal',
        'morositat': lambda *a: 'normal',
        'currency_id': _get_currency,
        'amount': lambda *a: 0.0,
        'amount_original': lambda *a: 0.0,
        'expenses': lambda *a: 0.0,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
    }

    def button_create(self, cr, uid, ids, context={}):
        self.write(cr,uid,ids,{'state':'pending'})
        return True


    def onchange_invoice_id(self, cr, uid, ids, invoice_id, context={}):
        if not invoice_id:
            return {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
        v = self.onchange_partner_id(cr, uid, ids, inv.partner_id.id)['value']
        v['partner_id']=inv.partner_id.id
        return {'value':v}

    def onchange_partner_id(self, cr, uid, ids, partner_id, context={}):
        if not partner_id:
            return {}
        v={}
        p= self.pool.get('res.partner').browse(cr,uid,partner_id)
             
        if p.property_account_receivable:
            v['account_id']= p.property_account_receivable.id
        res = p.address_get(cr, uid, [partner_id],['contact'])
        if 'contact' in res:
            v['address_invoice_id']=res['contact']
        else:
            v['address_invoice_id']=res['default']
        v['bank_id']=p.bank_ids and p.bank_ids[0] and p.bank_ids[0].id
        return {'value':v}

account_receivable()

"""
   Factures.
   Afegeix funcionalitat per a crear i esborrar les efectes.

"""
class account_invoice(osv.osv):

    _name = "account.invoice"
    _inherit = "account.invoice"
    _columns = {
        'receivable_ids': fields.one2many('account.receivable', 'invoice_id', 'Efectes'),
    }

    def create_receivable(self, cr, uid, ids, *args):
        ptt_obj= self.pool.get('account.payment.term.type')
        comptat= ptt_obj.search(cr,uid,[('code','=','comptat')])[0]
        
        pt_obj= self.pool.get('account.payment.term')
        pay_comptat= pt_obj.search(cr,uid,[('type','=','comptat')])[0]
        
        #print 'Create ' + str(ids)
        for inv in self.browse(cr,uid,ids):
            #if inv.type not in ['out_invoice','out_refund']:
            if inv.type != 'out_invoice':
                continue
            #if inv.type == 'out_refund':
            #    amount_total= -inv.amount_total
            #else:
            #    amount_total= inv.amount_total
            if inv.payment_term and inv.payment_term.id != pay_comptat:
                context = {"partner_id" : inv.partner_id.id}
                dates = pt_obj.compute(cr, uid, inv.payment_term.id, \
                    inv.amount_total, date_ref=inv.date_invoice, context=context)
            else:
                dates = [ (inv.date_due,inv.amount_total) ]
            
            #print inv.date_due,dates,dates[0]
            if not inv.date_due and dates and dates[0]:
                self.write(cr,uid,inv.id,{'date_due': dates[0][0] })
            
            for i,d in enumerate(dates):
                date,amount = d
                #if inv.type == 'out_refund':
                if inv.amount_untaxed < 0:
                    type = 'abonament'
                else:
                    type = inv.payment_term and inv.payment_term.type or 'comptat'
                
                if type not in ['reposicio','comptat'] and inv.partner_id and inv.partner_id.bank_ids:
                    bank_id = inv.partner_id.bank_ids[0].id
                else:
                    bank_id = False
                
                rec = {
                    'name' : "%s.%d" % (inv.name,i + 1),
                    'ref' : inv.reference,
                    'company_id': inv.company_id and inv.company_id.id,
                    'account_id': inv.account_id and inv.account_id.id,
                    'partner_id': inv.partner_id and inv.partner_id.id,
                    'state': 'pending',
                    'type': type,
                    'amount': amount,
                    'currency_id': inv.currency_id and inv.currency_id.id,
                    'expenses': 0.0,
                    'amount_original': amount,
                    'invoice_id': inv.id,
                    #'date': time.strftime('%Y-%m-%d'),
                    'date': inv.date_invoice,
                    'date_maturity': date or inv.date_invoice,
                    #'date_risk': date,
                    'address_invoice_id': inv.address_invoice_id and inv.address_invoice_id.id,
                    'bank_id': bank_id,
                    #'remittance':
                    'note':inv.comment,
                }
                #print 'Create ' + str(inv.name)
                self.pool.get('account.receivable').create(cr,uid,rec)
            
        return True
        
    def delete_receivable(self, cr, uid, ids, *args):
        invoices = self.read(cr, uid, ids, ['receivable_ids'])
        for i in invoices:
            if len(i['receivable_ids']):
                self.pool.get('account.receivable').unlink(cr,uid,i['receivable_ids'])
        return True

    def action_move_create(self, cr, uid, ids, *args):
        self.action_number(cr,uid,ids)
        if super(account_invoice, self).action_move_create(cr, uid, ids, *args):
            return self.create_receivable(cr, uid, ids, *args)
        else:
            return False

    def action_cancel(self, cr, uid, ids, *args):
        if super(account_invoice, self).action_cancel(cr, uid, ids, *args):
            return self.delete_receivable(cr, uid, ids, *args)
        else:
            return False

account_invoice()

