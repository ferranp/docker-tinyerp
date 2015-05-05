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
Llistat d'efectes

"""
import time
import wizard
import pooler 

form = '''<?xml version="1.0"?>
<form string="Llistat d'efectes">
    <separator colspan="4" string="Límits de la Selecció" />
    <field name="company_id" colspan="4"/>
    <field name="customer_id_1"/>
    <field name="customer_id_2"/>
    <newline/>
    <field name="date_min" />
    <field name="date_max" />
    <field name="venc_min" />
    <field name="venc_max" />
    <newline/>
    <field name="type"/>
    <field name="state"/>
    <field name="unpaid"/>
    <field name="morositat"/>
</form>'''

fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company','required':True},
    'customer_id_1': {'string': 'De Codi de Client', 'type': 'char',},
    'customer_id_2': {'string': 'A Codi de Client', 'type': 'char',},
    'date_min': {'string': 'De la Data Factura', 'type': 'date'},
    'date_max': {'string': 'A la Data Factura', 'type': 'date'},
    'venc_min': {'string': 'Del Venciment', 'type': 'date'},
    'venc_max': {'string': 'Al Venciment', 'type': 'date'},
    'state': {'string':'Estat','type':'selection','size':10,'selection':[('all',''),('draft','Esborrany'),('pending','Pendent'),('posted','Remesat'), ('received','Cobrat')]},
    'type': {'string': "Tipus", 'type': 'selection', 'size':10, 'selection':[]},
    'unpaid': {'string': "Impagat", 'type': 'selection', 'size':10, 'selection':[('all',''),('normal','Normal'),('unpaid','Impagat')]},
    'morositat': {'string': "Morositat", 'type': 'selection', 'size':10, 'selection':[('all',''),('normal','Normal'), ('moros','Morós')]},
}

class wizard_receivables_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        obj = pool.get('account.payment.term.type')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        res = [(r['code'], r['name']) for r in res]
        fields['type']= {'string': "Tipus", 'type': 'selection', 'size':10, 'selection':res}
        
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]
        
        data['form']['state'] = 'pending'
        data['form']['unpaid'] = 'normal'
        data['form']['morositat'] = 'normal'
        return data['form']

    def _get_selection_ids(self, cr, uid, data, context):
        form = data['form']
        pool = pooler.get_pool(cr.dbname)
        ids = pool.get('res.company')._get_company_children(cr,uid,form['company_id'])
        s=[('company_id','in',ids)]
        if form['type']:
            s.append(('type','=',form['type']))
        if form['state']!='all':
            s.append(('state','=',form['state']))
        if form['unpaid']!='all':
            s.append(('unpaid','=',form['unpaid']))
        if form['morositat']!='all':
            s.append(('morositat','=',form['morositat']))
        if form['date_min']:
            s.append(('date','>=',form['date_min']))
        if form['date_max']:
            s.append(('date','<=',form['date_max']))
        if form['venc_min']:
            s.append(('date_maturity','>=',form['venc_min']))
        if form['venc_max']:
            s.append(('date_maturity','<=',form['venc_max']))

        if form['customer_id_1'] and not form['customer_id_2']:
            form['customer_id_2'] =  form['customer_id_1']
        if form['customer_id_1'] and form['customer_id_2']:
            sql = "select partner_id from res_partner_customer "+\
                " where name between '%s' and '%s'" % (form['customer_id_1'],form['customer_id_2'])
            cr.execute(sql)
            ids = [ x[0] for x in cr.fetchall() ]
            s.append(('partner_id','in',ids))
        ids=pool.get('account.receivable').search(cr,uid,s)
        data['form']['ids']=ids
        data['ids']=ids
        return data['form']

    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.receivable', 'tree'))
        view_res = cr.fetchone()

        ids=self._get_selection_ids(cr, uid, data, context)['ids']
        
        domain = "[('id','in',%s)]" % str(ids)
        return {
            'name': 'Efectes seleccionats',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.receivable',
            'view_id': view_res,
            'domain': domain,
            'context': {},
            'type': 'ir.actions.act_window'
        }
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancelar'),('view','Veure'),('report','Imprimir') ]}
        },
        'view': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        },
        'report': {
            'actions': [_get_selection_ids],
            'result': {'type':'print','report':'receivables.report', 'get_id_from_action':True, 'state':'end'}
        }
    }
wizard_receivables_report('receivables.report')

