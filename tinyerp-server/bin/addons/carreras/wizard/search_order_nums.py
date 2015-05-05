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
  Llistat de factures de clients
  Es mostra l'empresa 
  Es seleccionen els limits
"""
import time
import wizard
import pooler 


limits_form = '''<?xml version="1.0"?>
<form string="Cerca de números de Fulls de Ruta">
    <field name="company_id" colspan="4"/>
    <field name="num_start" />
    <field name="num_end" nolabel="1"/>
</form>'''

search_fields = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    'num_start': {'string': 'Interval','type': 'integer','required': True,},
    'num_end': {'string': '-','type': 'integer','required': True,},
    'text_start': {'string': 'Interval','type': 'char', 'size':6},
    'text_end': {'string': '-','type': 'char', 'size':6},
    'nums': {'string': '-','type': 'text'},
}

search_form = '''<?xml version="1.0"?>
<form string="Cerca de números de Fulls de Ruta">
    <field name="company_id" colspan="4"/>
    <field name="text_start" readonly="1"/>
    <field name="text_end" readonly="1" nolabel="1"/>
    <separator string="Números Trobats" colspan="4"/>
    <label />
    <field name="nums" nolabel="1"/>
</form>'''

class wizard_search_nums(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr,uid,uid)
        data['form']['company_id'] = user.company_id.id
        return data['form']

    def _process(self,cr,uid,data,context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').browse(cr, uid, uid)
        
        form=data['form']
        form['text_start']= "%06d" % form['num_start']
        form['text_end']= "%06d" % form['num_end']
        query=  "SELECT name FROM sale_order " +\
                "WHERE company_id = '%d' AND name BETWEEN '%06d' AND '%06d'" %\
                    (form['company_id'],form['num_start'],form['num_end'])
        cr.execute(query)
        values= [ int(row[0]) for row in sorted(cr.fetchall()) ]
        form['nums']=""
        for i in range(form['num_start'],form['num_end'] + 1):
            if i in values:
                values.remove(i)
                continue
            form['nums']+= "%06d\n" % i
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':limits_form, 'fields':search_fields, 'state':[('end','Cancelar'),('search','Cerca') ]}
        },
        'search': {
            'actions': [_process],
            'result': {'type':'form', 'arch':search_form, 'fields':search_fields, 'state':[('end','Tancar')]}
        },
    }


wizard_search_nums('carreras.search_order_nums')
