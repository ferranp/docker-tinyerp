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
        
        msgs=pool.get('res.messages').search(cr, uid, [])
        msg_ids={}
        for msg in pool.get('res.messages').browse(cr, uid, msgs):
            msg_ids[msg.code]=msg.id

        agents=pool.get('agent.agent').search(cr, uid, [])
        agent_ids={}
        for agent in pool.get('agent.agent').browse(cr, uid, agents):
            agent_ids[agent.code]=agent.id

        """
        for k,v in msg_ids.iteritems():
            print k,v
        print "*********************************"
        for k,v in agent_ids.iteritems():
            print k,v
        print "*********************************"
        """

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
            sw_modif = True
            
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

            if d:
                emp_id = d[0]
                emp = pool.get('res.partner').read(cr,uid,d)[0]
                ult_fac = emp['last_invoice']
                new_ult_fac =  False
                if len(lin0[12]) > 7:
                    new_ult_fac = lin0[12][0:4] + '-' + lin0[12][4:6] + '-' + lin0[12][6:8]

                if new_ult_fac <= ult_fac:
                    sw_modif = False
                # esborrar altres
                if 'address' in emp:
                    address = emp['address']
                #    baixa('res.partner.address',emp['address'])
                if 'bank_ids' in emp and sw_modif:
                    bank_ids= emp['bank_ids']
                    #pool.get('res.partner.bank').unlink(cr,uid,emp['bank_ids'])

            emp = dict()
            emp['name'] = name
            #emp['code'] = numcli
            emp['ref'] = ref
            emp['ref_prov'] = lin0[14]
            #emp['category_id'] = [(6,0,[categ_id]) ]
            emp['category_id'] = [(6,0,[])]
            #pool.get('res.partner.category').unlink(cr,uid,emp['bank_ids'])
            if len(lin0[12]) > 7:
                emp['last_invoice'] = lin0[12][0:4] + '-' + lin0[12][4:6] + '-' + lin0[12][6:8]
            
            emp['pay_day1'] = 0
            emp['pay_day2'] = 0
            emp['pay_day3'] = 0
            pay_days = lin1[1].split(',')
            for ii,day in enumerate(pay_days):
                emp['pay_day%d' % (ii + 1)] = day
            
            if lin1[2]:
                s_nopay,e_nopay = lin1[2].split(',')
                #print lin1[2] , s_nopay,e_nopay
                emp['start_no_pay']="%s-%s-2000" % (s_nopay[0:2],s_nopay[2:4])
                emp['end_no_pay']="%s-%s-2000" % (e_nopay[0:2],e_nopay[2:4])
                #print emp
            
            # Morositat
            #if len(lin0[8].strip()) > 0:
            #    emp['comment'] = "Morositat %s" % lin0[8].strip()
            
            if len(lin0[13]) == 0:
                emp['credit_limit'] = 0.0
            elif float(lin0[13]) == 0.0:
                emp['credit_limit'] = 0.01
            else:
                emp['credit_limit'] = float(lin0[13])

            if len(lin0) > 24 and len(lin0[24]) == 8 and lin0[24].isdigit():
                emp['date'] = lin0[24][0:4] + '-' + lin0[24][4:6] + '-' + lin0[24][6:8]

            if len(lin0[8]) !=0: 
                emp['message']=msg_ids[lin0[8]]

            if sw_modif:
                if d:
                    pool.get('res.partner').write(cr,uid,d,emp)
                else:
                    emp_id = pool.get('res.partner').create(cr,uid,emp)

            if cname.strip() == "TT":
                if str(numcli).startswith('1'):
                    c_company_id = get_company(cr,uid,'TL')
                else:
                    c_company_id = get_company(cr,uid,'TJ')
            else:
                c_company_id = company_id
            
            acc_id = pool.get('account.account').search(cr,uid,[('code','=',lin0[11]),('company_id','=',c_company_id)])
            if acc_id:
                acc_id = acc_id[0]
            else:
                acc_id= create_account(cr,uid,lin0[11],name,c_company_id)
            res_id = 'res.partner,%d' % emp_id
            s = [('name','=','property_account_receivable'),
                 ('res_id','=',res_id),('company_id','=',c_company_id)]
            d = pool.get('ir.property').search(cr,uid,s)
            p = {}
            p['name']='property_account_receivable'
            p['res_id']= res_id
            p['company_id'] = c_company_id
            p['value']= 'account.account,%d' % acc_id
            p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_account_receivable')])[0]
            
            if d:
                pool.get('ir.property').write(cr,uid,d, p)
            else:
                pool.get('ir.property').create(cr,uid,p)

            cr.execute('update account_move_line set partner_id=%d where account_id=%d and partner_id is null' %
                        (emp_id,acc_id))
            
            payment_term = lin1[0]
            if snumcli[1:4] == "000":
                payment_term="28"
            if len(payment_term):
                pay_id = pool.get('account.payment.term').search(cr,uid,[('note','=',payment_term)])
                if pay_id:
                    pay_id = pay_id[0]
                    res_id = 'res.partner,%d' % emp_id
                    d = pool.get('ir.property').search(cr,uid,[('name','=','property_payment_term'),('res_id','=',res_id)])
                    p = {}
                    p['name']='property_payment_term'
                    p['res_id']= res_id
                    p['company_id'] = False
                    p['value']= 'account.payment.term,%d' % pay_id
                    p['fields_id']= pool.get('ir.model.fields').search(cr,uid,[('name','=','property_payment_term')])[0]
                    
                    if d:
                        pool.get('ir.property').write(cr,uid,d, p)
                    else:
                        pool.get('ir.property').create(cr,uid,p)
                    
        
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
            if sw_modif:
                if len(address):
                    addr_id = address[0]
                    addr_id = pool.get('res.partner.address').write(cr,uid,[addr_id],addr)
                else:
                    addr_id = pool.get('res.partner.address').create(cr,uid,addr)

            banc = dict()
            banc['name'] = lin1[3].decode('latin1').strip()
            banc['partner_id'] = emp_id
            #banc['bank_name'] = banc['name']
            baddr = lin1[4].decode('latin1').strip().split('!')
            banc['street'] = baddr[0]
            if len(baddr) > 1:
                banc['city'] = baddr[1]
            banc['state'] = 'bank'
            if len(lin1) > 13 and lin1[12]:
                banc['acc_number'] = lin1[11] +'-'+ lin1[12] +'-'+ lin1[13].strip() +'-'+ lin1[5]
            else:
                banc['acc_number'] = lin1[5]
            banc['acc_number'] = banc['acc_number'].strip()

            if sw_modif:
                if len(banc['name']) > 0 or len(banc['acc_number']) > 0 or banc['street'] > 0:
                    if len(bank_ids):
                        banc_id = pool.get('res.partner.bank').write(cr,uid,bank_ids[0],banc)
                    else:
                        banc_id = pool.get('res.partner.bank').create(cr,uid,banc)
            
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
                
                if sw_modif:
                    if addr2['street'] or addr2['name']:
                        if len(address) > 2: 
                            addr2_id = address[1]
                            addr2_id = pool.get('res.partner.address').write(cr,uid,[addr2_id],addr2)
                        else:
                            addr2_id = pool.get('res.partner.address').create(cr,uid,addr2)
                            
            s = [('name','=',numcli)]
            cust_id = pool.get('res.partner.customer').search(cr,uid,s)
            if not cust_id:
                s.append(('active','=',0))
                cust_id = pool.get('res.partner.customer').search(cr,uid,s)
            if cname.strip() == "TT":
                if str(numcli).startswith('1'):
                    c_company_id = get_company(cr,uid,'TL')
                else:
                    c_company_id = get_company(cr,uid,'TJ')
            else:
                c_company_id = company_id
            cust = {}
            cust['partner_id'] =  emp_id
            cust['name'] = numcli
            cust['company_id'] = c_company_id
            cust['discount_inv']= lin3[5] and float(lin3[5]) or 0.0
            s = len(lin3[6]) and [('code','=',lin3[6])] or [('code','=','0')]
            finan_cost=pool.get("account.financing").search(cr,uid,s)
            if len(finan_cost) == 0 and cname not in ["BD","TC","TL","TJ","TT"]:
                finan_cost=pool.get("account.financing").search(cr,uid,[('code','=','0')])
            cust['financing_cost']=finan_cost[0]
            cust['invoice_copies']= lin3[0] and int(lin3[0])+2 or 2
            if len(lin0[9]) !=0:
                if cname == "TC":
                    cust['agent_id']=agent_ids['6']
                else:
                    cust['agent_id']=agent_ids[lin0[9]]

            if cust_id:
                cust_id = pool.get('res.partner.customer').write(cr,uid,cust_id,cust)
            else:
                cust_id = pool.get('res.partner.customer').create(cr,uid,cust)

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
wizard_load_customer('carreras.load_customer')
