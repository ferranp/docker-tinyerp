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
  Generar factures amb batch
"""
import wizard
import netsvc
import pooler


class print_delivery(wizard.interface):

    def _test_cash(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        so = pool.get('sale.order').browse(cr,uid,data['id'])
        if so.state in ['draft','invoice_except','cancel']:
            raise wizard.except_wizard(
                'Impressió cancel·lada', 
                ("El Full de Ruta %s no té albarà." % so.name))
        
        if not so.customer_id or so.customer_id.name[1:4] != "000":
            return 'print_raw'
            if so.line_type == 'VA':
                return 'print_va'
            if so.line_type == 'RE':
                return 'print_re'
            return 'print'

        if so.state in ['manual']:
            raise wizard.except_wizard(
                'Impressió cancel·lada', 
                ("El Full de Ruta %s no està facturat." % so.name))
                
        return 'print_raw'
        if so.line_type == 'VA':
            return 'cash_print_va'
        if so.line_type == 'RE':
            return 'cash_print_re'
        return 'cash_print'

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
print_delivery("carreras.print_delivery")

