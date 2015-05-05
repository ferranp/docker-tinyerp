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

# 28.05.2009 Poder comptabilitzar efectes sense factura

"""
  Comptabilitzar un efecte

"""
import time
import wizard
import pooler 


limits_form = '''<?xml version="1.0"?>
<form string="Cobrar Efecte"> 
    <separator string="Dades per a la comptabilitzacio de l'efecte" colspan="4"/>
    <field name="date" />
    <newline/>
    <field name="name" colspan="4" />
    <field name="account_id" />
    <field name="journal_id" />
    <field name="type" />
</form>'''

limits_fields = {
    'date': {'string': 'Data comptable','type': 'date','required' : True,},
    'name': {'string': 'Text del assentament','type': 'char','size':64,'required' : True,},
    'account_id': {'string': 'Compte abonament','type': 'many2one','relation': 'account.account','domain':[('type','=','cash')],'required' : True,},
    'journal_id': {'string': 'Diari','type': 'many2one','relation': 'account.journal','required' : True,},
    'type': {'string': 'Tipus de contrapartida', 'required' : True, 'default':'detail',
            'type': 'selection','selection': (('detail','Detall'),('total','Total')),
    },
}

def view_receivables(self, cr, uid, data, context):
    return {
        'domain': "[('id','in', ["+','.join(map(str,data['ids']))+"])]",
        'name': 'Efectes Comptabilitzats',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'account.receivable',
        'view_id': False,
        'type': 'ir.actions.act_window'
    }

class wizard_receivable_post(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        # Primer miro si esta en estat pending
        pool = pooler.get_pool(cr.dbname)    
        for efecte in pool.get('account.receivable').browse(cr,uid,data['ids']):
            if efecte.state == 'draft':
                raise wizard.except_wizard("Procés cancel·lat", 
                    "Efecte %s està en estat esborrany" % efecte.name)
            if efecte.state == 'received':
                raise wizard.except_wizard("Procés cancel·lat", 
                    "Efecte %s està comptabilitzat" % efecte.name)
            if efecte.remittance_id:
                raise wizard.except_wizard("Procés cancel·lat", 
                    "Efecte %s està remesat" % efecte.name)
            if efecte.state != 'pending':
                raise wizard.except_wizard("Procés cancel·lat", 
                    "Efecte %s en estat incorrecte" % efecte.name)
        
        form = data['form']
        form['date'] = time.strftime('%Y-%m-%d')
        form['name'] = "Cobrament de l'efecte %s" % efecte.name
        
        return form

    def _write(self, cr, uid, data, context):
        form = data['form']
        pool = pooler.get_pool(cr.dbname)    
        rec_obj = pool.get('account.receivable')

        ap_obj=pool.get('account.period')
        period_id = ap_obj.find(cr, uid, form['date'])[0]
        period= ap_obj.browse(cr, uid, period_id)
        #period_ids= ap_obj.get_fiscalyear_periods(cr,uid,period.fiscalyear_id.id)
        
        journal = pool.get('account.journal').browse(cr, uid, form['journal_id'])
        if not journal.sequence_id:
            raise wizard.except_wizard('No es poden comptabilitzar els efectes',
                "El diari '%s' no té cap numerador definit" % journal.name)
        name = pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
        l = {
                'name':name,
                'journal_id': form['journal_id'],
                'period_id': period_id,
        }
        
        line_id = []
        amount = 0.0
        for rec in rec_obj.browse(cr,uid,data['ids']):
            l1={
                'name': rec.invoice_id and ("Cobrament Factura %s" % rec.invoice_id.number) or ("Cobrament Factura %s" % rec.name.rsplit('.',1)[0].replace('.','/')),
                'credit':rec.amount>0 and rec.amount or 0.0,
                'debit':rec.amount<0 and -rec.amount or 0.0,
                'account_id': rec.account_id.id,
                'partner_id': rec.invoice_id and rec.invoice_id.partner_id.id or (rec.partner_id and rec.partner_id.id or False),
                'date_maturity': rec.date_maturity,
                'date': form['date'],
                'ref': (rec.invoice_id.number or '').replace('/',''),
                'ref': (rec.invoice_id and rec.invoice_id.number or rec.name.rsplit('.',1)[0].replace('.','')).replace('/',''),
            }
            line_id.append(l1)
            amount = amount + rec.amount 
            if form['type'] == 'detail':
                line_id.append({
                    'name':form['name'],
                    'credit': l1['debit'],
                    'debit': l1['credit'],
                    'account_id': form['account_id'],
                    'partner_id': False,
                    'date': form['date'],
                    'ref': (rec.invoice_id and rec.invoice_id.number or rec.name.rsplit('.',1)[0].replace('.','')).replace('/',''),
                    #'partner_id': rec.invoice_id.partner_id.id,
                })
        
        if form['type'] != 'detail':
            line_id.append({
                'name':form['name'],
                'credit': amount<0 and -amount,
                'debit': amount>0 and amount,
                'account_id': form['account_id'],
                'partner_id': False,
                'date': form['date'],
            })
        
        # create the new move and its 2 (or 4) lines
        move = l.copy()
        move['line_id'] = [(0, 0, l) for l in line_id]
        move_id = pool.get('account.move').create(cr, uid, move)
        # conciliacio
        reconcile_ids=[]
        line_ids = pool.get('account.move.line').search(cr,uid,[('move_id','=',move_id)])
        for lin in pool.get('account.move.line').browse(cr,uid,line_ids):
            if lin.account_id.reconcile:
                limits=[]
                limits.append(('account_id','=',lin.account_id.id))
                limits.append(('reconcile_id','=',False))
                limits.append(('date_maturity','=',lin.date_maturity))
                limits.append(('credit','=',lin.debit))
                limits.append(('debit','=',lin.credit))
                #limits.append(('period_id','in',period_ids))
                lin2 = pool.get('account.move.line').search(cr,uid,limits)
                if len(lin2) == 1:
                    pool.get('account.move.line').reconcile(cr,uid,[lin.id,lin2[0]])
        # change transfer state and assign it its move
        rec_obj.write(cr, uid, data['ids'], {'state':'received', 'move_id': move_id})
        return {}

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form, 'fields':limits_fields, 'state':[('end','Abandonar'),('write','Comptabilitzar')]}
        },
        'write': {
            'actions': [_write],
            'result' : {'type' : 'action',
                        'action' : view_receivables,
                        'state' : 'end'}
        }
    }
wizard_receivable_post('receivable.post')

