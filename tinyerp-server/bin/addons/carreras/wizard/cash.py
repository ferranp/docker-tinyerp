# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: cash.py 1070 2005-07-29 12:41:24Z nicoe $
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
  Generar factures 
"""
import wizard
import netsvc
import pooler

cash_form = '''<?xml version="1.0"?>
<form string="Albarà de Comptat">
    <separator string="Facturar el Full de Ruta i imprimir l'Albarà de comptat?" colspan="4"/>
    <field name="discount" />
</form>'''

credit_form = '''<?xml version="1.0"?>
<form string="Albarà de Crèdit">
    <separator string="Generar i imprimir l'Albarà?" colspan="4"/>
</form>'''

credit_fields = {}
cash_fields = {
    'discount': {'string': 'Aplicar 3% de Descompte de Comptat', 'type': 'boolean'},    
}

class cash(wizard.interface):

    def check_risc(self,cr,uid,partner,company_id):
        if not partner.credit_limit:
            return 
        risc=pooler.get_pool(cr.dbname).get('res.partner').browse(cr,uid,partner.id).risk
        if risc <= partner.credit_limit:
            return 
        raise wizard.except_wizard(
                "Document bloquejat",
                "El client supera el crèdit permes")
        return

    def check_msg(self,cr,uid,partner):
        if not partner.message:
            return
        if not partner.message.block:
            return
        raise wizard.except_wizard(
                "Document bloquejat",partner.message.name
                )
        return

    def _credit_process(self, cr, uid, data, context):
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', data['id'], 'order_confirm', cr)
        return {}

    def _cash_process(self, cr, uid, data, context):
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'sale.order', data['id'], 'order_confirm', cr)
        so_obj=pooler.get_pool(cr.dbname).get('sale.order')
        if data['form']['discount']:
            so_obj.write(cr,uid,data['id'],{'cash_discount':3.0})
        so_obj.action_invoice_create(cr, uid, [data['id']], True)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', data['id'], 'manual_invoice', cr)        
        return {}

    def _test_cash(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
	so_obj=pool.get('sale.order')
        so = so_obj.browse(cr,uid,data['id'])
	so_obj._check_risc(cr,uid,[so.id])
	so_obj._check_msg(cr,uid,[so.id])
        #self.check_msg(cr,uid,so.customer_id.partner_id)
        #self.check_risc(cr,uid,so.customer_id.partner_id,so.customer_id.company_id.id)
        if not so.customer_id or so.customer_id.name[1:4] != "000":
            return 'credit_question_raw'
            if so.line_type == 'VA':
                return 'credit_question_va'
            if so.line_type == 'RE':
                return 'credit_question_re'
            return 'credit_question'
        return 'cash_question_raw'
        if so.line_type == 'VA':
            return 'cash_question_va'
        if so.line_type == 'RE':
            return 'cash_question_re'
        return 'cash_question'

    def _print_raw_so(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        if not user.raw_printer:
            raise wizard.except_wizard(
                "No es pot imprimir l'albarà",
                "L'usuari no té assignada cap impressora d'agulles")
        return {'ids' : data['ids'], 
                'print_batch':True,
                'printer' : user.raw_printer.id,
                }

    states = {
        'init': {
            'actions': [],
            'result': {'type':'choice', 'next_state':_test_cash}
            },
            
        'cash_question': {
            'actions': [],
            'result': {'type':'form', 'arch':cash_form, 'fields':cash_fields,'state':[('end','Cancel·la'),('cash_process',"D\'acord")]}
            },
        'cash_question_re': {
            'actions': [],
            'result': {'type':'form', 'arch':cash_form, 'fields':cash_fields,'state':[('end','Cancel·la'),('cash_process_re',"D\'acord")]}
            },
        'cash_question_va': {
            'actions': [],
            'result': {'type':'form', 'arch':cash_form, 'fields':cash_fields,'state':[('end','Cancel·la'),('cash_process_va',"D\'acord")]}
            },
        'cash_question_raw': {
            'actions': [],
            'result': {'type':'form', 'arch':cash_form, 'fields':cash_fields,'state':[('end','Cancel·la'),('cash_process_raw',"D\'acord")]}
            },
        'credit_question': {
            'actions': [],
            'result': {'type':'form', 'arch':credit_form, 'fields':credit_fields,'state':[('end','Cancel·la'),('credit_process',"D\'acord")]}
            },
        'credit_question_re': {
            'actions': [],
            'result': {'type':'form', 'arch':credit_form, 'fields':credit_fields,'state':[('end','Cancel·la'),('credit_process_re',"D\'acord")]}
            },
        'credit_question_va': {
            'actions': [],
            'result': {'type':'form', 'arch':credit_form, 'fields':credit_fields,'state':[('end','Cancel·la'),('credit_process_va',"D\'acord")]}
            },
        'credit_question_raw': {
            'actions': [],
            'result': {'type':'form', 'arch':credit_form, 'fields':credit_fields,'state':[('end','Cancel·la'),('credit_process_raw',"D\'acord")]}
            },
            
        'cash_process': {
            'actions': [],
            'result': {'type':'action','action':_cash_process,'state':'cash_print'}
            },
        'cash_process_re': {
            'actions': [],
            'result': {'type':'action','action':_cash_process,'state':'cash_print_re'}
            },
        'cash_process_va': {
            'actions': [],
            'result': {'type':'action','action':_cash_process,'state':'cash_print_va'}
            },
        'cash_process_raw': {
            'actions': [],
            'result': {'type':'action','action':_cash_process,'state':'print_raw'}
            },
        'credit_process': {
            'actions': [],
            'result': {'type':'action','action':_credit_process,'state':'print'}
            },
        'credit_process_re': {
            'actions': [],
            'result': {'type':'action','action':_credit_process,'state':'print_re'}
            },
        'credit_process_va': {
            'actions': [],
            'result': {'type':'action','action':_credit_process,'state':'print_va'}
            },
        'credit_process_raw': {
            'actions': [],
            'result': {'type':'action','action':_credit_process,'state':'print_raw'}
            },
            
        'print': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.shipping',
                        'state' : 'print_quality'}
            },
        'print_re': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.shipping_re',
                        'state' : 'print_quality'}
            },
        'print_va': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.shipping_va',
                        'state' : 'print_quality'}
            },
        'cash_print': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.cash',
                        'state' : 'print_quality'}
            },
        'cash_print_re': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.cash_re',
                        'state' : 'print_quality'}
            },
        'cash_print_va': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.cash_va',
                        'state' : 'print_quality'}
            },
        'print_quality': {
            'actions': [],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.shipping_quality',
                        'state' : 'end'}
            },
        'print_raw': {
            'actions': [_print_raw_so],
            'result' : {'type' : 'print',
                        'report' : 'sale.order.print_raw',
                        'get_id_from_action':True,
                        'state' : 'end'}
            },
        }
cash("carreras.cash")
