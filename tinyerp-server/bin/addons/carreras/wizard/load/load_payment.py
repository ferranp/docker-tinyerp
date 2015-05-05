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

class wizard_load_payment(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        print 'Carregar pagaments'
        payments={}
        #f = fbackup()
        f = fbackup('/opt/docs/Carreras/PROF')
        for lin in f:
            #if lin.startswith('^BD2006'):
            if lin.startswith('^PROF'):
                if len(lin.strip()) < 15:
                    continue
                
                company_id = get_company(cr,uid,lin[7:9])
                if not company_id:
                    continue
                lin2=f.next().split('#')
                
                
                code="4%07d" % int(lin2[0])
                ref=lin.split(',')[1].strip()
                
                if (code,company_id) not in payments:
                    payments[(code,company_id)]={}
                if ref not in payments[(code,company_id)]:
                    payments[(code,company_id)][ref]=[]
                
                lin2.append(ref)
                payments[(code,company_id)][ref].append(lin2)
                #print code,company_id,lin2
                

        accounts=[]
        print 'Carregar comptes'
        cr.execute("select id from account_account " + \
            " where code like '400_____' and type <> 'view' order by company_id,code")
        acc_ids=[x[0] for x in cr.fetchall()]
        
        print 'Conciliar moviments'
        mov_obj=pool.get('account.move')
        aml_obj=pool.get('account.move.line')
        
        for acc in pool.get('account.account').browse(cr,uid,acc_ids):
            
            #if acc.code != '40000011' or acc.company_id.id !=6:
            #    continue
            aml_ids=aml_obj.search(cr,uid,[('account_id','=',acc.id),('reconcile_id','=',False)])
            
            key=(acc.code,acc.company_id.id)
            if key in payments:
                ids=aml_obj.search(cr,uid,[('id','in',aml_ids),('name','=','SALDO INICIAL')])
                if len(ids) > 1:
                    print key,"mes d'un saldo inicial"
                    continue
                aml_ini=False
                aml=False
                lines=[]
                fac_ids=[]
                pag_ids=[]
                if len(ids) == 1:
                    aml_ini=aml_obj.browse(cr,uid,ids[0])
                for f in payments[key]:
                    new_lines=[]
                    imp_not_found=0
                    imp_found=0
                    for p in payments[key][f]:
                        credit=round(float(p[5]),2)
                        s=[('id','in',aml_ids),('ref','=',f),('debit','=',0),('credit','=',credit)]
                        ids=aml_obj.search(cr,uid,s)
                        if len(ids) > 1:
                            print key,f,"mes d'un pagament amb el mateix import"
                            continue
                        if not ids:
                            #if not aml_ini:
                            #    print key,f,"sense saldo inicial"
                            #    continue
                            imp_not_found+=credit
                            new_lines.append({
                                'name':'MIGRACIO',
                                'ref':f,
                                'credit': credit,
                                'debit': 0.0,
                                'account_id': acc.id,
                                'partner_id': False,
                                'date_maturity': "%s-%s-%s" % (p[4][0:4],p[4][4:6],p[4][6:8]),
                                'date': time.strftime('%Y-%m-%d'),
                            })
                            #print key,f,"N",p[5]
                            continue
                        imp_found+=credit
                        #print key,f,"S",p[5]
                        aml=aml_obj.browse(cr,uid,ids[0])
                        if aml.date_maturity == False:
                            mov_obj.button_cancel(cr,uid,[aml.move_id.id])
                            aml_obj.write(cr,uid,[aml.id],
                                {'date_maturity':"%s-%s-%s" % (p[4][0:4],p[4][4:6],p[4][6:8])})
                            mov_obj.button_validate(cr,uid,[aml.move_id.id])
                        aml_ids.remove(aml.id)

                    s=[('id','in',aml_ids),('ref','=',f),('debit','=',0)]
                    fac_ids=aml_obj.search(cr,uid,s)
                    imp_fac=0
                    for aml in aml_obj.browse(cr,uid,fac_ids):
                        imp_fac+=aml.credit

                    s=[('id','in',aml_ids),('ref','=',f),('credit','=',0)]
                    pag_ids=aml_obj.search(cr,uid,s)
                    imp_pag=0
                    for aml in aml_obj.browse(cr,uid,pag_ids):
                        imp_pag+=aml.debit
                    
                    imp=round(imp_not_found + imp_pag - imp_fac)
                    if imp == 0:
                        if fac_ids or pag_ids:
                            if len(new_lines) != len(fac_ids) or len(new_lines) > 1:
                                for line in new_lines:
                                    lines.append(line)
                                print key,f,"factura amb pagaments pendents DESGLOS",fac_ids,pag_ids
                            else:
                                print key,f,"factura amb pagaments pendents fraccionats",fac_ids,pag_ids
                                aml=aml_obj.browse(cr,uid,fac_ids[0])
                                mov_obj.button_cancel(cr,uid,[aml.move_id.id])
                                aml_obj.write(cr,uid,[aml.id],{'date_maturity':new_lines[0]['date_maturity']})
                                mov_obj.button_validate(cr,uid,[aml.move_id.id])
                                for id in fac_ids:
                                    aml_ids.remove(id)
                                for id in pag_ids:
                                    aml_ids.remove(id)
                    if imp != 0:
                        print key,f,"factura amb pagaments pendents anteriors"
                        for line in new_lines:
                            lines.append(line)
            
                if lines:
                    if aml:
                        pass
                    elif aml_ini:
                        aml=aml_ini
                    else:
                        ids=aml_obj.search(cr,uid,[('account_id','=',acc.id)])
                        if not ids:
                            print key,f,"no es troben moviments del compte",acc.code
                            continue
                        aml=aml_obj.browse(cr,uid,ids[0])
                    
                    mov_lines=[]
                    imp_not_found=0
                    for line in lines:
                        line['account_id']=acc.id
                        line['partner_id']=aml.partner_id.id
                        imp_not_found+=line['credit']
                        mov_lines.append(line)
                    
                    if not aml_ini or aml_ini.debit != imp_not_found:
                        mov_lines.append({
                            'name':'MIGRACIO',
                            'credit':0.0,
                            'debit':imp_not_found,
                            'account_id': acc.id,
                            'partner_id': aml.partner_id.id,
                            'date': time.strftime('%Y-%m-%d'),
                        })

                    period_id = pool.get('account.period').find(cr, uid,time.strftime('%Y-%m-%d'))[0]
                    s=[('code','=','COMP'),('company_id','=',acc.company_id.id)]
                    j_ids = pool.get('account.journal').search(cr, uid,s)
                    if len(j_ids) != 1:
                        raise wizard.except_wizard('No es pot crear l\'assentament',
                            "S'ha trobat més d'un diari COMP")
                    journal = pool.get('account.journal').browse(cr, uid, j_ids[0])
                    if not journal.sequence_id:
                        raise wizard.except_wizard('No es pot crear l\'assentament',
                            "El diari '%s' no té cap numerador definit" % journal.name)
                    
                    name = pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
                    move = {
                            'name':name,
                            'journal_id': journal.id,
                            'period_id': period_id,
                            'line_id': [(0, 0, l) for l in mov_lines],
                            'company_id': acc.company_id.id,
                    }
                    move_id = pool.get('account.move').create(cr, uid, move)
                    ids=aml_obj.search(cr,uid,[('move_id','=',move_id),('credit','=',0)])
                    if len(ids) != 1:
                        print key,"més d'un moviment amb credit 0"
                        continue
                    aml_ids.append(ids[0])
            
            if aml_ids:
                cr.execute("select sum(debit),sum(credit) from account_move_line " + \
                    " where id in (%s)" % (",".join(map(str, aml_ids)),))
                vals= cr.fetchall()[0]
                if round(vals[1] - vals[0],2) != 0:
                    print key, "NO QUADRA!!!",vals
                    continue

                # conciliació
                aml_obj.reconcile(cr,uid,aml_ids)
        
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
wizard_load_payment('carreras.load_payment')

