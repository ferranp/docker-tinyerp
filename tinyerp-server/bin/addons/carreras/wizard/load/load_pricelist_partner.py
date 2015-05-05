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

  Carrega de tarifes de preus per client
"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega tarifes">
    <label string="Carrega de tarifes de preus per client" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

def get_art(cr,uid,art):
    pool = pooler.get_pool(cr.dbname)
    s = [('default_code','=',art)]
    art_id = pool.get('product.product').search(cr,uid,s)
    if art_id:
        return art_id[0]
    return False


class wizard_load_pricelist_partner(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        kilo_id = pool.get('product.uom').search(cr,uid,[('name','=','KGM')])[0]
        unit_id = pool.get('product.uom').search(cr,uid,[('name','=','Unit')])[0]

        f = fbackup()
        i = 0
        cli_tar = {}
        for lin in f:
            if lin.startswith('^CLI("'):
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
                ref = lin0[4].strip().replace('-','')
                name = lin0[0].decode('latin1').strip()
                #print cname ,' ',ref,' ' ,name

                d = pool.get('res.partner').search(cr,uid,[('ref','=',ref)])
                if not d:
                    d = pool.get('res.partner').search(cr,uid,[('name','=',name)])
                if d:
                    tarifa = lin0[21].decode('latin1').strip()
                    if tarifa not in cli_tar:
                        cli_tar[tarifa] = []
                    cli_tar[tarifa].append(d[0])

        """
        for i,j in cli_tar.iteritems():
            print i
            print j
        print 'Final'
        return {}
        """
        f = fbackup()
        i = 0
        for lin in f:
            if lin.startswith('^TTPREU("'):
                cname = lin[9:11]
                if cname not in ("BD","TC"):
                    continue
                nomtar = lin[14:17].strip()
                art = lin[17:19].strip()
                
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                print cname , nomtar , art

                lin0 = f.next().split('#')
                
                #print lin0
                if lin0[2] == 'S' or lin0[2] == 'N':
                    variant = "Tarifa General Client"
                    minim = lin0[3].strip()
                elif lin0[3].decode('latin1').strip() == '':
                    variant = "Tarifa General Client"
                    minim = lin0[2].strip()
                else:
                    variant = lin0[3].decode('latin1').strip()
                    minim = lin0[2].strip()
                
                art_id = get_art(cr,uid,art)
                if not art_id:
                    continue
                art = pool.get('product.product').read(cr,uid,[art_id])[0]
                
                for client in cli_tar[nomtar]:
                    ti = {}
                    ti['name'] = "[%s] %s" % (art['default_code'],variant)
                    ti['partner_id'] = client
                    ti['company_id'] = company_id
                    ti['product_id']= art_id
                    ti['minimum']=minim
                    ti['apply_minimum']= True
                    ti['price']= lin0[1]
                    #ti['per_rec']= 0
                    if lin0[0] == 'K':
                        ti['product_uom']= kilo_id
                    else:
                        ti['product_uom']= unit_id
                    ti['profundity'] = 0
                    #print ti
                    s=[]
                    s.append(('name','=',ti['name']))
                    s.append(('partner_id','=',ti['partner_id']))
                    s.append(('product_id','=',art_id))
                    s.append(('company_id','=',company_id))
                    ti_id = pool.get('pricelist.partner').search(cr,uid,s)
                    if ti_id:
                        pool.get('pricelist.partner').write(cr,uid,ti_id,ti)
                        ti_id = ti_id[0]
                    else:    
                        ti_id = pool.get('pricelist.partner').create(cr,uid,ti)

                i = i +1
                if i > 100:
                    cr.commit()
                    print 'COMMIT'
                    i = 0
        print 'Final'
        return {}
    
    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields,
                    'state':[('end','Cancelar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 
                    'state':[('end','Tancar')]}
        }
    }
    
wizard_load_pricelist_partner('carreras.load_pricelist_partner')

