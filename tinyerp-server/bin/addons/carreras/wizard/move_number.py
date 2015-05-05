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
  Renumerar assentaments

"""
import time
import wizard
import netsvc
import pooler 

dates_form = '''<?xml version="1.0"?>
<form string="Renumerar assentaments">
    <separator string="Es renumeraran els assentaments de l'empresa i any seleccionats" colspan="4"/>
    <field name="company_id" colspan="4"/>
    <field name="fiscalyear_id" colspan="4"/>
</form>'''

dates_fields = {
    'company_id': {
        'string': 'Empresa',
        'type': 'many2one',
        'relation': 'res.company',
        'readonly': True,
    },
    'fiscalyear_id': {
        'string': 'Any Fiscal',
        'type': 'many2one',
        'relation': 'account.fiscalyear',
        'required': True,
    },
}
dates2_form = '''<?xml version="1.0"?>
<form string="Renumerar assentaments">
    <separator string="Procés finalitzat" colspan="4"/>
</form>'''

dates2_fields = {
}


class wizard_move_number(wizard.interface):

    def _get_defaults(self, cr, uid, data, context):

        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id']

        year = pool.get('account.fiscalyear').find(cr,uid)
        data['form']['fiscalyear_id'] = year 
        
        return data['form']

    def _move_number(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        form = data['form']
        s = [('fiscalyear_id','=',form['fiscalyear_id'])]
        p_ids = pool.get('account.period').search(cr,uid,s)
        if not p_ids:
            return []
        periods = ",".join(map(lambda p: str(p) ,p_ids))
        sql = "select m.name,m.id from account_move m ,account_move_line l "+ \
              "where m.id = l.move_id and m.period_id in (%s) and " +\
              " m.company_id=%d group by m.name,m.id "+\
              "order by max(l.date),m.name,m.id"
        
        m_obj = pool.get('account.move')
        
        cr.execute(sql % (periods,form['company_id']))
        i = -1
        for i,move in enumerate(cr.fetchall()):
            num = "%06d" % (i + 1)
            if num != move[0]:
                #print move[0] , num , '*'
                m_obj.write(cr,uid, [move[1]] , {'name':num})
            else:
	        pass
                #print move[0] , num
        # Modificar numerador
        i = i + 2
        print(" Proxim numero %d" % i)
        # busco la sequencia al journl
        s = [('company_id','=',form['company_id'])]
        j_ids = pool.get('account.journal').search(cr,uid,s)
        if j_ids:
            journal = pool.get('account.journal').read(cr,uid,j_ids[0],['sequence_id'])
            seq_id = journal['sequence_id'][0]
            pool.get('ir.sequence').write(cr,uid,[seq_id],{'number_next' : i})
        return {}

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancelar'),('number','Renumerar')]}
        },
        'number': {
            'actions': [_move_number], 
            'result': {'type':'form', 'arch':dates2_form, 'fields':dates2_fields, 'state':[('end','Tancar')]}
        }
    }

wizard_move_number('carreras.move_number')

