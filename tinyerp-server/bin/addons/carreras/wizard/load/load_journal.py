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

  Per cada diari/empresa tambe creem un comptador

"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de diaris comptables">
    <label string="Carrega de diaris comptables" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

class wizard_load_journal(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        f = fbackup()

        for lin in f:
            if lin.startswith('^DIARIO("'):
                cname = lin[9:11]
                l = lin.split('"')
                code = l[3].strip()
                lin0 = f.next().split('#')
                
                print code + ' ' + lin0[0].decode('latin1')
                comp_id = get_company(cr,uid,cname)
                if not comp_id:
                    continue
                d = pool.get('account.journal').search(cr,uid,[('code','=',code),('company_id','=',comp_id)])
                j = {}
                j['code'] = code
                j['name'] = lin0[0].decode('latin1').capitalize()
                j['centralisation'] = False
                j['update_posted'] = True
                #('sale','Sale'), ('purchase','Purchase'), ('cash','Cash'), ('general','General'), ('situation','Situation')], 'Type', size=32, required=True),
                if code == 'TTC':
                    j['type'] = 'general'
                    j['view_id'] = 1
                elif code == 'APE':
                    j['type'] = 'situation'
                    j['view_id'] = 1
                elif code == 'CIE':
                    j['type'] = 'general'
                    j['view_id'] = 1
                elif code == 'COBR':
                    j['type'] = 'cash'
                    j['view_id'] = 2
                elif code == 'COMP':
                    j['type'] = 'purchase'
                    j['view_id'] = 1
                elif code == 'IMPG':
                    j['type'] = 'cash'
                    j['view_id'] = 2
                elif code == 'PAGO':
                    j['type'] = 'cash'
                    j['view_id'] = 2
                elif code == 'VENT':
                    j['type'] = 'sale'
                    j['view_id'] = 1
                elif code == 'INSO':
                    j['type'] = 'general'
                    j['view_id'] = 1
                else:
                    j['type'] = 'general'
                    j['view_id'] = 1

                j['company_id'] = comp_id
                seq_name = "Journal %s" % cname
                seq_id = pool.get('ir.sequence').search(cr,uid,[('name','=',seq_name)])
                if seq_id:
                    seq_id = seq_id[0]
                else:
                    # crear sequenceia
                    seq_code = "journal.%s" % cname
                    seq_code = seq_code.lower()
                    new_seq_code = {
                        'name' : seq_name,
                        'code' : seq_code,
                    }
                    pool.get('ir.sequence.type').create(cr,uid,new_seq_code)
                    new_seq = {
                        'name' : seq_name,
                        'code' : seq_code,
                        'padding' : 6,
                    }
                    seq_id = pool.get('ir.sequence').create(cr,uid,new_seq)
                j['sequence_id'] = seq_id
        
                acc_id = pool.get('account.account').search(cr,uid,[('code','=','99999'),('company_id','=',comp_id)])
                if acc_id:
                    acc_id = acc_id[0]
                    j['default_credit_account_id'] = acc_id
                    j['default_debit_account_id'] = acc_id
                if d:
                    j_id = pool.get('account.journal').write(cr,uid,d,j)
                else:    
                    j_id = pool.get('account.journal').create(cr,uid,j)
        
           
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
wizard_load_journal('carreras.load_journal')

