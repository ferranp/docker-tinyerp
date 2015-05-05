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
Comissions
"""
import time
import wizard
import pooler 

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

form2 = '''<?xml version="1.0"?>
<form string="Llistat de la Liquidació">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="agent_id" colspan="4"/>
    <field name="date_start" string="Data de Liquidació" required="1"/>
    <field name="date_end" nolabel="1" required="1"/>
</form>'''


form = '''<?xml version="1.0"?>
<form string="Llistat de Comprovació de les comissions">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="agent_id" colspan="4"/>
    <field name="date_start" />
    <field name="date_end" nolabel="1" required="1"/>
    <field name="detail"/>
    <newline />
    <field name="closed"/>
</form>'''

fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company','readonly':True},
    'agent_id': {'string': 'Representant', 'type': 'many2one', 'relation': 'agent.agent'},
    'date_start': {'string': 'Data de Factura', 'type': 'date'},
    'date_end': {'string': '-', 'type': 'date'},
    'detail': {'string':'Detall','type':'selection','size':5,'selection':[('total','No'),('detail','Si')]},
    'closed': {'string':'Liquidats','type':'selection','size':5,'selection':[('all','Tots'),('closed','Liquidats'),('open','No Liquidats')]},
}

class wizard_comission_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date - RelativeDateTime(days=1)
        data['form']['date_end'] = date.strftime("%Y-%m-%d")
        data['form']['detail'] = 'total'
        data['form']['closed'] = 'all'
        return data['form']

    def _test_report(self, cr, uid, data, context):
        if data['form']['detail']=='total':
            return 'report'
        return 'report_detail'

    def _get_selection_ids(self, cr, uid, data, context):
        if data['form']['agent_id']:
            data['form']['ids']=[data['form']['agent_id']]
            return data['form']
        
        pool = pooler.get_pool(cr.dbname)
        data['form']['ids']= pool.get('agent.agent').search(cr,uid,[])
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancelar'),('detail','Imprimir') ]}
        },
        'detail': {
            'actions': [],
            'result': {'type':'choice', 'next_state':_test_report}
            },
        'report': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'comission.report', 'get_id_from_action':True, 'state':'end'}
        },
        'report_detail': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'comission.report.detail', 'get_id_from_action':True, 'state':'end'}
        },
    }
    

class wizard_close_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]
        
        date = mx.DateTime.today()
        date = date + RelativeDateTime(day=1) 
        date = date - RelativeDateTime(days=1)
        data['form']['date_end'] = date.strftime("%Y-%m-%d")
        date = date + RelativeDateTime(day=1) 
        data['form']['date_start'] = date.strftime("%Y-%m-%d")
        return data['form']

    def _get_selection_ids(self, cr, uid, data, context):
        if data['form']['agent_id']:
            data['form']['ids']=[data['form']['agent_id']]
            return data['form']
        
        pool = pooler.get_pool(cr.dbname)
        data['form']['ids']= pool.get('agent.agent').search(cr,uid,[])
        return data['form']
        
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form2, 'fields':fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'close.report', 'get_id_from_action':True, 'state':'end'}
        },
    }


wizard_comission_report('carreras.comission.report')
wizard_close_report('carreras.close.report')
