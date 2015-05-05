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

  Carrega de Proveïdors

"""
import time
import StringIO
import base64
import netsvc

import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de Proveïdors">
    <label string="Carrega de Proveïdors" colspan="4"/>
    <newline/>
    <field name="load_file" colspan="4"/>
</form>'''


select_fields = {
    'load_file':{
        'string': 'Fitxer a carregar',
        'type': 'binary',
    }
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

class wizard_load_supplier(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        logger = netsvc.Logger()

        uid=pool.get('res.users').search(cr, uid, [('login','=','batch')])[0]

        es_id = pool.get('res.country').search(cr,uid,[('code','=','ES')])[0]

        d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_receivable'),('res_id','=',False)])
        p = {}
        p['name']='property_account_receivable'
        p['res_id']= False
        p['value']= False
        p['company_id']= False
        p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_receivable')])[0]
        if d:
            pool.get('ir.property').write(cr,uid,d, p)
        else:
            pool.get('ir.property').create(cr,uid, p)

        d = pool.get('ir.property').search(cr,uid,[('name','=','property_account_payable'),('res_id','=',False)])
        p = {}
        p['name']='property_account_payable'
        p['res_id']= False
        p['value']= False
        p['company_id']= False
        p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_payable')])[0]
        if d:
            pool.get('ir.property').write(cr,uid,d, p)
        else:
            pool.get('ir.property').create(cr,uid, p)

        """
        categ_id = pool.get('res.partner.category').search(cr,uid,[('name','=','Client')])
        if categ_id:
            categ_id = categ_id[0]
        else:
            categ_id = pool.get('res.partner.category').create(cr,uid,{'name':'Client'})

        categ_pro = pool.get('res.partner.category').search(cr,uid,[('name','=','Proveïdor')])
        if categ_pro:
            categ_pro = categ_pro[0]
        else:
            categ_pro = pool.get('res.partner.category').create(cr,uid,{'name':'Proveïdor'})
        """
        
        if data['form'].get('load_file',False):
            f = StringIO.StringIO(base64.decodestring(data['form']['load_file']))
        else:
            f = fbackup()
        i = 0
        for lin in f:
            if len(lin.strip()) < 10:
                continue
            if not lin.startswith('^PRO("'):
                continue

            lin0 = f.next().split('#')
            cname = lin[6:8]
            company_id = get_company(cr,uid,cname)
            if not company_id:
                continue

            snumprov = lin.strip()[10:-1]

            #if cname != "TL":
            #    continue
            #if snumprov[0:1] in ['0','1','2','3','4','5','6','7','8'] and len(snumprov.strip()) < 4:
            #    continue
            
            name = lin0[0].decode('latin1').strip()
            ref = lin0[4]
            ref = ref.replace('-','')
            #print "%s %-4s %-10s %s" % (cname,snumprov,ref,name)
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s %4s %10s %s" % (cname,snumprov,ref,name))
            
            d2 = pool.get('res.partner').search(cr,uid,[('name','=',name)])
            d = pool.get('res.partner').search(cr,uid,[('ref','=',ref)])
            if d2:
                if not d or d != d2:
                    name = name + " (*)"
                    while d2:
                        d2 = pool.get('res.partner').search(cr,uid,[('name','=',name)])
                        if d2:
                            name = name + " (*)"
                    logger.notifyChannel("info", netsvc.LOG_INFO,"                   Nom del Proveïdor Duplicat")

            if d:
                emp_id = d[0]
                emp = pool.get('res.partner').read(cr,uid,d)[0]
                # esborrar altres
                address = emp['address']
                #if 'address' in emp:
                #     = pool.get('res.partner.address').unlink(cr,uid,emp['address'])
            else:
                address=[]
            
            emp = dict()
            emp['name'] = name
            emp['ref'] = ref
            
            #emp['category_id'] = [(6,0,[(categ_pro)]) ]
            emp['category_id'] = [(6,0,[]) ]
            if d:
                pool.get('res.partner').write(cr,uid,d, emp)
                #create=False
            else:
                emp_id = pool.get('res.partner').create(cr,uid,emp)
                #create=True

            c_company_id = company_id
            acc_id = pool.get('account.account').search(cr,uid,[('code','=',lin0[24]),('company_id','=',c_company_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id= create_account(cr,uid,lin0[11],name,c_company_id)

            res_id = 'res.partner,%d' % emp_id
            s = [('name','=','property_account_payable'),
                 ('res_id','=',res_id),('company_id','=',c_company_id)]
            d = pool.get('ir.property').search(cr,uid,s)
            p = {}
            p['name']='property_account_payable'
            p['res_id']= res_id
            p['company_id']= c_company_id
            p['value']= 'account.account,%d' % acc_id
            p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_payable')])[0]
            
            if d:
                pool.get('ir.property').write(cr,uid,d, p)
            else:
                pool.get('ir.property').create(cr,uid,p)
            cr.execute('update account_move_line set partner_id=%d where account_id=%d and partner_id is null' %
                        (emp_id,acc_id))

            addr = dict()
            addr['name'] = name
            addr['partner_id'] = emp_id
            addr['type'] = 'default'
            addr['street'] = lin0[1].decode('latin1')
            if len(lin0[2].split(' ')) > 1:
                addr['zip'] = lin0[2].split(' ',2)[0].decode('latin1')
                addr['city'] = " ".join(lin0[2].split(' ')[1:])

                addr['city'] = addr['city'].decode('latin1')
            else:
                addr['zip'] = ''
                addr['city'] = lin0[2].decode('latin1')

            addr['phone'] = lin0[7].decode('latin1')

            if not len(address):
                addr_id = pool.get('res.partner.address').create(cr,uid,addr)
            else:
                pass
                #addr_id = address[0]
                #addr_id = pool.get('res.partner.address').write(cr,uid,[addr_id],addr)

            if cname == "TL":
                numprov = "1%04d" % int(snumprov)
            elif cname == "TJ":
                numprov = "2%04d" % int(snumprov)
            elif cname == "BD":
                numprov = "5%04d" % int(snumprov)
            elif cname == "TC":
                numprov = "9%04d" % int(snumprov)
            else:
                continue

            s = [('name','=',numprov)]
            supp_id = pool.get('res.partner.supplier').search(cr,uid,s)
            
            if not supp_id:
                s.append(('active','=',0))
                supp_id = pool.get('res.partner.supplier').search(cr,uid,s)
                
            c_company_id = company_id
            supp = {}
            supp['name'] = numprov
            supp['partner_id'] =  emp_id
            supp['company_id'] = c_company_id

            if supp_id:
                supp_id = pool.get('res.partner.supplier').write(cr,uid,supp_id,supp)
            else:
                supp_id = pool.get('res.partner.supplier').create(cr,uid,supp)

            i = i + 1
            if i > 10:
                i = 0
                print 'COMMIT'
                cr.commit()
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
wizard_load_supplier('carreras.load_supplier')
