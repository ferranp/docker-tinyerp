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
  Balanç de sumes i saldos, balanç comptable i explotacio

"""
import time
import wizard
import pooler 

dates_form = '''<?xml version="1.0"?>
<form string="Llistat del Balanç de Sumes i Saldos">
    <field name="company_id" colspan="4"/>
    <field name="account_id" colspan="4"/>
    <field name="code_start"/>
    <field name="code_end"/>
    <field name="fiscalyear" colspan="4"/>
    <field name="date_start"/>
    <field name="date_end"/>
    <field name="detail" />
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'account_id': {'string': 'Compte', 'type': 'many2one', 'relation': 'account.account', 'required': True},
    'fiscalyear': {'string': 'Any Fiscal', 'type': 'many2one', 'relation': 'account.fiscalyear', 'required': True},
    'date_start': {'string': 'Data desde', 'type': 'date', 'required':True},
    'date_end': {'string': 'Data fins a', 'type': 'date', 'required':True},
    'code_start': {'string': 'Compte desde', 'type': 'char', 'required': True, },
    'code_end': {'string': 'Compte fins a','type': 'char','required': True, },
    'detail': {'string': 'Llistar desglos', 'type': 'boolean', 'help': 'Llistar el desglos de tots els comptes'},
}

class wizard_report1(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']
        data['form']['detail'] = True
        
        data['form']['code_start'] = '0'
        data['form']['code_end'] = '999999999'

        a_obj = pool.get('account.account')
        s = [('code','=','0')]
        a_ids = a_obj.search(cr,uid,s,context=context)
        if a_ids:
            data['form']['account_id'] = a_ids[0]
        fiscalyear_obj = pool.get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        return data['form']

    def _get_account(self, cr, uid, data, context):
        data['form']['ids'] = [ data['form']['account_id'] ]
        print data['form']
        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('report','Imprimir')]}
        },
        'report': {
            'actions': [_get_account],
            'result': {'type':'print', 'report':'carreras.balance_detail', 'get_id_from_action':True ,'state':'end'}
        }
    }

wizard_report1('carreras.balance')


dates_form = '''<?xml version="1.0"?>
<form string="Llistat del Balanç de Situació">
    <field name="company_id" colspan="4"/>
    <field name="account_id" colspan="4"/>
    <field name="fiscalyear" colspan="4"/>
    <field name="detail" />
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'account_id': {'string': 'Compte', 'type': 'many2one', 'relation': 'account.account', 'required': True},
    'fiscalyear': {'string': 'Any Fiscal', 'type': 'many2one', 'relation': 'account.fiscalyear', 'required': True},
    'periods': {'string': 'Periodes', 'type': 'many2many', 'relation': 'account.period', 'help': 'En blanc tots els periodes'},
    'date_start': {'string': 'Data desde', 'type': 'date'},
    'date_end': {'string': 'Data fins a', 'type': 'date'},
    'detail': {'string': 'Llistar desglos', 'type': 'boolean', 'help': 'Llistar el desglos de tots els comptes'},
}

class wizard_report2(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']
        data['form']['detail'] = False

        a_obj = pool.get('account.account')
        s = [('code','=','0'),('name','ilike','situac')]
        a_ids = a_obj.search(cr,uid,s,context=context)
        if a_ids:
            data['form']['account_id'] = a_ids[0]
        data['form']['fiscalyear'] = pool.get('account.fiscalyear').find(cr, uid)
        return data['form']

    def _get_account(self, cr, uid, data, context):
        data['form']['ids'] = [ data['form']['account_id'] ]
        pool = pooler.get_pool(cr.dbname)
        fiscalyear=pool.get('account.fiscalyear').browse(cr, uid,data['form']['fiscalyear'])
        data['form']['date_start']=fiscalyear.date_start
        data['form']['date_end']=fiscalyear.date_stop
        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('report','Imprimir')]}
        },
        'report': {
            'actions': [_get_account],
            'result': {'type':'print', 'report':'account.account.situation_balance', 'get_id_from_action':True ,'state':'end'}
        }
    }

wizard_report2('carreras.situation_balance')

dates_form = '''<?xml version="1.0"?>
<form string="Compte d'explotació">
    <field name="company_id" colspan="4"/>
    <field name="account_id" colspan="4"/>
    <field name="fiscalyear" colspan="4"/>
    <field name="detail" />
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'account_id': {'string': 'Compte', 'type': 'many2one', 'relation': 'account.account', 'required': True},
    'fiscalyear': {'string': 'Any Fiscal', 'type': 'many2one', 'relation': 'account.fiscalyear', 'required': True},
    'date_start': {'string': 'Data desde', 'type': 'date'},
    'date_end': {'string': 'Data fins a', 'type': 'date'},
    'periods': {'string': 'Periodes', 'type': 'many2many', 'relation': 'account.period', 'help': 'En blanc tots els periodes'},
    'detail': {'string': 'Llistar desglos', 'type': 'boolean', 'help': 'Llistar el desglos de tots els comptes'},
}

class wizard_report3(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']
        data['form']['detail'] = False

        a_obj = pool.get('account.account')
        s = [('code','=','0'),('name','ilike','Explotac')]
        a_ids = a_obj.search(cr,uid,s,context=context)
        if a_ids:
            data['form']['account_id'] = a_ids[0]
        fiscalyear_obj = pool.get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        return data['form']

    def _get_account(self, cr, uid, data, context):
        data['form']['ids'] = [ data['form']['account_id'] ]
        pool = pooler.get_pool(cr.dbname)
        fiscalyear=pool.get('account.fiscalyear').browse(cr, uid,data['form']['fiscalyear'])
        data['form']['date_start']=fiscalyear.date_start
        data['form']['date_end']=fiscalyear.date_stop
        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('report','Imprimir')]}
        },
        'report': {
            'actions': [_get_account],
            'result': {'type':'print', 'report':'account.account.situation_balance', 'get_id_from_action':True ,'state':'end'}
        }
    }

wizard_report3('carreras.account.results')
