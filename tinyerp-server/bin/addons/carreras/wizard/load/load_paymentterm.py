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

  Carrega de diaris comptables

"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de formes de pagament">
    <label string="Carrega de formes de pagament" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

class wizard_load_paymentterm(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        f = fbackup()


        for lin in f:
            if lin.startswith('^TAB(3'):
                lin = lin.strip()
                num = lin[7:-1]
                lin = f.next()
                l = lin.strip().split('#')
                name = l[0].capitalize()
                #print num,name
                d = pool.get('account.payment.term').search(cr,uid,[('name','=',name)])
                
                if l[3] == 'R':
                    type = 'reposicio'
                elif l[3] == 'C':
                    type = 'comptat'
                elif l[3] == 'G':
                    type = 'gir'
                else:
                    type = 'comptat'
                
                if name=='Contado':
                    type='comptat'
                
                pt = {}
                pt['name']=name
                pt['type']=type
                pt['note']=num
                if d:
                    p_id = d[0]
                    pool.get('account.payment.term').write(cr,uid,d,pt)
                    cr.execute("delete from account_payment_term_line where payment_id = %d" % p_id)
                else:
                    p_id = pool.get('account.payment.term').create(cr,uid,pt)
                
                vtos = int(l[1])
                dies = l[2].split(",")
                for i in range(vtos):
                    ptl = {}
                    ptl['name'] = name +".%d" % (i + 1)
                    ptl['sequence'] = i + 1
                    if vtos == 1:
                        ptl['value'] = 'balance'
                    elif vtos == (i + 1):
                        ptl['value'] = 'balance'
                    else:
                        ptl['value'] = 'procent'
                        ptl['value_amount'] = float(1) / float(vtos)
                    dia = int(dies[i])
                    if dia in (30,60,90,120,150,180):
                        ptl['days'] = (i+1) * dia / 30
                        ptl['condition'] = 'months'
                    else:
                        ptl['days'] = dia
                        ptl['condition'] = 'net days'
                        
                    ptl['payment_id'] = p_id
                    pool.get('account.payment.term.line').create(cr,uid,ptl)
                
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
    
wizard_load_paymentterm('carreras.load_paymentterm')

