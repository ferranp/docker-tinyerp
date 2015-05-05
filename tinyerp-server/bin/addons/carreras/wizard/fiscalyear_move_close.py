# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import wizard
import osv
import pooler
import netsvc

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

_explo_form = '''<?xml version="1.0"?>
<form string="Explotació de l'Any">
    <field name="fy_id" domain="[('state','=','draft')]"/>
    <field name="report_name" colspan="3"/>
    <field name="report_journal" colspan="3"/>
    <separator string="Està segur ?" colspan="4"/>
    <field name="sure"/>
</form>'''
_explo_fields = {
    'fy_id': {'string':'Any Fiscal', 'type':'many2one', 'relation': 'account.fiscalyear','required':True, 'domain':[('state','=','draft')]},
    'report_name': {'string':'Descripció de les noves entrades', 'type':'char', 'size': 64, 'required':True},
    'report_journal': {'string':"Diari d'Explotació", 'type':'many2one', 'relation': 'account.journal', 'required':True},
    'sure': {'string':'Marca aquesta casella', 'type':'boolean'},
}

_close_form = '''<?xml version="1.0"?>
<form string="Tancament de l'Any">
    <field name="fy_id" domain="[('state','=','done')]"/>
    <field name="report_name" colspan="3"/>
    <field name="report_journal" colspan="3"/>
    <separator string="Està segur ?" colspan="4"/>
    <field name="sure"/>
</form>'''
_close_fields = {
    'fy_id': {'string':'Any Fiscal a tancar', 'type':'many2one', 'relation': 'account.fiscalyear','required':True, 'domain':[('state','=','draft')]},
    'report_name': {'string':'Descripció de les noves entrades', 'type':'char', 'size': 64, 'required':True},
    'report_journal': {'string':'Diari del Tancament', 'type':'many2one', 'relation': 'account.journal', 'required':True},
    'sure': {'string':'Marca aquesta casella', 'type':'boolean'},
}

_open_form = '''<?xml version="1.0"?>
<form string="Obertura de l'Any">
    <field name="fy_id" domain="[('state','=','draft')]"/>
    <field name="fy2_id" domain="[('state','=','draft')]"/>
    <field name="report_name" colspan="3"/>
    <field name="report_journal" colspan="3"/>
    <separator string="Està segur ?" colspan="4"/>
    <field name="sure"/>
</form>'''
_open_fields = {
    'fy_id': {'string':'Any Fiscal Vell', 'type':'many2one', 'relation': 'account.fiscalyear','required':True, 'domain':[('state','=','draft')]},
    'fy2_id': {'string':'Any Fiscal Nou', 'type':'many2one', 'relation': 'account.fiscalyear', 'domain':[('state','=','draft')], 'required':True},
    'report_name': {'string':'Nom de les entrades', 'type':'char', 'size': 64, 'required':True},
    'report_journal': {'string':"Diari d'Obertura", 'type':'many2one', 'relation': 'account.journal', 'required':True},
    'sure': {'string':'Marqui aquesta casella', 'type':'boolean'},
}

end_form = '''<?xml version="1.0"?>
<form string="Traspàs">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''
end_fields = {}

def _explo_data_save(self, cr, uid, data, context):
    if not data['form']['sure']:
        raise wizard.except_wizard('Explotació de l\'any fiscal cancel·lada', 'Marqui la casella !')
    pool = pooler.get_pool(cr.dbname)
    aml_obj=pool.get('account.move.line')

    fy_id = data['form']['fy_id']
    fiscalyear=pool.get('account.fiscalyear').browse(cr, uid, fy_id)
    period =fiscalyear.period_ids[11]

    user = pool.get('res.users').browse(cr,uid,uid)
    cr.execute("select id from account_account WHERE active and substr(code,1,1) in ('6','7') and company_id = '%d'" \
        % user.company_id.id)
    
    ids = map(lambda x: x[0], cr.fetchall())
    reconcile_ids=[]
    for account in pool.get('account.account').browse(cr, uid, ids, {'fiscalyear':fy_id}):
        if account.type == 'view':
            continue
        print account.code

        # Es fa un unic moviment per cada compte
        if abs(account.balance)>0.0001:
            aml_id=pool.get('account.move.line').create(cr, uid, {
                'debit': account.balance<0 and -account.balance or 0,
                'credit': account.balance>0 and account.balance or 0,
                'name': data['form']['report_name'],
                'date': period.date_stop,
                'journal_id': data['form']['report_journal'],
                'period_id': period.id,
                'account_id': account.id
            }, {'journal_id': data['form']['report_journal'], 'period_id':period.id})

            if account.reconcile:
                reconcile_ids.append(aml_id)
    
    r_id = pool.get('account.move.reconcile').create(cr, uid, {
        'name': fiscalyear.code, 
        'type': 'auto', 
        'line_id': map(lambda x: (4,x,False), reconcile_ids)
    })
    wf_service = netsvc.LocalService("workflow")
    for id in ids:
        wf_service.trg_trigger(uid, 'account.move.line', id, cr)
    return {}

def _close_data_save(self, cr, uid, data, context):
    if not data['form']['sure']:
        raise wizard.except_wizard('Tancament de l\'any fiscal cancel·lat', 'Marqui la casella !')
    pool = pooler.get_pool(cr.dbname)
    aml_obj=pool.get('account.move.line')

    fy_id = data['form']['fy_id']
    fiscalyear=pool.get('account.fiscalyear').browse(cr, uid, fy_id)
    period =fiscalyear.period_ids[11]
    user = pool.get('res.users').browse(cr,uid,uid)
    cr.execute("select id from account_account WHERE active and company_id = '%d'" % user.company_id.id)
    
    ids = map(lambda x: x[0], cr.fetchall())
    reconcile_ids=[]
    for account in pool.get('account.account').browse(cr, uid, ids, {'fiscalyear':fy_id}):
        if account.close_method=='none' or account.type == 'view':
            continue

        # Es fa un unic moviment per cada compte
        print account.code
        if abs(account.balance)>0.0001:
            aml_id=pool.get('account.move.line').create(cr, uid, {
                'debit': account.balance<0 and -account.balance or 0,
                'credit': account.balance>0 and account.balance or 0,
                'name': data['form']['report_name'],
                'date': period.date_stop,
                'journal_id': data['form']['report_journal'],
                'period_id': period.id,
                'account_id': account.id
            }, {'journal_id': data['form']['report_journal'], 'period_id':period.id})
            if account.reconcile:
                reconcile_ids.append(aml_id)
    
    r_id = pool.get('account.move.reconcile').create(cr, uid, {
        'name': fiscalyear.code, 
        'type': 'auto', 
        'line_id': map(lambda x: (4,x,False), reconcile_ids)
    })
    wf_service = netsvc.LocalService("workflow")
    for id in ids:
        wf_service.trg_trigger(uid, 'account.move.line', id, cr)
    return {}

def _open_data_save(self, cr, uid, data, context):
    if not data['form']['sure']:
        raise wizard.except_wizard('Obertura de l\'any fiscal cancel·lada', 'Marqui la casella !')
    pool = pooler.get_pool(cr.dbname)

    fy_id = data['form']['fy_id']
    fiscalyear=pool.get('account.fiscalyear').browse(cr, uid, data['form']['fy2_id'])
    period = fiscalyear.period_ids[0]
    user = pool.get('res.users').browse(cr,uid,uid)
    cr.execute("select id from account_account WHERE active and company_id = '%d'" % user.company_id.id)
    ids = map(lambda x: x[0], cr.fetchall())
    reconcile_ids=[]
    for account in pool.get('account.account').browse(cr, uid, ids, {'fiscalyear':fy_id}):
        if account.close_method=='none' or account.type == 'view':
            continue
        
        print account.code
        if abs(account.balance)>0.0001:
            aml_id=pool.get('account.move.line').create(cr, uid, {
                'debit': account.balance>0 and account.balance or 0,
                'credit': account.balance<0 and -account.balance or 0,
                'name': data['form']['report_name'],
                'date': period.date_start,
                'journal_id': data['form']['report_journal'],
                'period_id': period.id,
                'account_id': account.id
            }, {'journal_id': data['form']['report_journal'], 'period_id':period.id})
            if account.reconcile:
                reconcile_ids.append(aml_id)
    r_id = pool.get('account.move.reconcile').create(cr, uid, {
        'name': fiscalyear.code, 
        'type': 'auto', 
        'line_id': map(lambda x: (4,x,False), reconcile_ids)
    })
    wf_service = netsvc.LocalService("workflow")
    for id in ids:
        wf_service.trg_trigger(uid, 'account.move.line', id, cr)
    cr.execute('update account_journal_period set state=%s where period_id in (select id from account_period where fiscalyear_id=%d)', ('done',fy_id))
    cr.execute('update account_period set state=%s where fiscalyear_id=%d', ('done',fy_id))
    cr.execute('update account_fiscalyear set state=%s where id=%d', ('done',fy_id))
    return {}

def _explo_data_load(self, cr, uid, data, context):
    date = mx.DateTime.today()
    date = date + RelativeDateTime(years=-1) 
    data['form']['report_name'] = "Explotació de l\'Any Fiscal "+date.strftime("%Y")
    return data['form']

class wiz_journal_explo(wizard.interface):
    states = {
        'init': {
            'actions': [_explo_data_load],
            'result': {'type': 'form', 'arch':_explo_form, 'fields':_explo_fields, 'state':[('end','Cancel·la'),('close',"Procés")]}
        },
        'close': {
            'actions': [_explo_data_save],
            'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
        }
    }

def _close_data_load(self, cr, uid, data, context):
    date = mx.DateTime.today()
    date = date + RelativeDateTime(years=-1) 
    data['form']['report_name'] = "Tancament de l\'Any Fiscal "+date.strftime("%Y")
    return data['form']

class wiz_journal_close(wizard.interface):
    states = {
        'init': {
            'actions': [_close_data_load],
            'result': {'type': 'form', 'arch':_close_form, 'fields':_close_fields, 'state':[('end','Cancel·la'),('close',"Tanca l'Any")]}
        },
        'close': {
            'actions': [_close_data_save],
            'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
        }
    }

def _open_data_load(self, cr, uid, data, context):
    date = mx.DateTime.today()
    data['form']['report_name'] = "Obertura de l'Any Fiscal " + date.strftime("%Y")
    return data['form']

class wiz_journal_open(wizard.interface):
    states = {
        'init': {
            'actions': [_open_data_load],
            'result': {'type': 'form', 'arch':_open_form, 'fields':_open_fields, 'state':[('end','Cancel'),('close',"Obre l'Any")]}
        },
        'close': {
            'actions': [_open_data_save],
            'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
        }
    }

wiz_journal_explo('account.fiscalyear.move.explo')
wiz_journal_close('account.fiscalyear.move.close')
wiz_journal_open('account.fiscalyear.move.open')
