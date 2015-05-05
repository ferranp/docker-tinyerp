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

import time
import wizard
import pooler
import netsvc

"""
    wizard_report
    wizard_report2 -> no es fa servir
    wizard_report3
"""

select_form = '''<?xml version="1.0"?>
<form string="Extracte de comptes">
    <field name="company_id" colspan="4"/>
    <field name="account_id" colspan="4"/>
    <field name="fiscalyear_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" />
</form>'''

select_fields = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'account_id': {'string': 'Compte','type': 'many2one','relation': 'account.account','required': True,'domain': [('type','<>','view')],},
    'fiscalyear_id': {'string': 'Any Fiscal','type': 'many2one','relation': 'account.fiscalyear','required': True,},
    'date_start': {'string': 'Data desde','type': 'date','required': True,},
    'date_end': {'string': 'Data fins a','type': 'date','required': True,},
}

select_form2 = '''<?xml version="1.0"?>
<form string="Extracte de comptes">
    <field name="company_id" colspan="4"/>
    <field name="account_1"/>
    <field name="account_2" nolabel="1"/>
    <field name="fiscalyear_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" nolabel="1" />
    <field name="entries" />
</form>'''

select_fields2 = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'account_1': {'string': 'Comptes entre', 'type': 'char', 'size': 10,'required': True,},
    'account_2': {'string': 'Compte', 'type': 'char', 'size': 10,'required': True,},
    'fiscalyear_id': {'string': 'Any Fiscal','type': 'many2one','relation': 'account.fiscalyear','required': True,},
    'date_start': {'string': 'Venciment entre','type': 'date','required': True,},
    'date_end': {'string': 'Data fins a','type': 'date','required': True,},
    'entries': {'string': 'Entrades','type': 'selection','size': 10,'selection':[('all','Totes'),('no','No Conciliades')],},
}

select_form3 = '''<?xml version="1.0"?>
<form string="Pagaments Pendents">
    <field name="company_id" colspan="4"/>
    <field name="fiscalyear_id" colspan="4"/>
    <field name="account_1"/>
    <field name="account_2" nolabel="1"/>
    <field name="date_1" />
    <field name="date_2" nolabel="1" />
    <field name="import_1" />
    <field name="import_2" nolabel="1" />
    <!--
        <field name="entries" />
        <field name="type" nolabel="1"/>
    -->
    <field name="type"/>
    <newline />
    <field name="order"/>
    <field name="channel_id" colspan="4"/>
</form>'''

select_fields3 = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'fiscalyear_id': {'string': 'Any Fiscal','type': 'many2one','relation': 'account.fiscalyear','required': True,},
    'account_1': {'string': 'Comptes entre', 'type': 'char', 'size': 10,'required': True,},
    'account_2': {'string': 'Compte', 'type': 'char', 'size': 10,'required': True,},
    'date_1': {'string': 'Venciment entre','type': 'date','required': True,},
    'date_2': {'string': 'Data fins a','type': 'date','required': True,},
    'import_1': {'string': 'Import entre','type': 'float'},
    'import_2': {'string': 'Import','type': 'float'},
    'entries': {'string': 'Entrades','type': 'selection','size': 10,'selection':[('all','Totes'),('no','No Conciliades')],},
    'type': {'string': 'Entrades','type': 'selection','size': 10,'selection':[('S','Saldo'),('C','Càrrec'),('A','Abonament')],},
    'order': {'string': 'Ordre','type': 'selection','size': 10,'selection':[('V','Venciment'),('C','Compte'),('I','Import')],},
    'channel_id': {'string': 'Canal de Pagament','type': 'many2one','relation': 'account.receivable.channel'},
}

class wizard_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        
        
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        dt = time.strftime('%Y-%m-%d')
        year = pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',dt),('date_stop','>=',dt)])
        data['form']['fiscalyear_id'] = year[0]
        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')

        if data['model'] == 'account.account' and data['id']:
            data['form']['account_id'] = data['id']
        if data['model'] == 'account.account' and data['ids']:
            data['form']['account_id'] = data['ids'][0]
        return data['form']


    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        acc = pool.get('account.account').browse(cr,uid,form['account_id'])
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.move.line', 'tree'))
        view_res = cr.fetchone()
        fy = form['fiscalyear_id']
        pids = pool.get('account.period').search(cr,uid,[('fiscalyear_id','=',fy)])
        domain = [('account_id','=',form['account_id']),('period_id','in',pids)]
        domain.append(('date','>=',form['date_start']))
        domain.append(('date','<=',form['date_end']))
        return {
            'domain': str(domain),
            'name': 'Extracte de %s' % acc.code,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': view_res,
            'context': "{'account_id':%d}" % (form['account_id']),
            'type': 'ir.actions.act_window'
        }
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('view','Veure'),('report','Imprimir') ]}
        },
        'view': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.extracte', 'state':'end'}
        }
    }

class wizard_report2(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        dt = time.strftime('%Y-%m-%d')
        year = pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',dt),('date_stop','>=',dt)])
        data['form']['fiscalyear_id'] = year[0]
        data['form']['date_start'] = time.strftime('%Y-01-01')
        data['form']['date_end'] = time.strftime('%Y-12-31')
        data['form']['entries'] = 'all'

        if data['model'] == 'account.account':
            if data['id'] or data['ids']:
                acc_id=data['ids'] and data['ids'][0] or data['id']
                acc_code=pool.get('account.account').browse(cr,uid,acc_id).code
                data['form']['account_1'] = acc_code
                data['form']['account_2'] = acc_code
        #logger= netsvc.Logger()
        #logger.notifyChannel("info", netsvc.LOG_INFO,data)
        return data['form']

    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.move.line', 'tree'))
        view_res = cr.fetchone()
        fy = form['fiscalyear_id']
        
        aids = self._get_ids(cr,uid,data,context)['ids']
        pids = pool.get('account.period').search(cr,uid,[('fiscalyear_id','=',fy)])

        domain=[]
        domain.append(('account_id','in',aids))
        domain.append(('period_id','in',pids))
        domain.append(('date','>=',form['date_start']))
        domain.append(('date','<=',form['date_end']))
        if form['entries']=='no':
            domain.append(('reconcile_id','=',False))

        if form['account_1'] == form['account_2']:
            name='Extracte %s' % form['account_1']
        else:
            name='Diari %s - %s' % (form['account_1'],form['account_2'])

        return {
            'domain': str(domain),
            'name': name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': view_res,
            'type': 'ir.actions.act_window'
        }

    def _get_ids(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        s=[('code','>=',data['form']['account_1']),('code','<=',data['form']['account_2'])]
        ids = pool.get('account.account').search(cr,uid,s)
        data['form']['ids']=ids
        data['ids']=ids
        return data['form']
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form2, 'fields':select_fields2, 'state':[('end','Cancelar'),('view','Veure'),('report','Imprimir') ]}
        },
        'view': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        },
        'report': {
            'actions': [_get_ids],
            'result': {'type':'print', 'report':'account.pending.payment', 'get_id_from_action':True, 'state':'end'}
        }
    }

class wizard_report3(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        c_id = user['company_id'][0]
        data['form']['company_id'] = c_id
        dt = time.strftime('%Y-%m-%d')
        year = pool.get('account.fiscalyear').search(cr, uid, [('date_start','<=',dt),('date_stop','>=',dt)])
        data['form']['fiscalyear_id'] = year[0]
        data['form']['date_1'] = time.strftime('%Y-01-01')
        data['form']['date_2'] = time.strftime('%Y-12-31')
        data['form']['account_1'] = '40000000'
        data['form']['account_2'] = '40099999'
        data['form']['import_1'] = -1000000.0
        data['form']['import_2'] = 1000000.0
        data['form']['entries'] = 'all'
        data['form']['type'] = 'S'
        data['form']['order'] = 'V'

        """
        if data['model'] == 'account.account':
            if data['id'] or data['ids']:
                acc_id=data['ids'] and data['ids'][0] or data['id']
                acc_code=pool.get('account.account').browse(cr,uid,acc_id).code
                data['form']['account_1'] = acc_code
                data['form']['account_2'] = acc_code
        """
        #logger= netsvc.Logger()
        #logger.notifyChannel("info", netsvc.LOG_INFO,data)
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form3, 'fields':select_fields3, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [],
            'result': {'type':'print', 'report':'account.pending.payment', 'state':'end'}
        }
    }

wizard_report('carreras.account.extracte')
wizard_report3('carreras.account.pending.payment')

