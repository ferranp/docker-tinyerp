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

  Carrega d'assentaments

"""
import time
import wizard
from osv import osv
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega d'assentaments">
    <label string="Carrega d'assentaments" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}
valid_form = '''<?xml version="1.0"?>
<form string="Carrega d'assentaments">
    <label string="Validar els assentaments" colspan="4"/>
    <newline/>
</form>'''


valid_fields = {
}

_accounts={}
def _load_accounts(cr,uid):
    print 'Carregar comptes en memoria'
    cr.execute("select id,code,company_id from account_account " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _accounts[(c[1],c[2])] = c[0]
        
def get_account(cr,uid,code,company):
    return _accounts[(code,company)]

_journals={}    
def _load_journals(cr,uid):
    print 'Carregar diaris en memoria'
    cr.execute("select id,code,company_id from account_journal " + 
               " where type <> 'view'")
    for c in cr.fetchall():
        _journals[(c[1].strip(),c[2])] = c[0]
        
def get_journal(cr,uid,code,company):
    return _journals[(code,company)]

_moves={}
def get_move(cr,uid,move,date,company_id):    
    pool = pooler.get_pool(cr.dbname)
    if (move,company_id,date) in _moves:
        return _moves[(move,company_id,date)]
    p_id = get_period(cr,uid,date,company_id)
    s = [('name','=',move),('period_id','=',p_id)]
    ids = pool.get('account.move').search(cr, uid, s)
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
    sql = "select id from account_period where company_id=%d and date_start <='%s' and date_stop >='%s'" % (company_id,dt,dt)
    cr.execute(sql)
    ids = cr.fetchall()
    if len(ids):
        _periods[(date,company_id)] = ids[0][0]
        return ids[0][0]
    print 'No trobat'
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
        pool.get('res.users').write(cr,uid,[uid],{'company_id':company_id})
        pool.get('account.fiscalyear').create_period(cr,uid,ids)
        pool.get('res.users').write(cr,uid,[uid],{'company_id':1})

    ids = pool.get('account.period').search(cr, uid, [('company_id','=',company_id),
                            ('date_start','<=',dt),('date_stop','>=',dt)])
    cr.commit()
    if ids:
        _periods[(date,company_id)] = ids[0]
        return ids[0]
    
    #raise "No es pot crear any fiscal"
    return False
    
class wizard_load_account_move(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        _load_accounts(cr,uid)
        _load_journals(cr,uid)

        linies = {}
        print 'Ordenar moviments'
        i=0
        f = fbackup()
        for lin in f:
            #if lin.startswith('^BD2006'):
            #if lin.startswith('^') and lin[3:7] in ['2006','2007','2008']:
            if lin.startswith('^') and lin[3:7] in ['2008']:
                
                lin = lin.strip()
                cname = lin[1:3]
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                
                l = lin.split(',')
                move = l[2]
                if lin[7:8] == '0':
                    # es apertura
                    move = "0."+move
                
                line = l[3][:-1]
                acc = l[1]
                acc_id = get_account(cr,uid,acc,company_id)
                #print move,line,acc
                lin = f.next()
                lin = lin.strip()
                l = lin.split('#')
                #print l
                date_move = l[0][0:4] + '-' +l[0][4:6] +'-' +l[0][6:8]
                #if date_move > "2008-04-30":
                #    continue
                diari = l[1]
                doc = l[2]
                name = l[3].decode('latin_1')
                #l[4]
                tmov = l[5]
                #l[6]
                dh = l[7]
                amount = float(l[8])
                
                m_id = get_move(cr,uid,move,date_move,company_id)
                
                if not m_id:
                    m={}
                    m['name'] = move
                    m['ref'] = False
                    p_id = get_period(cr,uid,date_move,company_id)
                    if not p_id:
                        print 'ERROR PERIOD ' , date_move , str(company_id)
                        continue
                    m['period_id'] = p_id
                    m['journal_id'] = get_journal(cr,uid,diari,company_id)
                    #m['state'] = 
                    m_id = pool.get('account.move').create(cr,uid,m)
                
                s = [('move_id','=',m_id),('name','=',name),('account_id','=',acc_id)]
                l_id = pool.get('account.move.line').search(cr,uid,s)
                if l_id:
                    continue

                print lin
                ml={}
                ml['name'] = name
                if dh == 'D':
                    ml['debit'] = amount > 0 and amount or 0
                    ml['credit'] = amount < 0 and -amount or 0
                else:
                    ml['credit'] = amount > 0 and amount or 0
                    ml['debit'] = amount < 0 and -amount or 0
                
                ml['account_id']=acc_id
                ml['move_id'] = m_id
                ml['ref'] = doc
                ml['currency_id'] = 1
                p_id = get_period(cr,uid,date_move,company_id)
                if not p_id:
                    print "errro periode "  + str(company_id )
                    print date_move
                    continue
                ml['period_id'] = p_id
                ml['journal_id'] =get_journal(cr,uid,diari,company_id)
                #ml['company_id'] = company_id
                ml['date'] = date_move
                #pool.get('account.move.line').create(cr,uid,ml,check=False)
                key = (company_id,diari,date_move,move,line)
                linies[key]=ml
                
        print 'Carregar moviments'        
        keys = linies.keys()
        keys.sort()
        for key in keys:
            ml = linies[key]
            pool.get('account.move.line').create(cr,uid,ml,check=False)
            i = i + 1
            if i > 100:
                i = 0
                print 'COMMIT'
                cr.commit()
                
        print "final"
        return {}
        

    def _valid(self, cr, uid, data, context):
        _load_accounts(cr,uid)
        pool = pooler.get_pool(cr.dbname)
        company_id = get_company(cr,uid,'BD')
        #ids = pool.get('account.fiscalyear').search(cr, uid, [('company_id','=',company_id),
        #                    ('code','=','2006')])
        sql = "select id from account_move where state='draft' " 
        
        print sql
        cr.execute(sql)
        ids = [c[0] for c in cr.fetchall()]
        steps = (len(ids) / 100) + 1
        for s in range(steps):
            s_ids = ids[s*100:(s+1)*100]
            for m in pool.get('account.move').browse(cr,uid,s_ids):
                print m.id,m.name
                #l_ids = [l.id for l in m.line_id]
                #pool.get('account.move.line').write(cr,uid,l_ids,{'state':'valid'})
                try:
                    pool.get('account.move').button_validate(cr,uid,[m.id])
                except osv.except_osv:
                    print 'ERROR ASSENTAMENT'
                    self.quadrar(cr,uid,m)
                print 'COMMIT '
                cr.commit()
        print 'final'
        return {}
    
    def quadrar(self,cr,uid,move):
        pool = pooler.get_pool(cr.dbname)
        if move.credit == move.debit:
            return
        
        diff = move.credit - move.debit
        
        ml={}
        ml['name'] = "Quadre de carrega inicial"
        if diff > 0:
            ml['debit'] = diff
            ml['credit'] = 0
        else:
            ml['credit'] = -diff
            ml['debit'] = 0
        
        
        acc_iu = acc_id = get_account(cr,uid,'99999',move.journal_id.company_id.id)
        ml['account_id']= acc_id
        ml['move_id'] =move.id
        ml['ref'] = ""
        ml['currency_id'] = 1
        ml['period_id'] = move.period_id.id
        ml['journal_id'] =move.journal_id.id
        #ml['company_id'] = move.journal_id.company_id.id
        for line in move.line_id:
            ml['date'] = line.date
            break
        pool.get('account.move.line').create(cr,uid,ml,check=False)
            

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('valida','Validar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':valid_form, 'fields':valid_fields, 'state':[('end','Tancar')]}
        },
        'valida': {
            'actions': [_valid],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        },
    }
wizard_load_account_move('carreras.load_account_move')

