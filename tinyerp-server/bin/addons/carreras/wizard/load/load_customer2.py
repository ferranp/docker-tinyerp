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

  Carrega de Clients

"""
import time
import StringIO
import base64
import netsvc

import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de Clients">
    <label string="Carrega de Clients" colspan="4"/>
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
    acc['name'] = name.capitalize()
    acc['sign'] = 1
    acc['parent_id'] = [(6,0,[(get_parent(cr,uid,code,company_id))]) ]
    acc['company_id'] = company_id  
    acc['close_method'] = 'detail'
    acc['type'] = get_type(code)
    acc['reconcile'] = True
    return pool.get('account.account').create(cr,uid,acc)


class wizard_load_customer(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        logger = netsvc.Logger()
        uid=pool.get('res.users').search(cr, uid, [('login','=','batch')])[0]
        es_id = pool.get('res.country').search(cr,uid,[('code','=','ES')])[0]

        if data['form'].get('load_file',False):
            f = StringIO.StringIO(base64.decodestring(data['form']['load_file']))
        else:
            f = fbackup()
        i = 0
        u=0
        for lin in f:
            if len(lin.strip()) < 10:
                continue
            if not lin.startswith('^CLI('):
                continue

            lin = lin.strip()
            cname = lin[6:8]

            company_id = get_company(cr,uid,cname)
            if not company_id:
                continue
            
            snumcli = lin[10:-1]
            numcli = int(snumcli)

            lin0 = f.next().split('#')
            f.next()
            lin1 = f.next().split('#')
            f.next()
            lin2 = f.next().split('#')
            f.next()
            lin3 = f.next().split('#')
            
            ref = lin0[4].strip()
            ref = ref.replace('-','')

            name = lin0[0].decode('latin1').strip()
            logger.notifyChannel("info", netsvc.LOG_INFO,"%s %4s %10s %s" % (cname,snumcli,ref,name))

            address = []
            bank_ids = []
            
            #cust_id = pool.get('res.partner.customer').search(cr,uid,[('name','=',numcli)])
            #if cust_id:
            #    continue
            if ref == '':
                ref = snumcli

            d2 = pool.get('res.partner').search(cr,uid,[('name','=',name)])
            d = pool.get('res.partner').search(cr,uid,[('ref','=',ref)])
            if d2:
                if not d or d != d2:
                    name = name + " (*)"
                    print "                   Nom del Client Duplicat"

            emp_id = d[0]
            emp = pool.get('res.partner').read(cr,uid,d)[0]

            # esborrar altres
            if 'address' in emp:
                address = emp['address']

            emp = dict()
            emp['name'] = name
            emp['ref'] = ref
            
            pool.get('res.partner').write(cr,uid,d,emp)

            """
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

            addr['phone'] = lin0[22].decode('latin1')
            addr['country_id'] = es_id
            if lin0[3]:
                pr = "%d" % int(lin0[3])
                #print pr ,'*', lin0[3]
                addr['state_id'] = pool.get('res.country.state').search(cr,uid,[('country_id','=',es_id)
                                    ,('code','=',pr)])[0]

            if len(lin0) > 22:
                addr['mobile'] = lin0[7].decode('latin1')
            if len(lin0) > 23:
                addr['fax'] = lin0[23].decode('latin1').strip()
            if len(lin0) > 15:
                addr['email'] = lin0[15].decode('latin1')
            if len(address):
                addr_id = address[0]
                addr_id = pool.get('res.partner.address').write(cr,uid,[addr_id],addr)
            else:
                addr_id = pool.get('res.partner.address').create(cr,uid,addr)

            # Adreca de pago
            if len(lin1) > 9:
                addr2 = dict()
                addr2['name'] = lin1[6].decode('latin1')
                addr2['partner_id'] = emp_id
                addr2['type'] = 'invoice'
                addr2['country_id'] = es_id
                addr2['street'] = lin1[7].decode('latin1')
                if len(lin1[8].split(' ')) > 1:
                    addr2['zip'] = lin1[8].split(' ',2)[0].decode('latin1')
                    addr2['city'] = " ".join(lin1[8].split(' ')[1:])
                    addr2['city'] = addr2['city'].decode('latin1')
                else:
                    addr2['zip'] = ''
                    addr2['city'] = lin1[8].decode('latin1')
                if lin1[9]:
                    pr = "%d" % int(lin1[9])
                    #print pr ,'*', lin0[3]
                    addr2['state_id'] = pool.get('res.country.state').search(cr,uid,[('country_id','=',es_id)
                                    ,('code','=',pr)])[0]
                
                    if addr2['street'] or addr2['name']:
                        if len(address) > 2: 
                            addr2_id = address[1]
                            addr2_id = pool.get('res.partner.address').write(cr,uid,[addr2_id],addr2)
                        else:
                            addr2_id = pool.get('res.partner.address').create(cr,uid,addr2)
                            
            """
            
            i = i + 1
            if i > 10:
                i = 0
                print 'COMMIT'
                cr.commit()
                u= u+1
                #if u==5:
                #    return {}
                    
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
wizard_load_customer('carreras.load_customer2')
