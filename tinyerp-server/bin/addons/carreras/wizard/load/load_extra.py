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

  Carrega de dades extra

"""
import time
import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de dades extra">
    <label string="Carrega de impostos, periode, forma de pagament, centres de treball" colspan="4"/>
    <newline/>
</form>'''

select_fields = {
}

def get_type(acc):
    if len(acc) < 3:
       return 'view'
    if acc.startswith('470'):   
       return 'tax'
    if acc.startswith('6'):   
       return 'expense'
    if acc.startswith('7'):   
       return 'income'
    if acc.startswith('1'):   
       return 'asset'
    if acc.startswith('57'):   
       return 'cash'
    if acc.startswith('40'):   
       return 'payable'
    if acc.startswith('43'):   
       return 'receivable'
    return 'equity' 

def get_parent(cr,uid,code,company):
    pool = pooler.get_pool(cr.dbname)
    if len(code) > 6:
        code = code[:6]
    if len(code) < 2:
        return buscar_code(cr,uid,'0',company)

    code = code[:-1]
    parent = buscar_code(cr,uid,code,company)
    if parent:
        return parent
    return get_parent(cr,uid,code,company)

accounts = {}

def buscar_code(cr,uid,code,company):
    pool = pooler.get_pool(cr.dbname)
    if (code,company) in accounts:
        return accounts[(code,company)]
    s = [('code','=',code),('company_id','=',company)]
    if code == '0':
        s.append(('name','like','Pla Comptable'))
    d = pool.get('account.account').search(cr,uid,s)
    if d:
        accounts[(code,company)]=d[0]
        return d[0]
    return False

def create_account(cr, uid, code, name, company_id):
    pool = pooler.get_pool(cr.dbname)
    acc = {}
    acc['code'] = code
    acc['name'] = name
    acc['sign'] = 1
    acc['parent_id'] = [(6,0,[(get_parent(cr,uid,code,company_id))]) ]
    acc['company_id'] = company_id  
    acc['close_method'] = 'detail'
    acc['type'] = get_type(code)
    acc['reconcile'] = True
    return pool.get('account.account').create(cr,uid,acc)

class wizard_load_extra(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        year = time.strftime("%Y")
        ids = pool.get('account.fiscalyear').search(cr,uid,[('code','=',year)])
        for i in ids:
            p = pool.get('account.fiscalyear').read(cr,uid,[i],['period_ids'])
            if not p:
                pool.get('account.fiscalyear').create_period(cr,uid,[i])
                
        
        # crear tax codes
        emp_ids = pool.get('res.company').search(cr,uid,[('id','>','1'),('name','not like','TT%')])
        
        for emp_id in emp_ids:

            # compte ingressos financers
            fin_acc_id = pool.get('account.account').search(cr,uid,[('code','=','76900'),('company_id','=',emp_id)])[0]
            d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_financing'),('company_id','=',emp_id)])
            p = {}
            p['name']='property_account_financing'
            p['company_id'] = emp_id
            p['value']= 'account.account,%d' % fin_acc_id
            p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_financing')])[0]
            if d:
                pool.get('ir.property').write(cr,uid,d, p)
            else:
                pool.get('ir.property').create(cr,uid,p)

            # compte de descompte facturació
            fac_acc_id = pool.get('account.account').search(cr,uid,[('code','=','66500'),('company_id','=',emp_id)])[0]
            d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_discount'),('company_id','=',emp_id)])
            p = {}
            p['name']='property_account_discount'
            p['company_id'] = emp_id
            p['value']= 'account.account,%d' % fac_acc_id
            p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_discount')])[0]
            if d:
                pool.get('ir.property').write(cr,uid,d, p)
            else:
                pool.get('ir.property').create(cr,uid,p)

            t = pool.get('account.tax.code').search(cr,uid,[('company_id','=',emp_id)])
            if not t:
                emp = pool.get('res.company').read(cr,uid,[emp_id])[0]
                tax = {}
                tax['name'] = 'Declaracio de IVA ' + emp['short_name']
                tax['code'] = 'IVA'
                tax['company_id'] = emp_id
                t_id = pool.get('account.tax.code').create(cr,uid,tax)
                
                tax = {}
                tax['name'] = 'Import IVA Suportat ' + emp['short_name']
                tax['code'] = 'IVA SUP'
                tax['company_id'] = emp_id
                tax['parent_id'] = t_id
                s_id = pool.get('account.tax.code').create(cr,uid,tax)
            
                tax = {}
                tax['name'] = 'Import IVA Repercutit ' + emp['short_name']
                tax['code'] = 'IVA REP'
                tax['company_id'] = emp_id
                tax['parent_id'] = t_id
                r_id = pool.get('account.tax.code').create(cr,uid,tax)

                tax = {}
                tax['name'] = 'Base IVA Suportat ' + emp['short_name']
                tax['code'] = 'BASE SUP'
                tax['company_id'] = emp_id
                tax['parent_id'] = t_id
                s_id = pool.get('account.tax.code').create(cr,uid,tax)

                tax = {}
                tax['name'] = 'Base IVA Repercutit ' + emp['short_name']
                tax['code'] = 'BASE REP'
                tax['company_id'] = emp_id
                tax['parent_id'] = t_id
                s_id = pool.get('account.tax.code').create(cr,uid,tax)

            acc_id = pool.get('account.account').search(cr,uid,[('code','=','47201'),('company_id','=',emp_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id=create_account(cr, uid, '42701', 'IVA Soportado 16%', emp_id)
            imp_id = pool.get('account.tax.code').search(cr,uid,[('code','=','IVA SUP'),('company_id','=',emp_id)])[0]
            base_id = pool.get('account.tax.code').search(cr,uid,[('code','=','BASE SUP'),('company_id','=',emp_id)])[0]
            tax = {
                'name': "Iva suportat al 16%",
                'amount': 0.16,
                'type': 'percent',
                'applicable_type': True,
                'account_collected_id': acc_id,
                'account_paid_id': acc_id,
                #'parent_id':fields.many2one('account.tax', 'Parent Tax Account', select=True),
                #'child_ids':fields.one2many('account.tax', 'parent_id', 'Childs Tax Account'),
                'tax_group': 'vat',
                #
                # Fields used for the VAT declaration
                #
                'base_code_id': base_id,
                'tax_code_id': imp_id,
                'base_sign': -1,
                'tax_sign': -1,
                # Same fields for refund invoices
                'ref_base_code_id': base_id,
                'ref_tax_code_id': imp_id,
                'ref_base_sign': -1,
                'ref_tax_sign': -1,
                'company_id': emp_id,
            }
            t = pool.get('account.tax').search(cr,uid,[('company_id','=',emp_id),('name','=','Iva suportat al 16%')])
            if not t:
                t = pool.get('account.tax').create(cr,uid,tax)
            else:
                pool.get('account.tax').write(cr,uid,t,tax)

            acc_id = pool.get('account.account').search(cr,uid,[('code','=','47202'),('company_id','=',emp_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id=create_account(cr, uid, '42702', 'IVA Soportado 7%', emp_id)
            imp_id = pool.get('account.tax.code').search(cr,uid,[('code','=','IVA SUP'),('company_id','=',emp_id)])[0]
            base_id = pool.get('account.tax.code').search(cr,uid,[('code','=','BASE SUP'),('company_id','=',emp_id)])[0]
            tax = {
                'name': "Iva suportat al 7%",
                'amount': 0.07,
                'type': 'percent',
                'applicable_type': True,
                'account_collected_id': acc_id,
                'account_paid_id': acc_id,
                #'parent_id':fields.many2one('account.tax', 'Parent Tax Account', select=True),
                #'child_ids':fields.one2many('account.tax', 'parent_id', 'Childs Tax Account'),
                'tax_group': 'vat',
                #
                # Fields used for the VAT declaration
                #
                'base_code_id': base_id,
                'tax_code_id': imp_id,
                'base_sign': -1,
                'tax_sign': -1,
                # Same fields for refund invoices
                'ref_base_code_id': base_id,
                'ref_tax_code_id': imp_id,
                'ref_base_sign': -1,
                'ref_tax_sign': -1,
                'company_id': emp_id,
            }
            t = pool.get('account.tax').search(cr,uid,[('company_id','=',emp_id),('name','=','Iva suportat al 7%')])
            if not t:
                t = pool.get('account.tax').create(cr,uid,tax)
            else:
                pool.get('account.tax').write(cr,uid,t,tax)

            acc_id = pool.get('account.account').search(cr,uid,[('code','=','47203'),('company_id','=',emp_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id=create_account(cr, uid, '42703', 'IVA Soportado 4%', emp_id)
            imp_id = pool.get('account.tax.code').search(cr,uid,[('code','=','IVA SUP'),('company_id','=',emp_id)])[0]
            base_id = pool.get('account.tax.code').search(cr,uid,[('code','=','BASE SUP'),('company_id','=',emp_id)])[0]
            tax = {
                'name': "Iva suportat al 4%",
                'amount': 0.04,
                'type': 'percent',
                'applicable_type': True,
                'account_collected_id': acc_id,
                'account_paid_id': acc_id,
                #'parent_id':fields.many2one('account.tax', 'Parent Tax Account', select=True),
                #'child_ids':fields.one2many('account.tax', 'parent_id', 'Childs Tax Account'),
                'tax_group': 'vat',
                #
                # Fields used for the VAT declaration
                #
                'base_code_id': base_id,
                'tax_code_id': imp_id,
                'base_sign': -1,
                'tax_sign': -1,
                # Same fields for refund invoices
                'ref_base_code_id': base_id,
                'ref_tax_code_id': imp_id,
                'ref_base_sign': -1,
                'ref_tax_sign': -1,
                'company_id': emp_id,
            }
            t = pool.get('account.tax').search(cr,uid,[('company_id','=',emp_id),('name','=','Iva suportat al 4%')])
            if not t:
                t = pool.get('account.tax').create(cr,uid,tax)
            else:
                pool.get('account.tax').write(cr,uid,t,tax)

            acc_id = pool.get('account.account').search(cr,uid,[('code','=','47700'),('company_id','=',emp_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id=create_account(cr, uid, '47700', 'IVA Repercutido 16%', emp_id)
            imp_id = pool.get('account.tax.code').search(cr,uid,[('code','=','IVA REP'),('company_id','=',emp_id)])[0]
            base_id = pool.get('account.tax.code').search(cr,uid,[('code','=','BASE REP'),('company_id','=',emp_id)])[0]
            tax = {
                'name': "Iva repercutit al 16%",
                'amount': 0.16,
                'type': 'percent',
                'applicable_type': True,
                'account_collected_id': acc_id,
                'account_paid_id': acc_id,
                #'parent_id':fields.many2one('account.tax', 'Parent Tax Account', select=True),
                #'child_ids':fields.one2many('account.tax', 'parent_id', 'Childs Tax Account'),
                'tax_group': 'vat',
                #
                # Fields used for the VAT declaration
                #
                'base_code_id': base_id,
                'tax_code_id': imp_id,
                'base_sign': 1,
                'tax_sign': 1,
                # Same fields for refund invoices
                'ref_base_code_id': base_id,
                'ref_tax_code_id': imp_id,
                'ref_base_sign': 1,
                'ref_tax_sign': 1,
                'company_id': emp_id,
            }
            t = pool.get('account.tax').search(cr,uid,[('company_id','=',emp_id),('name','=','Iva repercutit al 16%')])
            if not t:
                t = pool.get('account.tax').create(cr,uid,tax)
            else:
                pool.get('account.tax').write(cr,uid,t,tax)
            
            
            sel = [('company_id','=',emp_id),('name','=',"Iva suportat al 16%")]
            iva_sup = pool.get('account.tax').search(cr,uid,sel)[0]
            sel = [('company_id','=',emp_id),('name','=',"Iva repercutit al 16%")]
            iva_rep = pool.get('account.tax').search(cr,uid,sel)[0]
            # ventes
            cr.execute("select id from account_account where company_id=%d and code like '70%%' and type<>'view'"%emp_id)
            ids = [x[0] for x in cr.fetchall()]
            if len(ids):
                data = {'tax_ids' : [ (6,0,[iva_rep]) ]}
                pool.get('account.account').write(cr,uid,ids,data)
            
            # Descomptes
            cr.execute("select id from account_account where company_id=%d and code like '665%%' and type<>'view'"%emp_id)
            ids = [x[0] for x in cr.fetchall()]
            if len(ids):
                data = {'tax_ids' : [ (6,0,[iva_rep]) ]}
                pool.get('account.account').write(cr,uid,ids,data)
            
            # comptes
            cr.execute("select id from account_account where company_id=%d and code like '60%%' and type<>'view'"%emp_id)
            ids = [x[0] for x in cr.fetchall()]
            if len(ids):
                data = {'tax_ids' : [ (6,0,[iva_sup]) ]}
                pool.get('account.account').write(cr,uid,ids,data)
            
        pt_id = pool.get('account.payment.term').search(cr,uid,[('name','=','Comptat')])
        if pt_id:
            pt_id = pt_id[0]
        else:
            pt_id = 1
        
        for i,name in enumerate(['Sabadell','Manresa','Rubí','Inducció','Hospitalet','Barcelona']):
            ids = pool.get('sale.shop').search(cr,uid,[('name','=',name)])
            seq_ids=pool.get('ir.sequence').search(cr,uid,[('code','=','sale.order.ser0'+str(i+1))])
            if not ids:
                data = {'name':name,'warehouse_id':1,'payment_default_id':pt_id}
                if seq_ids:
                    data['sequence_id']=seq_ids[0]
                pool.get('sale.shop').create(cr,uid,data)
            else:
                if seq_ids:
                    pool.get('sale.shop').write(cr,uid,ids,{'sequence_id':seq_ids[0]})
            ids = pool.get('res.groups').search(cr,uid,[('name','=',name)])
            if not ids:
                data = {'name':name}
                pool.get('res.groups').create(cr,uid,data)
                
        eur_id = pool.get('res.currency').search(cr,uid,[('name','=','EUR')])[0]
        eur = pool.get('res.currency').browse(cr,uid,eur_id)
        for rate in eur.rate_ids:
            pool.get('res.currency.rate').write(cr,uid,rate.id,{'name':'2000-01-01'})

        # Eliminar properties errònies
        s=[('res_id','is',False),('company_id','is',False)]
        ids=pool.get('ir.property').search(cr,uid,s)
        print ids
        cr.execute('delete from ir_property where company_id is null and res_id is null')
        cr.commit()
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
wizard_load_extra('carreras.load_extra')

