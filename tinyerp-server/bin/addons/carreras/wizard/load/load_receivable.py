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

  Carrega efectes

"""
import time
import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega d'efectes">
    <label string="Carrega d'efectes" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

_accounts={}
def _load_accounts(cr,uid):
    print 'Carregar comptes en memoria'
    cr.execute("select id,code,company_id from account_account " + 
               " where type <> 'view' and code like '430%'")
    for c in cr.fetchall():
        _accounts[(c[1],c[2])] = c[0]
        
def get_account(cr,uid,code,company):
    return _accounts[(code,company)]

def get_partner(cr,uid,cust):
    pool = pooler.get_pool(cr.dbname)
    cr.execute("select id from res_partner_customer " + 
               " where name = '%s'" % cust)
    #ids = pool.get("res.partner.customer").search(cr,uid,[('name','=',cust)])
    ids=cr.fetchall()[0]
    if ids:
        c = pool.get("res.partner.customer").browse(cr,uid,ids[0])
        return c.partner_id
    else:
        return False

def get_invoice(cr,uid,inv,company_id,partner,data):
    pool = pooler.get_pool(cr.dbname)
    #s = [('name','=',inv),('partner_id','=',partner.id),('company_id','=',company_id),('period_id','=',fac['period_id'])]
    s = [('name','=',inv),('partner_id','=',partner.id),('company_id','=',company_id),('date_invoice','=',data)]
    ids = pool.get("account.invoice").search(cr,uid,s)
    if ids:
        return pool.get("account.invoice").browse(cr,uid,ids[0])
    else:
        return False

def get_remesa(cr,uid,remesa,company_id,type,date,cname):
    pool = pooler.get_pool(cr.dbname)
    s = [('name','=',"C%s%06d" % (cname,int(remesa)),),('company_id','=',company_id),('date','=',date)]
    ids = pool.get("account.receivable.remittance").search(cr,uid,s)
    if ids:
        return ids[0]
    
    rem = {
        'name' : "C%s%06d" % (cname,int(remesa)),
        'company_id': company_id,
        'note': False,
        'channel_id': False,
        'state': 'draft',
        'date': date,
        'move_id': False,
        'type' : type,
    }
    ids = pool.get("account.receivable.remittance").create(cr,uid,rem)
    return ids

class wizard_load_receivable(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        tip_reb = {
        'G':'gir',
        'R':'reposicio',
        'I':'impagat',
        'C':'comptat',
        'M':'moros',
        'T':'temp',
        'A':'abonament',
        'P':'pendent',
        }
        
        pool = pooler.get_pool(cr.dbname)
        _load_accounts(cr,uid)
        
        print 'Carregar efectes'
        i = 0
        tipus = []
        f = fbackup()
        for lin in f:
            if lin.startswith('^CAR('):
                if len(lin) < 10:
                    continue
                cname = lin[6:8]
                #if cname != "BD":
                #    continue
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                l = lin.split(',')
                if len(l) < 3:
                    continue
                doc = l[1]
                ver = l[2][0:1]

                lin = f.next()
                lin = lin.strip()
                l = lin.split('#')
                
                partner = get_partner(cr,uid,l[0])
                if not partner:
                    print '*'*100
                    print l[0]
                    continue

                if l[2]=="C":
                    if cname == "TL":
                        num_fac="2.%06d" % int(doc)
                    elif cname == "TJ":
                        num_fac="3.%06d" % int(doc)
                    else:
                        num_fac="1.%06d" % int(doc)
                else:
                    if cname == "TJ":
                        num_fac="1.%06d" % int(doc)
                    else:
                        num_fac="0.%06d" % int(doc)

                data=l[3][0:4] + '-' +l[3][4:6] +'-' +l[3][6:8]
                inv = get_invoice(cr,uid,num_fac,company_id,partner,data)
                print cname,doc,l[2],num_fac,l[3],l[4]
                
                #vtos_fac = l[6]
                #canal = l[7]
                proc = l[8]
                banc = l[9]
                agencia = l[10]
                cuenta = l[11]
                
                nbanco = l[22]
                nsucur = l[23]
                
                impagado = l[13]
                contab = l[14]
                caducat = l[15]
                #canal_assign = l[16]
                remesa = l[17].strip()
                
                tip_doc=tip_reb.get(l[2],None)
                if tip_doc == 'gir':
                    type='gir'
                    unpaid='normal'
                    moros='normal'
                elif tip_doc == 'reposicio':
                    type='reposicio'
                    unpaid='normal'
                    moros='normal'
                elif tip_doc == 'abonament':
                    type='abonament'
                    unpaid='normal'
                    moros='normal'
                elif tip_doc == 'comptat':
                    type='comptat'
                    unpaid='normal'
                    moros='normal'
                elif tip_doc == 'impagat':
                    type='comptat'
                    unpaid='unpaid'
                    moros='normal'
                    if len(l[20]) == 8:
                        data = l[20][0:4] + '-' +l[20][4:6] +'-' +l[20][6:8]
                    #ban_imp = l[21]
                elif tip_doc == 'moros':
                    type='comptat'
                    unpaid='normal'
                    moros='moros'
                    if len(l[20]) == 8:
                        unpaid='unpaid'
                        data = l[20][0:4] + '-' +l[20][4:6] +'-' +l[20][6:8]
                    #ban_imp = l[21]
                else:
                    print cname,doc,"tipus desconegut :",tip_doc
                    continue
                
                state = 'pending'
                rem_id = False
                if remesa != "":
                    fec_ult_move = l[18][0:4] + '-' +l[18][4:6] +'-' +l[18][6:8]
                    rem_id = get_remesa(cr,uid,remesa,company_id,tip_doc,fec_ult_move,cname)
                    state = 'posted'
                
                if contab == 'S':
                    state = 'received'
                
                if partner and partner.bank_ids:
                    bank_id = partner.bank_ids[0].id
                else:
                    bank_id =  False
                
                rec = {
                'name' : "%s.%s" % (num_fac,ver),
                'ref' : inv and inv.name or False,
                'company_id': company_id,
                'account_id': get_account(cr,uid,"4300"+l[0],company_id),
                
                'state': state,
                'type' : type,
                'date': data,
                
                'amount': float(l[5]),
                'currency_id': 1,
                'expenses': l[19],
                'amount_original': float(l[5]),
                
                'invoice_id': inv and inv.id or False,
                'date_maturity': l[4][0:4] + '-' +l[4][4:6] +'-' +l[4][6:8],
                'date_risk': False,
                
                'partner_id': partner.id,
                'address_invoice_id': inv and inv.address_invoice_id.id or False,
                'bank_id': bank_id,

                'remittance_id': rem_id,
                'note': l[12],
                #'move_id':,
                'unpaid': unpaid,
                'morositat': moros,
                #'xec':,
                #'ccc1':,
                #'ccc2':,
                #'ccc3':,
                #'ccc4':,
                
                }
                
                s = [('name','=',rec['name']),('partner_id','=',rec['partner_id']),('company_id','=',rec['company_id']),('date','=',rec['date'])]
                try:
                    ids = pool.get("account.receivable").search(cr,uid,s)
                except:
                    print s
                    print "exception",cname,doc,l[2],num_fac,l[3],l[4]
                    continue
                if ids:
                    pool.get("account.receivable").write(cr,uid,ids,rec)
                else:
                    ids = pool.get("account.receivable").create(cr,uid,rec)
                    ids = [ids]
                
                i = i + 1
                if i > 100:
                    i = 0
                    print 'COMMIT'
                    cr.commit()
        print 'Marcar remeses'
        cr.execute("select id from account_receivable_remittance where state<>'received'");
        rem_ids = [r[0] for r in cr.fetchall()]
        for rem in pool.get('account.receivable.remittance').browse(cr,uid,rem_ids):
            if rem.num_receivables > 0:
                sql = "select count(*) from account_receivable where remittance_id"\
                            "='%d' and state='received'" % rem.id
                cr.execute(sql)
                num = cr.fetchone()
                if num and num[0] == rem.num_receivables:
                    pool.get('account.receivable.remittance').write(cr,uid,rem.id,{'state':'received'})
                    
        cr.commit()
        print 'Final'
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
wizard_load_receivable('carreras.load_receivable')

