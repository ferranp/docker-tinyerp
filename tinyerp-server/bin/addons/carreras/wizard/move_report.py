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
  Llistat d'assentaments
"""
import time
import wizard
import pooler 

dates_form = '''<?xml version="1.0"?>
<form string="Llistat d'assentaments">
    <field name="company_id" colspan="4"/>
    <field name="fiscalyear" colspan="4"/>
    <field name="move_start"/>
    <field name="move_end"/>
    <field name="date_start"/>
    <field name="date_end"/>
</form>'''

dates_fields = {
    'company_id': {'string': 'Empresa', 'type': 'many2one', 'relation': 'res.company', 'readonly': True},    
    'move_start': {'string': 'Assentament desde', 'type': 'char'},
    'move_end': {'string': 'Assentament fins a', 'type': 'char'},
    'date_start': {'string': 'Data desde', 'type': 'date'},
    'date_end': {'string': 'Data fins a', 'type': 'date'},
    'fiscalyear': {'string':'Any Fiscal','type':'many2one','relation': 'account.fiscalyear','required':True},
}

class wizard_report1(wizard.interface):
    def _get_defaults(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']
        data['form']['fiscalyear']= pool.get('account.fiscalyear').find(cr, uid, exception=False)
        return data['form']

    def _get_moves(self, cr, uid, data, context):
        form=data['form']
        if  (not form['date_start'] or not form['date_end']) and \
            (not form['move_start'] or not form['move_end']):
            raise wizard.except_wizard(
                "No es pot generar el llistat",
                "S'ha d'informar els límits de dates o d'assentaments")

        pool = pooler.get_pool(cr.dbname)
        ctx={}
        ctx['fiscalyear'] = form['fiscalyear']
        query = pool.get('account.move.line')._query_get(cr, uid, context=ctx)
        if form['date_start'] and form['date_end']:
            query = "%s and l.date between '%s' and '%s'" % (query,form.get('date_start'),form.get('date_end'))
        if form['move_start'] and form['move_end']:
            move_obj=pool.get('account.move')
            s=[]
            s.append(('name','>=',form['move_start']))
            s.append(('name','<=',form['move_end']))
            ids=move_obj.search(cr,uid,s)
            move_set = ",".join(map(str, ids))
            if move_set:
                query = "%s and l.move_id IN (%s)" % (query,move_set)
            else:
                query = "%s and false" % query

        query=  "SELECT l.move_id FROM account_move_line l WHERE %s GROUP BY l.move_id" % (query)
        cr.execute(query)
        data['form']['ids']=map(lambda x: x[0],cr.fetchall())
        return data['form']

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('report','Imprimir')]}
        },
        'report': {
            'actions': [_get_moves],
            'result': {'type':'print', 'report':'move.report', 'get_id_from_action':True ,'state':'end'}
        }
    }

wizard_report1('move.report')


