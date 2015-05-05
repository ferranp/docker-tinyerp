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

  Carrega de tarifes de preus
"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega tarifes">
    <label string="Carrega de tarifes de preus" colspan="4"/>
    <newline/>
</form>'''


select_fields = {
}

def get_tarifa(cr,uid,nomtar):
    pool = pooler.get_pool(cr.dbname)
    tar_id = pool.get('product.pricelist').search(cr,uid,[('name','=',nomtar)])
    if tar_id:
        return tar_id[0]
    tar = {}
    tar['type'] = "sale" 
    tar['name'] = nomtar
    tar['currency_id'] = 1
    
    tar_id = pool.get('product.pricelist').create(cr,uid,tar)
    ver = {}
    ver['name'] = nomtar
    ver['pricelist_id'] = tar_id
    version_id = pool.get('product.pricelist.version').create(cr,uid,ver)
    
    return tar_id
    
def get_art(cr,uid,art,variant):
    pool = pooler.get_pool(cr.dbname)
    s = [('default_code','=',art)]
    art_id = pool.get('product.product').search(cr,uid,s)
    if art_id:
        return art_id[0]
    return False
    #art_id = buscar('product.product',[('default_code','=',art)])
    #if not art_id:
    #    return False
    #tmpl_id = llegir('product.product',art_id)[0]['product_tmpl_id'][0]
    #if not tmpl_id:
    #    return False
    
    #a = {}
    #a['default_code'] = art
    #a['variants'] = variant
    #a['product_tmpl_id'] = tmpl_id
    
    #return alta('product.product',a)


class wizard_load_pricelist(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        

        f = fbackup()
        i = 0
        for lin in f:
            if lin.startswith('^TTPREU("'):
                cname = lin[9:11]
                nomtar = lin[14:17].strip()
                art = lin[17:19].strip()
                
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                print cname , nomtar , art

                tar_id = get_tarifa(cr,uid,nomtar)
                
                tar = pool.get('product.pricelist').read(cr,uid,[tar_id])[0]
                
                lin0 = f.next().split('#')
                
                kop = lin0[0]
                minim = lin0[3]
                #print lin0
                if lin0[2] == 'S':
                    variant = False
                else:
                    variant = lin0[3].decode('latin1').strip()
                
                art_id = get_art(cr,uid,art,variant)
                if not art_id:
                    continue
                art = pool.get('product.product').read(cr,uid,[art_id])[0]
                
                ti = {}
                if variant:
                    ti['name'] = "[%s] %s" % (art['default_code'],variant)
                else:
                    ti['name'] = "[%s]" % art['default_code']
                ti['price_version_id'] = tar['version_id'][0]

                ti['product_id']= art_id
                ti['product_tmpl_id']=art['product_tmpl_id'][0]
                #ti['categ_id']=
                #ti['nin_quantity']=
                if lin0[2] == 'S':
                    ti['sequence']= 10
                else:
                    ti['sequence']= 5
                ti['base']=-1
                #ti['base_pricelist_id']=
                ti['price_surcharge']= lin0[1]
                #ti['price_discount']=
                #ti['price_round']=
                #ti['price_min_margin']=
                #ti['price_max_margin']=
                
                ti_id = pool.get('product.pricelist.item').search(cr,uid,[('name','=',ti['name']),
                            ('price_version_id','=',ti['price_version_id'])])
                if ti_id:
                    ti_id = pool.get('product.pricelist.item').write(cr,uid,ti_id,ti)
                else:    
                    ti_id = pool.get('product.pricelist.item').create(cr,uid,ti)

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
            'result': {'type':'form', 'arch':select_form, 'fields':select_fields, 'state':[('end','Cancelar'),('change','Carregar') ]}
        },
        'change': {
            'actions': [_load],
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
        }
    }
    
wizard_load_pricelist('carreras.load_pricelist')

