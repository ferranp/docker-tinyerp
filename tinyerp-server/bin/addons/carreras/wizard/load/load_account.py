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

  Carrega de comptes

"""
import time
import wizard
import pooler 
from common import *
import os.path
import netsvc

select_form = '''<?xml version="1.0"?>
<form string="Carrega de comptes">
    <label string="Carrega de comptes" colspan="4"/>
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


accounts = {}

def crea_top(cr,uid,company):
    pool = pooler.get_pool(cr.dbname)
    d = pool.get('account.account').search(cr,uid,[('code','=','0'),('company_id','=',company)])
    if d:
        return  d[0]
    else:    
        cname = pool.get('res.company').read(cr,uid,[company])[0]['name']
        acc = {}
        acc['code'] = '0'
        acc['name'] = 'Pla Comptable %s' % cname
        acc['sign'] = 1
        #acc_data['parent_id'] = [(6,0,[(parent)]) ]
        acc['close_method'] = 'none'
        #acc['currency_id'] = 1
        acc['company_id'] = company 

        return pool.get('account.account').create(cr,uid,acc)

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
        top = buscar_code(cr,uid,'0',company)
        if top:
            return top
        return crea_top(cr,uid,company)

    code = code[:-1]
    parent = buscar_code(cr,uid,code,company)
    if parent:
        return parent
    return get_parent(cr,uid,code,company)


def link(cr,uid,parent_id,childs,company):
    if not childs:
        return
    pool = pooler.get_pool(cr.dbname)
    #parent_id = buscar_code(cr,uid,parent,company)
    parent = pool.get('account.account').browse(cr,uid,parent_id)
    #print parent.child_id
    for child in childs.keys():
        child_id = buscar_code(cr,uid,child,company)
        if child_id:
            #if child_id not in parent.child_id:
            #print child,child_id
            data = {'parent_id' : [(4,parent_id)]}
            pool.get('account.account').write(cr,uid,child_id,data)
            link(cr,uid,child_id,childs[child],company)
        
    

class wizard_load_account(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        f = fbackup()
        logger=netsvc.Logger()

        for lin in f:
            if lin.startswith('^CON("'):
                cname = lin[6:8]
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                l = lin.split('"')
                code = l[3].strip()
                lin0 = f.next().split('#')
                logger.notifyChannel("info", netsvc.LOG_INFO,cname + ' ' + code + ' ' + lin0[0].decode('latin1'))
                d = pool.get('account.account').search(cr,uid,[('code','=',code),('company_id','=',company_id)])
                acc = {}
                acc['code'] = code
                acc['name'] = lin0[0].decode('latin1').capitalize()
                acc['sign'] = 1
                acc['parent_id'] = [(6,0,[(get_parent(cr,uid,code,company_id))]) ]
                acc['company_id'] = company_id  
                if lin0[2] == 'S':
                    if len(code) == 8 and code[0:4] == '4000':
                        acc['close_method'] = 'unreconciled'
                        acc['type'] = get_type(code)
                        acc['reconcile'] = True
                    elif len(code) == 8 and code[0:4] == '4300':
                        acc['close_method'] = 'balance'
                        acc['type'] = get_type(code)
                        acc['reconcile'] = True
                    else:
                        acc['close_method'] = 'none'
                        acc['type'] = get_type(code)
                        acc['reconcile'] = False
                else:  
                    acc['close_method'] = 'none'
                    acc['type'] = 'view'
                    acc['reconcile'] = False
                #acc['currency_id'] = 1
                
                if d:
                    acc_id = pool.get('account.account').write(cr,uid,d,acc)
                else:    
                    acc_id = pool.get('account.account').create(cr,uid,acc)
        return {}

    def _get_or_create(self,cr,uid,acc):
        pool = pooler.get_pool(cr.dbname)
        code = acc['code']
        company_id = acc['company_id']
        s = [('code','=',code),('company_id','=',company_id)]
        if code == '0':
            s.append(('name','=',acc['name']))
        d = pool.get('account.account').search(cr,uid,s)
        #acc['currency_id'] = 1
        if d:
            pool.get('account.account').write(cr,uid,d,acc)
            acc_id = d[0]
        else:    
            acc_id = pool.get('account.account').create(cr,uid,acc)
        return acc_id

    def _struct(self, cr, uid, data, context):
        global accounts
        accounts = {}
        logger=netsvc.Logger()
        pool = pooler.get_pool(cr.dbname)
        for cname in ['TL','TJ','TC','BD','RT','TI','IS']:
            company_id = get_company(cr,uid,cname)
            if not company_id:
                continue
            b_id = None
            e_id = None
            cr.execute("delete from account_account where code like 'B%%' and company_id=%d"%company_id)
            cr.execute("delete from account_account where code like 'E%%' and company_id=%d"%company_id)
            if not company_id:
                continue
            if os.path.isfile('/opt/tinyerp-server/bin/addons/carreras/balance3.txt'):
                file = '/opt/tinyerp-server/bin/addons/carreras/balance3.txt'
            elif os.path.isfile('/opt/tinyerp/addons/carreras/balance3.txt'):
                file = '/opt/tinyerp/addons/carreras/balance3.txt'
            for line in open(file):
                if len(line.strip()) == 0:
                    continue
                if line.startswith('#'):
                    continue
                elif line.startswith('*'):
                    parts = line.split(',')
                    code = parts[1]
                    name = parts[2].strip().strip('"').strip()
                    logger.notifyChannel("info", netsvc.LOG_INFO,cname+' '+code+' '+name)
                    acc = {}
                    acc['code'] = code
                    acc['name'] = name
                    acc['sign'] = 1
                    #acc['parent_id'] = False
                    acc['company_id'] = company_id  
                    acc['close_method'] = 'none'
                    acc['type'] = 'view'
                    acc['reconcile'] = False
                    
                    if code == 'B0':
                        acc['code'] = '0'
                        b_id = self._get_or_create(cr,uid,acc)
                    elif code == 'E0':
                        acc['code'] = '0'
                        e_id = self._get_or_create(cr,uid,acc)
                    else:
                        balance_id = self._get_or_create(cr,uid,acc)
                else:
                    parts = line.split(',')
                    parent = parts[0].strip()
                    if parent == 'B0':
                        parent_id = b_id
                    elif parent == 'E0':
                        parent_id = e_id
                    else:
                        parent_id = buscar_code(cr,uid,parent,company_id)
                    if not parent_id:
                        logger.notifyChannel("info", netsvc.LOG_INFO,'*'*100)
                        logger.notifyChannel("info", netsvc.LOG_INFO,line)
                        continue
                    
                    child = parts[1].strip()
                    logger.notifyChannel("info", netsvc.LOG_INFO,'Link, '+parent+' '+child)
                    child_id = buscar_code(cr,uid,child,company_id)
                    if not child_id:
                        continue

                    data = {'parent_id' : [(4,parent_id)]}
                    pool.get('account.account').write(cr,uid,child_id,data)
            cr.commit()
        logger.notifyChannel("info", netsvc.LOG_INFO,'Final')
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Carregar'),('struct','Crea Balanç i Explotacio') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        },
        'struct': {
            'actions': [_struct],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        }
    }
wizard_load_account('carreras.load_account')

