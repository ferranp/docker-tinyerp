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
  Comptabilitzar una remesa
"""
import time
import wizard
import pooler 
import mx.DateTime
from decimal import Decimal

limits_form = '''<?xml version="1.0"?>
<form string="Comptabilitar remesa"> 
    <separator string="Dades per a la comptabilitzacio de la remesa" colspan="4"/>
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
    'type': {'string': 'Tipus de contrapartida','type': 'selection','selection': (('detail','Detall'),('total','Total')),'default':'detail','required' : True,},
}

class wizard_remittance_post(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        
        if len(data['ids']) > 1:
            raise wizard.except_wizard('No es poden comptabilitzar les remeses',
                "Les remeses només es poden comptabilitzar una a una")
        
        # Primer miro si esta en estat pending
        pool = pooler.get_pool(cr.dbname)    
        
        remesa = pool.get('account.receivable.remittance').browse(cr,uid,[data['id']])[0]
        if remesa.state == 'draft':
            raise wizard.except_wizard('No es pot comptabilitzar la remesa', "Remesa en estat esborrany")
        if remesa.state == 'received':
            raise wizard.except_wizard('No es pot comptabilitzar la remesa', "Remesa ja comptabilitzada")
        if remesa.state != 'pending':
            raise wizard.except_wizard('No es pot comptabilitzar la remesa', "Remesa amb estat incorrecte")
        
        form = data['form']
        form['date'] = time.strftime('%Y-%m-%d')
        form['name'] = "Cobro Remesa %s" % remesa.name
        
        return form

    def _write(self, cr, uid, data, context):
        form = data['form']
        pool = pooler.get_pool(cr.dbname)    
        rec_obj = pool.get('account.receivable')
        rem_obj = pool.get('account.receivable.remittance')

        ap_obj=pool.get('account.period')
        period_id = ap_obj.find(cr, uid,form['date'])[0]
        period= ap_obj.browse(cr, uid, period_id)
        #period_ids= ap_obj.get_fiscalyear_periods(cr,uid,period.fiscalyear_id.id)
        
        rem = rem_obj.browse(cr,uid,data['id'])
        
        #partner_id = (pay['partner_id'] or None) and pay['partner_id'][0]
        #project_id = (pay['project_id'] or None) and pay['project_id'][0]

        journal = pool.get('account.journal').browse(cr, uid, form['journal_id'])
        if not journal.sequence_id:
            raise wizard.except_wizard('No es pot comptabilitzar la remesa',
                "El diari '%s' no té cap numerador definit" % journal.name)
        # create two move lines (one for the source account and one for the destination account)
        name = pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
        line_id = []
        amount = 0.0
        for rec in rem.receivable_ids:
            l1={
                'name': rec.invoice_id and ("Cobrament Factura %s" % rec.invoice_id.number) or ("Cobrament Factura %s" % rec.name.rsplit('.',1)[0].replace('.','/')),
                'credit':rec.amount>0 and rec.amount,
                'debit':rec.amount<0 and -rec.amount,
                'account_id': rec.account_id.id,
                'partner_id': rec.partner_id and rec.partner_id.id or (rec.invoice_id and rec.invoice_id.partner_id.id or False),
                'date_maturity': rec.date_maturity,
                'date': form['date'],
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
        #for i in line_id:
        #    print i
        move = {
                'name':name,
                'journal_id': form['journal_id'],
                'period_id': period_id,
                'line_id': [(0, 0, l) for l in line_id],
        }
        move_id = pool.get('account.move').create(cr, uid, move)
        # conciliacio
        reconcile_ids=[]
        line_ids = pool.get('account.move.line').search(cr,uid,[('move_id','=',move_id)])
        for lin in pool.get('account.move.line').browse(cr,uid,line_ids):
            if lin.account_id.reconcile:
                limits = [('account_id','=',lin.account_id.id)]
                limits.append(('reconcile_id','=',False))
                limits.append(('date_maturity','=',lin.date_maturity))
                limits.append(('credit','=',lin.debit))
                limits.append(('debit','=',lin.credit))
                #limits.append(('period_id','in',period_ids))
                lin2 = pool.get('account.move.line').search(cr,uid,limits)
                if len(lin2) == 1:
                    #aml = pool.get('account.move.line').browse(cr,uid,lin2[0])
                    pool.get('account.move.line').reconcile(cr,uid,[lin.id,lin2[0]])
        
        # change transfer state and assign it its move and risk
        rem_obj.write(cr, uid, [data['id']], {'state':'received', 'move_id': move_id})
        for rec in rem.receivable_ids:
            date_risk= mx.DateTime.strptime(rec.date_maturity, '%Y-%m-%d') + mx.DateTime.RelativeDateTime(days=rem.channel_id.days)
            rec_obj.write(cr,uid,[rec.id],{'date_risk':date_risk.strftime('%Y-%m-%d'),'move_id':move_id,'state':'received'})
        
        #cr.execute("update account_receivable set move_id=%d where remittance_id=%d"
        #        %(move_id,data['id']))
        return {}

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form, 'fields':limits_fields, 'state':[('end','Abandonar'),('write','Comptabilitzar')]}
        },
        'write': {
            'actions': [_write],
            'result': {'type':'state','state':'end' }
        }
    }
wizard_remittance_post('remittance.post')
