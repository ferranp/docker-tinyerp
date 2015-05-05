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

  
  Carrega d'empreses

"""
import time
import wizard
import pooler 
from common import *
select_form = '''<?xml version="1.0"?>
<form string="Canvi d'empresa">
    <label string="Carrega d'emrpeses" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

class wizard_load_company(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        # creo empresa TT
        emp = dict()
        name = "TT Empresa consolidada"

        d = pool.get('res.partner').search(cr,uid,[('ref','=','TT')])
        if d:
            emp_id = d[0]
        else :	  
            #emp['ref'] = data[0]
            emp['name'] = name
            # nif
            emp['ref'] = "TT"
            emp['comment'] = ""

            emp_id = pool.get('res.partner').create(cr,uid,emp)
            addr = dict()
            addr['name'] = name
            addr['partner_id'] = emp_id
            addr['type'] = 'default'
            
        comp_id = pool.get('res.company').search(cr,uid,[('name','=',name)])
        if comp_id:
            comp_id = comp_id[0]
        comp = dict()
        comp['name'] = name
        comp['partner_id'] = emp_id
        comp['rml_header1'] = name
        comp['parent_id'] = 1
        comp['short_name'] = "TT"
        comp['currency_id'] = 1

        if comp_id:
            comp_id = pool.get('res.company').write(cr,uid,[comp_id],comp)
        else:
            comp_id = pool.get('res.company').create(cr,uid,comp)

        f = fbackup()

        for lin in f:
            if lin.startswith('^TAB(21,"0'):
                num = lin[9:11]
                lin = f.next()
                data = lin.split('#')
                emp = dict()
                abr = data[0]
                name = data[1]
                
                if abr in ['RT','TI','IS']:
                    continue                

                print num,abr,name,data[4]

                d = pool.get('res.partner').search(cr,uid,[('ref','=',data[4])])
                d2 = pool.get('res.partner').search(cr,uid,[('name','=',name)])
                if d2 and not d:
                   d = d2

                if d:
                    emp_id = d[0]
                else :	  
                    #emp['ref'] = data[0]
                    emp['name'] = name
                    # nif
                    emp['ref'] = data[4].replace('-','')
                    emp['comment'] = data[8]

                    emp_id = pool.get('res.partner').create(cr,uid,emp)
                    addr = dict()
                    addr['name'] = name
                    addr['partner_id'] = emp_id
                    addr['type'] = 'default'
                    addr['street'] = data[2]
                    addr['zip'] = data[3].split(' ',2)[0]
                    addr['city'] = data[3].split(' ',2)[1]
                    addr['phone'] = data[6]
                    addr['fax'] = data[7]

                    addr_id = pool.get('res.partner.address').create(cr,uid,addr)
                
                comp_id = pool.get('res.company').search(cr,uid,[('short_name','=',abr)])
                if comp_id:
                    comp_id = comp_id[0]
                comp = dict()
                comp['name'] = abr +" "+ name
                comp['short_name'] =  abr
                comp['partner_id'] = emp_id
                comp['rml_header1'] = name
                comp['currency_id'] = 1
                if len(data) > 9:
                    comp['rml_footer1'] = data[9].decode('latin_1').strip()

                if len(data) > 8  and data[8].strip() == abr:
                    comp['parent_id'] = 1
                else:
                    comp['parent_id'] = False
                    print data[8]
                    parent_id = pool.get('res.company').search(cr,uid,[('name','like',data[8].strip())])
                    if parent_id:
                        for i in parent_id:
                            if i != 1:
                                comp['parent_id'] = i

                if comp_id:
                    pool.get('res.company').write(cr,uid,[comp_id],comp)
                else:
                    comp_id = pool.get('res.company').create(cr,uid,comp)
                    
                # creo fiscal-year
                for code in ['2006','2007','2008']:
                    fy = pool.get('account.fiscalyear').search(cr,uid,[('company_id','=',comp_id),
                            ('code','=',code)])
                    year = {}
                    year['name']= "Any fiscal " + code + " " + abr
                    year['code']=code
                    year['date_start'] = year['code'] + '-01-01'
                    year['date_stop'] = year['code'] + '-12-31'
                    year['company_id'] = comp_id
                    if fy:
                        pool.get('account.fiscalyear').write(cr,uid,fy,year)
                    else:
                        fy = pool.get('account.fiscalyear').create(cr,uid,year)
                        fy = [fy]
                    cr.commit()
                    yy = pool.get('account.fiscalyear').read(cr,uid,fy,['period_ids'])[0]
                    if not yy['period_ids']:
                        pool.get('res.users').write(cr,uid,[uid],{'company_id':comp_id})
                        pool.get('account.fiscalyear').create_period(cr,uid,fy)
                        pool.get('res.users').write(cr,uid,[uid],{'company_id':1})

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
wizard_load_company('carreras.load_company')

