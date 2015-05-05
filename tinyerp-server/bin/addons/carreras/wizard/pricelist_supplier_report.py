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
  Llistat de Tarifes de Compres
"""
import time
import wizard
import pooler 

select_form = '''<?xml version="1.0"?>
<form string="Llistat de Tarifes de Compres">
    <field name="company_id" colspan="4" />
    <field name="family1" />
    <label string="-" />
    <field name="family2" nolabel="1"/>
    <newline />
    <field name="department1" />
    <label string="-" />
    <field name="department2" nolabel="1"/>
    <newline />
    <field name="code1" />
    <label string="-" />
    <field name="code2" nolabel="1"/>
    <newline />
    <field name="actual" colspan="4"/>
    <newline />
    <field name="order" colspan="4"/>
</form>'''


select_fields = {
    'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company','readonly': True,},
    #'company_id': {'string': 'Empresa','type': 'many2one','relation': 'res.company',},
    'family1': {'string': 'Families entre','type': 'char',},
    'family2': {'string': '-','type': 'char',},
    'department1': {'string': 'Departaments entre','type': 'char',},
    'department2': {'string': '-','type': 'char',},
    'code1': {'string': 'Codis dels productes entre','type': 'char',},
    'code2': {'string': '-','type': 'char',},
    'actual': {'string': 'Només preus vigents','type': 'boolean',},
    'order': {'string': 'Ordre','type': 'selection','size':10,'selection':[('family_id','Família'),('department_id','Departament')]},
}

class wizard_report(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        data['form']['company_id'] = user['company_id'][0]
        data['form']['actual'] = True
        data['form']['order'] = 'family_id'
        return data['form']

    def _select_products(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        p_s=[]
        
        s=[]
        if data['form']['family1'] and data['form']['family1'] != "":
            s.append(('name','>=',data['form']['family1']))
        if data['form']['family2'] and data['form']['family2'] != "":
            s.append(('name','<=',data['form']['family2']))
        if len(s):
            fam_ids=pool.get('product.family').search(cr,uid,s)
            if not len(fam_ids):
                raise wizard.except_wizard( 
                    "No hi ha famílies de productes en aquesta selecció",
                    'Fixeu un altre marge o en blanc per seleccionar totes les famílies')
            p_s.append(('family_id','in',fam_ids))

        s=[]
        if data['form']['department1'] and data['form']['department1'] != "":
            s.append(('name','>=',data['form']['department1']))
        if data['form']['department2'] and data['form']['department2'] != "":
            s.append(('name','<=',data['form']['department2']))
        if len(s):
            dep_ids=pool.get('product.department').search(cr,uid,s)
            if not len(dep_ids):
                raise wizard.except_wizard( 
                    "No hi ha cap departament en aquesta selecció",
                    'Fixeu un altre marge o en blanc per seleccionar tots els departaments')
            p_s.append(('department_id','in',dep_ids))

        if data['form']['code1'] and data['form']['code1'] != "":
            p_s.append(('default_code','>=',data['form']['code1']))
        if data['form']['code2'] and data['form']['code2'] != "":
            p_s.append(('default_code','<=',data['form']['code2']))

        p_s.append(('categ_id','like','Compres'))
        prod_ids = pool.get('product.product').search(cr,uid,p_s)
        if not len(prod_ids):
            raise wizard.except_wizard('No hi ha productes seleccionats amb aquests marges')
        return {'ids' : prod_ids,}

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('report','Imprimir') ]}
        },
        'report': {
            'actions': [_select_products],
            'result': {'type':'print', 
            'report':'carreras.pricelist_supplier_report', 
            'get_id_from_action':True ,
            'state':'end'}
        }
    }
wizard_report('carreras.pricelist_supplier_report')

