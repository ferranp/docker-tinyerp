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

  Carrega factures a partir del diari de vendes

"""
import time
import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de factures">
    <label string="Carrega de factures" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

_accounts={}
def _load_accounts(cr,uid):
    print 'Carregar comptes en memoria'
    cr.execute("select id,code,company_id from account_account " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _accounts[(c[1],c[2])] = c[0]
        
def get_account(cr,uid,code,company):
    return _accounts.get((code,company),False)

_journals={}    
def _load_journals(cr,uid):
    print 'Carregar diaris en memoria'
    cr.execute("select id,code,company_id from account_journal " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _journals[(c[1].strip(),c[2])] = c[0]
        
def get_journal(cr,uid,code,company):
    return _journals[(code,company)]

_tax={}    
def _load_tax(cr,uid):
    print 'Carregar tax'
    cr.execute("select id,code,company_id from account_tax ")
    for c in cr.fetchall():
        _tax[(c[1].strip(),c[2])] = c[0]
        
def get_tax(cr,uid,code,company):
    return _tax[(code,company)]

_moves={}
def get_move(cr,uid,move,date,company_id):    
    pool = pooler.get_pool(cr.dbname)
    
    if (move,company_id,date) in _moves:
        return _moves[(move,company_id,date)]
    p_id = get_period(cr,uid,date,company_id)
    ids = pool.get('account.move').search(cr, uid, [('name','<=',move),('period_id','>=',p_id)])
    if ids:
        _moves[(move,company_id,date)] = ids[0]
        return ids[0]
    return False

_periods = {}
def get_period(cr,uid,date,company_id):
    pool = pooler.get_pool(cr.dbname)
    if (date,company_id) in _periods:
        return _periods[(date,company_id)]

    dt = date
    ids = pool.get('account.period').search(cr, uid, [('company_id','=',company_id),
                            ('date_start','<=',dt),('date_stop','>=',dt)])
    if ids:
        _periods[(date,company_id)] = ids[0]
        return ids[0]
    ids = pool.get('account.fiscalyear').search(cr, uid, [('company_id','=',company_id),
                            ('date_start','<=',dt),('date_stop','>=',dt)])
    if not ids:
        year = {}
        year['name']= "Any fiscal " + date[0:4] 
        year['code']=date[0:4]
        year['date_start'] = year['code'] + '-01-01'
        year['date_stop'] = year['code'] + '-12-31'
        year['company_id'] = company_id
        fy = pool.get('account.fiscalyear').create(cr,uid,year)
        ids = [fy]
        cr.commit()
        pool.get('account.fiscalyear').create_period(cr,uid,ids)
        cr.commit()

    ids = pool.get('account.period').search(cr, uid, [('company_id','=',company_id),
                            ('date_start','<=',dt),('date_stop','>=',dt)])
    cr.commit()
    if ids:
        _periods[(date,company_id)] = ids[0]
        return ids[0]
    
    #raise "No es pot crear any fiscal"
    return False

def get_partner(cr,uid,cust):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get("res.partner.customer").search(cr,uid,[('name','=',cust)])
    if ids:
        c = pool.get("res.partner.customer").browse(cr,uid,ids[0])
        return c.partner_id
    else:
        return False

    
class wizard_load_invoice(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        _load_accounts(cr,uid)
        _load_journals(cr,uid)
        
        vwid = pool.get('workflow').search(cr,uid,[('name','=','account.invoice.basic')])
        if not vwid:
            print "no es troba el workflow"
            return
        workflow_id=vwid[0]
        
        ids=pool.get('res.company').search(cr,uid,[])
        companies=pool.get('res.company').browse(cr,uid,ids)
        credit_sequence_id={}
        cash_sequence_id={}
        refund_sequence_id={}
        for c in companies:
            credit_sequence_id[c.short_name]=c.credit_sequence_id.id
            cash_sequence_id[c.short_name]=c.cash_sequence_id.id
            refund_sequence_id[c.short_name]=c.refund_sequence_id.id
        print 'Carregar factures'
        i = 0
        f = fbackup()
        for lin in f:
            if lin.startswith('^IVA('):
                cname = lin[6:8]
                #if cname not in ["BD"]:
                #    continue
                #print cname,lin
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                #lin = lin.strip()
                #print lin
                l = lin.split(',')
                if len(l) < 5:
                    continue
                if l[3] != '1':
                    continue
                year = l[2]
                ####################################################
                #if year != '2006' and year !='2007':
                #if year not in ['2006','2007','2008']:
                if year not in ['2008']:
                    continue
                inv = l[4].strip().strip(')"')
                
                lin = f.next()
                lin = lin.strip()
                l = lin.split('#')
                #print lin
                #print l
                date_inv = l[0][0:4] + '-' +l[0][4:6] +'-' +l[0][6:8]
                #if date_inv > '2008-04-30':
                #    continue
                serie = l[1]
                numfac = l[2]
                cust = l[3]
                # l[4]
                amount = float(l[5])
                #l[6]
                #l[7]
                por_iva = l[8]
                l[9]
                l[10]
                l[11]
                l[12]
                l[13]
                l[14]
                l[15]
                imp_iva = l[16]
                l[17]
                l[18]
                l[19]
                l[20]
                acc = l[21]
                if inv == "3-200291":
                    acc="43003000"
                acc_id = get_account(cr,uid,acc,company_id)
                
                fac = {}
                numfac = "%s.%06d" % (serie, int(numfac))
                #if numfac not in ['2.101683','2.101684','2.101685','2.101686','2.101687','2.101688','2.101689','3.200297']:
                #    continue
                print year,cname,inv
                inv=numfac
                fac['name'] = inv
                fac['origin'] = "Carrega Inicial"
                fac['type'] = 'out_invoice'
                fac['number'] = numfac
                #fac['reference'] 
                #fac['comment']
                fac['state'] = 'paid'
                fac['date_invoice'] = date_inv
                #fac['date_due'] 
                partner = get_partner(cr,uid,cust)
                fac['partner_id'] = partner.id
                #if partner.bank_ids and partner.bank_ids[0].id : 
                #   fac['partner_bank_id'] = partner.bank_ids[0].id
                #fac['address_contact_id'] 
                fac['address_invoice_id'] = partner.address and partner.address[0].id or False
                if not fac['address_invoice_id']:
                    print partner.name,cust
                if partner.property_payment_term and partner.property_payment_term.id:
                    fac['payment_term'] = partner.property_payment_term.id 
                fac['period_id']=get_period(cr,uid,date_inv,company_id)
                #if acc_id != partner.property_account_receivable:
                #    print acc
                #    print partner.property_account_receivable
                #    raise "ERROR"
                fac['account_id'] = acc_id
                #fac['move_id'] 
                fac['currency_id'] = 1
                fac['journal_id'] = get_journal(cr,uid,"VENT",company_id)
                fac['company_id'] = company_id
                
                if acc[5:8]=="000":
                    fac['sequence_id']=cash_sequence_id[cname]
                else:
                    fac['sequence_id']=credit_sequence_id[cname]
                if numfac[0:3]=="0.9":
                    #fac['type'] = 'out_refund'
                    fac['sequence_id']=refund_sequence_id[cname]
                    #amount= -float(amount)
                
                s = [('name','=',inv),('partner_id','=',partner.id),('company_id','=',company_id),('period_id','=',fac['period_id'])]
                ids = pool.get("account.invoice").search(cr,uid,s)
                if ids:
                    pool.get("account.invoice").write(cr,uid,ids,fac)
                else:
                    ids = pool.get("account.invoice").create(cr,uid,fac)
                    ids = [ids]
                
                vwinst = pool.get('workflow.instance').search(cr,uid,[('res_type','=','account.invoice'),('res_id','=',ids[0])])
                if vwinst:
                    pool.get('workflow.instance').unlink(cr,uid,vwinst)
                    vwit = pool.get('workflow.workitem').search(cr,uid,[('inst_id','in',vwinst)])
                    if vwit:
                        pool.get('workflow.workitem').unlink(cr,uid,vwit)
                
                """
                w={}
                w['wkf_id']=workflow_id
                w['res_id']=ids[0]
                w['res_type']='account.invoice'
                w['state']='complete'
                vwid = pool.get('workflow.instance').search(cr,uid,[('res_type','=','account.invoice'),('res_id','=',ids[0])])
                if vwid:
                    wid=vwid[0]
                    pool.get('workflow.instance').write(cr,uid,wid,w)
                else:
                    wid = pool.get('workflow.instance').create(cr,uid,w)
                """
                iline={}
                iline['name'] = inv
                iline['invoice_id'] = ids[0]
                v_acc_id = get_account(cr,uid,'70510',company_id)
                iline['account_id'] = v_acc_id
                iline['price_unit'] = amount
                iline['quantity'] = 1
                iline['discount'] = 0.0
                tax_id = pool.get('account.account').read(cr,uid,[v_acc_id],['tax_ids'])[0]
                iline['invoice_line_tax_id'] = [ (6,0,tax_id['tax_ids']) ]
                s = [('name','=',inv),('invoice_id','=',ids[0])]
                l_ids = pool.get("account.invoice.line").search(cr,uid,s)
                if l_ids:
                    pool.get("account.invoice.line").write(cr,uid,l_ids,iline)
                else:
                    l_ids = pool.get("account.invoice.line").create(cr,uid,iline)
                
                pool.get("account.invoice").button_compute(cr,uid,ids)
                
                i = i + 1
                if i > 500:
                    i = 0
                    print 'COMMIT'
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
wizard_load_invoice('carreras.load_invoice')
