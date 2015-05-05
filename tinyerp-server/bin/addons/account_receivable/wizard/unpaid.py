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
  Comtabilitzar un efecte

"""
import time
import wizard
import pooler 

import mx.DateTime

form1 = '''<?xml version="1.0"?>
<form string="Alta d'Impagats"> 
    <separator string="Dades per a la l'alta de l'impagat" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="receivable_id" />
</form>'''

form2 = '''<?xml version="1.0"?>
<form string="Alta d'Impagats"> 
    <separator string="Dades per a la l'alta de l'impagat" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="receivable_id" readonly="1"/>
    <field name="customer" readonly="1"/>
    <field name="partner_id" colspan="4" readonly="1"/>
    <separator colspan="4"/>
    <field name="name" colspan="4"/>
    <field name="journal_id" colspan="4" />
    <newline/>
    <field name="supplier_account_id" colspan="4" />
    <newline/>
    <field name="cash_account_id" colspan="4" />
    <newline/>
    <field name="expenses" />
</form>'''

fields2 = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly' : True,},
    'name': {'string': 'Text del assentament','type': 'char','size':64,},#'required' : True,},
    'date': {'string': 'Data comptable','type': 'date','required' : True,},
    'receivable_id': {'string': 'Efecte','type': 'many2one','relation': 'account.receivable','required' : True,},
    'partner_id': {'string': 'Client','type': 'many2one','relation': 'res.partner','required' : True,},
    'customer': {'string': 'Codi','type': 'char','required' : True,},
    'supplier_account_id': {'string': 'Compte de Despeses','type': 'many2one','relation': 'account.account','domain':[('type','=','payable')],'required' : True,},
    'cash_account_id': {'string': 'Compte de Caixa','type': 'many2one','relation': 'account.account','domain':[('type','=','cash')],'required' : True,},
    'journal_id': {'string': "Diari d'Impagats",'type': 'many2one','relation': 'account.journal','required' : True,},
    'expenses': {'string':"Despeses Bancàries", 'type':'float', 'digits':(16,2), },
}
fields1 = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly' : True,},
    'receivable_id': {'string': 'Efecte','type': 'many2one','relation': 'account.receivable','domain':[('state','=','received')],'required' : True,},
    #'supplier_account_id': {'string': 'Compte de Despeses','type': 'many2one','relation': 'account.account','domain':[('type','=','payable')]},
    #'cash_account_id': {'string': 'Compte de Caixa','type': 'many2one','relation': 'account.account','domain':[('type','=','cash')]},
}

def view_move(self, cr, uid, data, context):
    pool = pooler.get_pool(cr.dbname)
    rec=pool.get('account.receivable').browse(cr,uid,data['form']['receivable_id'])
    return {
        #'domain': "[('id','in', ["+','.join(map(str,data['ids']))+"])]",
        #'domain': "[('state','=','pending'),('unpaid','=', 'unpaid'),('morositat','=','normal')]",
        'domain': "[('id','in',[%d,%d])]" % (data['move_id'],rec.move_id.id),
        'name': 'Assentaments',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.move',
        #'view_id': False,
        'type': 'ir.actions.act_window'
    }
def view_unpaid(self, cr, uid, data, context):
    return {
        #'domain': "[('id','in', ["+','.join(map(str,data['ids']))+"])]",
        #'domain': "[('state','=','pending'),('unpaid','=', 'unpaid'),('morositat','=','normal')]",
        'domain': "[('id','in',[%d,%d])]" % (data['receivable_id'],data['form']['receivable_id']),
        'name': 'Efectes',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.receivable',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }

class wizard_create_unpaid(wizard.interface):
    def _set_default_company(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        form['company_id']=pool.get('res.users').browse(cr,uid,uid).company_id.id
        return form

    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        
        form['company_id']=pool.get('res.users').browse(cr,uid,uid).company_id.id
        form['date'] = time.strftime('%Y-%m-%d')
        
        rec=pool.get('account.receivable').browse(cr,uid,form['receivable_id'])
        form['name'] = "Devolució del Gir %s" % \
            mx.DateTime.strptime(rec.date_maturity, '%Y-%m-%d').strftime('%d-%m-%Y')
        form['partner_id']=rec.partner_id.id
        form['customer']=rec.partner_id.code
        if rec and rec.remittance_id and rec.remittance_id.channel_id:
            bank=rec.remittance_id.channel_id
            form['supplier_account_id']=bank.supplier_account_id and bank.supplier_account_id.id or None
            form['cash_account_id']=bank.cash_account_id and bank.cash_account_id.id or None
        form['date'] = time.strftime('%Y-%m-%d')
        
        ids= pool.get('account.journal').search(cr,uid,[('code','=','IMPG'),('company_id','=',rec.company_id.id)])
        if ids:
            form['journal_id']=ids[0]
        return form

    def _write_move(self, cr, uid, data, context):
        form = data['form']
        pool = pooler.get_pool(cr.dbname)    
        rec_obj = pool.get('account.receivable')

        journal = pool.get('account.journal').browse(cr, uid, form['journal_id'])
        if not journal.sequence_id:
            raise wizard.except_wizard('No es pot generar l\'impagat',
                "El diari '%s' no té cap numerador definit" % journal.name)
        
        ap_obj=pool.get('account.period')
        period_id = ap_obj.find(cr, uid,form['date'])[0]
        period= ap_obj.browse(cr, uid, period_id)
        period_ids= ap_obj.get_fiscalyear_periods(cr,uid,period.fiscalyear_id.id)
        
        rec= pool.get('account.receivable').browse(cr, uid,form['receivable_id'])
        
        line_id=[]
        amount=rec.amount + form['expenses']
        line_id.append({
            'name':form['name'],
            'debit': amount<0 and -amount or 0.0,
            'credit': amount>0 and amount or 0.0,
            'account_id': form['cash_account_id'],
            'partner_id': rec.partner_id and rec.partner_id.id or (rec.invoice_id and rec.invoice_id.partner_id.id),
            'date': form['date'],
            'date_maturity': rec.date_maturity,
            #'ref': rec.invoice_id and rec.invoice_id.number,
            'ref': (rec.invoice_id.number or '').replace('/',''),
        })
        if form['expenses'] != 0:
            line_id.append({
                'name':"Pagament Factura",
                'debit':form['expenses']>0 and form['expenses'] or 0.0,
                'credit':form['expenses']<0 and -form['expenses'] or 0.0,
                'account_id': form['supplier_account_id'],
                'partner_id': rec.partner_id and rec.partner_id.id or (rec.invoice_id and rec.invoice_id.partner_id.id),
                'date': form['date'],
                'ref': (rec.invoice_id.number or '').replace('/',''),
            })
        line_id.append({
            'name': form['name'],
            'debit': rec.amount>0 and rec.amount or 0.0,
            'credit': rec.amount<0 and -rec.amount or 0.0,
            'account_id': rec.account_id.id,
            #'partner_id': False,
            'partner_id': rec.partner_id and rec.partner_id.id or (rec.invoice_id and rec.invoice_id.partner_id.id),
            'date_maturity': rec.date_maturity,
            'date': form['date'],
            #'ref': rec.invoice_id and rec.invoice_id.number,
            'ref': (rec.invoice_id.number or '').replace('/',''),            
        })

        # create the new move and its 3 lines
        name = pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
        move = {
                'name':name,
                'journal_id': form['journal_id'],
                'period_id': period_id,
        }
        move['line_id'] = [(0, 0, l) for l in line_id]
        move_id = pool.get('account.move').create(cr, uid, move)
        # conciliacio
        """
        reconcile_ids=[]
        line_ids = pool.get('account.move.line').search(cr,uid,[('move_id','=',move_id)])
        
        for lin in pool.get('account.move.line').browse(cr,uid,line_ids):
            if lin.account_id.reconcile:
                limits = [('account_id','=',lin.account_id.id)]
                limits.append(('reconcile_id','=',False))
                #limits.append(('date_maturity','=',lin.date_maturity))
                limits.append(('date','=',lin.date))
                limits.append(('credit','=',lin.debit))
                limits.append(('debit','=',lin.credit))
                limits.append(('period_id','in',period_ids))
                lin2 = pool.get('account.move.line').search(cr,uid,limits)
                if len(lin2) == 1:
                    pool.get('account.move.line').reconcile(cr,uid,[lin.id,lin2[0]])
        """
        
        # change transfer state and assign it its move
        #rec_obj.write(cr, uid, data['ids'], {'state':'received', 'move_id': move_id})
        data['move_id']=move_id
        return {}

    def _write_unpaid(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        rec_obj=pool.get('account.receivable')
        rec=rec_obj.browse(cr,uid,data['form']['receivable_id'])
        pool.get('account.receivable').write(cr,uid,[rec.id],{'date_risk':None})
        
        form=data['form']
        receivable = {
            'name' : rec.name,
            'ref' : rec.ref,
            'company_id': rec.company_id.id,
            'account_id': rec.account_id.id,
            'partner_id': rec.partner_id and rec.partner_id.id,
            'state': 'pending',
            'type': rec.type,
            'date': form['date'],
            'amount': rec.amount,
            'currency_id': rec.currency_id.id,
            'expenses': form['expenses'],
            'amount_original': rec.amount,
            'invoice_id': rec.invoice_id.id,
            'date_maturity': rec.date_maturity,
            #'date_risk': ,
            'partner_id': rec.partner_id.id,
            'address_invoice_id': rec.address_invoice_id.id,
            'bank_id': rec.bank_id.id,
            #'remittance':,
            'note':rec.note,
            #'move_id':,
            'unpaid':'unpaid',
            'morositat':'normal',
            #'xec':,
            #'ccc1':,
            #'ccc2':,
            #'ccc3':,
            #'ccc4':,
        }
        id=pool.get('account.receivable').create(cr,uid,receivable)
        data['receivable_id']=id
        return {}

    states = {
        'init': {
            'actions': [_set_default_company], 
            'result': {'type':'form', 'arch':form1, 'fields':fields1, 'state':[('end','Abandonar'),('select','Selecciona')]}
        },
        'select': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form2, 'fields':fields2, 'state':[('end','Abandonar'),('unpaid','Alta')]}
        },
        'unpaid': {
            'actions': [_write_unpaid],
            'result' : {'type' : 'action',
                        'action' : view_unpaid,
                        'state' : 'move'}
        },
        'move': {
            'actions': [_write_move],
            'result' : {'type' : 'action',
                        'action' : view_move,
                        'state' : 'end'}
        },
    }
wizard_create_unpaid('create.unpaid')

