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
  Mostra el risc del client

"""
import time
import wizard
import netsvc
import pooler 

data_form = '''<?xml version="1.0"?>
<form string="Risc Calculat">
    <label string="Risc Calculat per l'Empresa" />
    <field name="company" colspan="4" nolabel="1"/>
    <field name="risc_alb" />
    <newline />
    <field name="risc_fac" />
    <newline />
    <field name="risc_efe" />
    <newline />
    <field name="risc_cir" />
    <newline />
    <field name="risc_imp" />
    <newline />
    <field name="risc_mor" />
    <separator colspan="4" />
    <field name="risc_total" />
    <newline />
    <field name="risc_limit" />
</form>'''

data_fields = {
    'company': {'string': 'Empresa', 'type': 'char','size':64,'readonly': True},
    'risc_alb': {'string': 'No Facturat', 'type': 'float','readonly': True},
    'risc_fac': {'string': 'Facturat', 'type': 'float','readonly': True},
    'risc_efe': {'string': 'Cartera Viva', 'type': 'float','readonly': True},
    'risc_cir': {'string': 'Circulant', 'type': 'float','readonly': True},
    'risc_imp': {'string': 'Impagat', 'type': 'float','readonly': True},
    'risc_mor': {'string': 'Morós', 'type': 'float','readonly': True},
    'risc_total': {'string': 'Risc del Client', 'type': 'float','readonly': True},
    'risc_limit': {'string': 'Límit de Crèdit', 'type': 'float','readonly': True},
}

class wizard_partner_risk(wizard.interface):

    def _get_defaults(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        partner=pool.get('res.partner').browse(cr,uid,data['id'])
        
        data['form']['company'] = user.company_id.name
        data['form']['risc_alb'] = partner.alb_risk
        data['form']['risc_fac'] = partner.fac_risk
        data['form']['risc_efe'] = partner.efe_risk
        data['form']['risc_cir'] = partner.cir_risk
        data['form']['risc_imp'] = partner.imp_risk
        data['form']['risc_mor'] = partner.mor_risk
        data['form']['risc_total'] = partner.risk
        data['form']['risc_limit'] = partner.credit_limit

        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':data_form, 'fields':data_fields, 'state':[('end','Tanca')]}
        },
    }

wizard_partner_risk('carreras.partner_risk')

