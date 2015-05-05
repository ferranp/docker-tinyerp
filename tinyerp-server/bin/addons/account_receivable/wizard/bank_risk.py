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
  Risc Bancari
"""
import time
import wizard
import pooler 
from tools.misc import UpdateableStr

bank_form = '''<?xml version="1.0"?>
<form string="Risc Bancari">
    <field name="channel_id"/>
    <newline />
    <field name="detail"/>
</form>'''

bank_fields = {
    'channel_id': {
        'string': 'Banc',
        'type': 'many2one',
        'relation': 'account.receivable.channel',
    },
    'detail': {
        'string': 'Detall',
        'type': 'selection',
        'selection':(('yes','Desglossat'),('no','No Desglossat')),
        'default': 'no'
    },
}

risk_form = UpdateableStr()
risk_fields = {
    'channel_id': {
        'string': 'Banc',
        'type': 'many2one',
        'relation': 'account.receivable.channel',
        'required' : True,
        'readonly':True,
    },
    'company_id': {
        'string': 'Empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'required' : True,
        'readonly':True,
    },
}

class wizard_bank_risk(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        return data['form']

    def _open_risk(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        id = data['form']['channel_id']
        bank_obj=pool.get('account.receivable.channel')
        data['form']['company_id']= bank_obj.browse(cr,uid,id).company_id.id
        
        xml = ['<?xml version="1.0"?>',
               '<form string="Risc Bancari">',
               '<field name="company_id" colspan="4" />',
               '<field name="channel_id" colspan="4" />',
               '<group col="2" colspan="2">']
        
        r= bank_obj.get_risk_by_date(cr,uid, [id])[id]
        group=int(len(r)/2 + 0.5)
        conv=lambda x:x[8:10]+'/'+x[5:7]+'/'+x[0:4]
        for i,date in enumerate(sorted(r.keys())):
            key='row_' + str(i)
            risk_fields[key]={
                'string':conv(date),
                'type':'float',
                'readonly':'1',
                'default':r[date],
            }
            xml.append('<field name="%s"/>' % key)
            if i==group:
                xml.append('</group>')
                xml.append('<group col="2" colspan="2">')
        xml.append('</group>')
        xml.append('</form>')
        risk_form.string='\n'.join(xml)
        return data['form']

    def _action_open_receivables(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        date = time.strftime('%Y-%m-%d')
        
        bank_obj=pool.get('account.receivable.channel')
        company_id = bank_obj.browse(cr,uid,id).company_id.id
        
        s = [('state','=','received'),
            ('channel_id','=',data['form']['channel_id']),
            ('company_id','child_of',[company_id])]
        rem_ids = pool.get('account.receivable.remittance').search(cr,uid,s)
        
        s = [('remittance_id','in',rem_ids)]
        rec_obj=pool.get('account.receivable')
        rec_ids = rec_obj.search(cr,uid,s)
        ids=[]
        for rec in rec_obj.browse(cr,uid,rec_ids):
            if rec.date_risk >= date:
                ids.append(rec.id)
        
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.receivable', 'tree'))
        view_res = cr.fetchone()
        domain = "[('id','in',%s)]" % str(ids)
        return {
            'name': 'Efectes en Risc',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.receivable',
            'view_id': view_res,
            'domain': domain,
            'context': {},
            'type': 'ir.actions.act_window'
        }

    def _get_selection_ids(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        if data['form']['channel_id']:
            ids=[data['form']['channel_id']]
        else:
            ids = pool.get('account.receivable.channel').search(cr,uid,[])
        data['form']['ids']=ids
        data['ids']=ids
        return data['form']
        
    def _check_view(self, cr, uid, data, context):
        if not data['form']['channel_id']:
            raise wizard.except_wizard(
                'No es pot mostrar la selecció',
                "No s'ha seleccionat cap banc")
    
        if data['form']['detail']=='yes':
            return 'view_receivables'
        return 'view_risc'

    def _check_report(self, cr, uid, data, context):
        if data['form']['detail']=='yes':
            return 'report_receivables'
        return 'report_risc'

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':bank_form, 'fields':bank_fields, 'state':[('end','Cancelar'),('view','Veure'),('report','Imprimir')]}
        },
        'report': {
            'actions': [],
            'result': {'type':'choice', 'next_state':_check_report}
        },
        'report_risc': {
            'actions': [_get_selection_ids],
            'result': {'type':'print', 'report':'account_receivable.bank_risk', 'get_id_from_action':True, 'state':'end'}
        },
        'report_receivables': {
            'actions': [_get_selection_ids],
            'result': {'type':'print', 'report':'account_receivable.bank_risk_detail', 'get_id_from_action':True, 'state':'end'}
        },
        'view': {
            'actions': [],
            'result': {'type':'choice', 'next_state':_check_view}
        },
        'view_risc': {
            'actions': [_open_risk],
            'result': {'type':'form', 'arch':risk_form, 'fields':risk_fields, 'state':[('end','Tancar')]}
        },
        'view_receivables': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_receivables, 'state':'end'}
        },
    }
wizard_bank_risk('bank.risk')
