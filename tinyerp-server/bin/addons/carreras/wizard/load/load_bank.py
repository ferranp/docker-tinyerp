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

  Carrega de bancs

"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de bancs">
    <label string="Carrega de bancs" colspan="4"/>
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

class wizard_load_bank(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        _load_accounts(cr,uid)
        _load_journals(cr,uid)
        f = fbackup()
        
        for lin in f:
            if lin.startswith('^CARB("'):
                cname = lin[7:9]
                lin = lin.strip()
                l = lin.split(',')
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                code = l[1].strip(')')
                lin0 = f.next().split('#')
                name = lin0[0].decode('latin1')
                print code + ' ' + name
                cta = lin0[1]
                acc= lin0[2]
                acc_id = get_account(cr,uid,acc,company_id)
                
                b = {}
                b['name'] = name
                b['currency_id'] = 1
                b['journal_id'] = get_journal(cr,uid,'VENT',company_id)
                b['account_id'] = acc_id
           
                ids = pool.get('account.bank.account').search(cr,uid,[('name','=',name)])
                if ids:
                    pool.get('account.bank.account').write(cr,uid,ids,b)
                else:
                    pool.get('account.bank.account').create(cr,uid,b)
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
wizard_load_bank('carreras.load_bank')

