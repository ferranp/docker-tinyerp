# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: make_invoice.py 1070 2005-07-29 12:41:24Z nicoe $
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
  Imprimir Rebuts en Impressor d'Agulles
"""
import wizard
import netsvc
import pooler

class wizard_print_receivable(wizard.interface):

    def _print_rec(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        if not user.raw_printer:
            raise wizard.except_wizard(
                "No es pot imprimir l'efecte",
                "L'usuari no té assignada cap impressora d'agulles")
        return {'ids' : data['ids'], 
                'print_batch':True,
                'printer' : user.raw_printer.id,
                }

    states = {
        'init': {
            'actions': [_print_rec],
            'result' : {
                'type' : 'print',
                'report' : 'print.receivable',
                'get_id_from_action':True,
                'state' : 'end'}
        },
    }
    
wizard_print_receivable("print.receivable")
