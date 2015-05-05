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

  Carrega de diaris comptables

"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega productes">
    <label string="Carrega de productes" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

class wizard_load_product(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        f = fbackup()
        
        cat_id = pool.get('product.category').search(cr,uid,[('name','=','Vendes')])
        if not cat_id:
            cat_id = pool.get('product.category').create(cr,uid,{'name':'Vendes'})
        else:
            cat_id = cat_id[0]

        cat_id = pool.get('product.category').search(cr,uid,[('name','=','Vendes - Recobriments')])
        if not cat_id:
            cat_id = pool.get('product.category').create(cr,uid,{'name':'Vendes - Recobriments'})
        else:
            cat_id = cat_id[0]

        com_id = pool.get('product.category').search(cr,uid,[('name','=','Compres')])
        if not com_id:
            com_id = pool.get('product.category').create(cr,uid,{'name':'Compres'})
        else:
            com_id = com_id[0]

        emp_ids = pool.get('res.company').search(cr,uid,[('id','>','1'),('name','not like','TT%')])
        for emp_id in emp_ids:
            # Compte de Ingressos per Vendes
            acc_id = pool.get('account.account').search(cr,uid,[('code','=','70510'),('company_id','=',emp_id)])
            print emp_id , acc_id
            if acc_id:
                acc_id = acc_id[0]
                res_id = 'product.category,%d' % cat_id
                
                d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_income_categ'),('res_id','=',res_id),('company_id','=',emp_id)])
                p = {}
                p['name']='property_account_income_categ'
                p['res_id']= res_id
                p['company_id'] = emp_id
                p['value']= 'account.account,%d' % acc_id
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_income_categ')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)

                d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_income_categ'),('res_id','=',False),('company_id','=',emp_id)])
                p = {}
                p['name']='property_account_income_categ'
                p['res_id']= False
                p['company_id'] = emp_id
                p['value']= 'account.account,%d' % acc_id
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_income_categ')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)

                d = pool.get('ir.property').search(cr,uid,[('name','=','property_stock_journal'),('res_id','=',res_id),('company_id','=',emp_id)])
                p = {}
                p['name']='property_stock_journal'
                p['res_id']= res_id
                p['company_id'] = emp_id
                p['value']= False
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_stock_journal')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)

            # Compte de Despeses per Compres
            """
            acc_id = pool.get('account.account').search(cr,uid,[('code','=','70510'),('company_id','=',emp_id)])
            print emp_id , acc_id
            if acc_id:
                acc_id = acc_id[0]
                res_id = 'product.category,%d' % cat_id
                
                d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_income_categ'),('res_id','=',res_id),('company_id','=',emp_id)])
                p = {}
                p['name']='property_account_income_categ'
                p['res_id']= res_id
                p['company_id'] = emp_id
                p['value']= 'account.account,%d' % acc_id
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_income_categ')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)

                d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_income_categ'),('res_id','=',False),('company_id','=',emp_id)])
                p = {}
                p['name']='property_account_income_categ'
                p['res_id']= False
                p['company_id'] = emp_id
                p['value']= 'account.account,%d' % acc_id
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_income_categ')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)

                d = pool.get('ir.property').search(cr,uid,[('name','=','property_stock_journal'),('res_id','=',res_id),('company_id','=',emp_id)])
                p = {}
                p['name']='property_stock_journal'
                p['res_id']= res_id
                p['company_id'] = emp_id
                p['value']= False
                p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_stock_journal')])[0]
                
                if d:
                    pool.get('ir.property').write(cr,uid,d, p)
                else:
                    pool.get('ir.property').create(cr,uid,p)
                """

        # Productes
        sel = [('name','=',"Iva suportat al 16%")]
        iva_sup = pool.get('account.tax').search(cr,uid,sel)
        sel = [('name','=',"Iva repercutit al 16%")]
        iva_rep = pool.get('account.tax').search(cr,uid,sel)

        for lin in f:
            if lin.startswith('^TTRAC("'):
                cname = lin[8:10]
                if cname not in ("BD","TC","TL","TC","TT"):
                    continue
                #company_id = get_company(cname)
                #if not company_id:
                #    continue
                if lin.strip().endswith(',1)'):
                    continue
                if lin.strip().endswith(',2)'):
                    continue
                if lin.strip().endswith(',3)'):
                    continue
                if lin.strip().endswith(',4)'):
                    continue
                if lin.strip().endswith(',5)'):
                    continue
                if lin.strip().endswith(',6)'):
                    continue
                if lin.strip().endswith(',1)'):
                    pass
                else:    
                    uom_id = pool.get('product.uom').search(cr,uid,[('name','=','Unit')])[0]
                    cat_id = pool.get('product.category').search(cr,uid,[('name','=','Vendes')])[0]
                    l = lin.split('"')
                    code = l[3].strip()
                    lin0 = f.next().split('#')
                    name = lin0[0].decode('latin1').strip()
                    #name = '%s %s' % (code ,name)
                    print cname, code, name
                    a_id = pool.get('product.product').search(cr,uid,[('default_code','=',code)])
                    
                    a = {}
                    a['default_code'] = code
                    a['name'] = name
                    a['categ_id'] = cat_id
                    a['type']='service'
                    a['supply_method']='produce'
                    a['uom_id'] = uom_id
                    a['uom_po_id'] = uom_id
                    
                    a['taxes_id'] = [(6,0,iva_rep)]
                    a['supplier_taxes_id'] = [(6,0,iva_sup)]
                    #a['in_out']='OUT'
                    if a_id:
                        a_id = pool.get('product.product').write(cr,uid,a_id,a)
                    else:    
                        a_id = pool.get('product.product').create(cr,uid,a)
                
        print "Final"
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        }
    }
    
wizard_load_product('carreras.load_product')

