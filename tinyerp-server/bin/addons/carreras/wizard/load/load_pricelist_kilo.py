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

  Carrega de tarifes de preus per kilo/partida
"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega tarifes">
    <label string="Carrega de tarifes de preus per kilo" colspan="4"/>
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
    
def get_art(cr,uid,art):
    pool = pooler.get_pool(cr.dbname)
    s = [('default_code','=',art)]
    art_id = pool.get('product.product').search(cr,uid,s)
    if art_id:
        return art_id[0]
    return False


class wizard_load_pricelist_kilo(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        uom_id = pool.get('product.uom').search(cr,uid,[('name','=','KGM')])[0]
        f = fbackup()
        i = 0
        for lin in f:
            if lin.startswith('^TTARKP("'):
                cname = lin[9:11]
                l =lin.split(",")
                nomtar = l[3].strip().strip('")').strip()
                art = l[2].strip().strip('")').strip()
                
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                print cname , nomtar , art
                lin0 = f.next().split('#')
                
                kop = lin0[0]
                minim = lin0[3]
                
                art_id = get_art(cr,uid,art)
                if not art_id:
                    continue
                artic = pool.get('product.product').read(cr,uid,[art_id])[0]
                
                t = {}
                t['name'] = "[%s] %s " % (art,nomtar)
                t['company_id'] = company_id
                t['product_id'] = art_id
                t['product_uom'] = uom_id
                t['minimum'] = lin0[0]
                t['apply_minimum'] = True
                t['depth'] = nomtar
                
                t_id = pool.get('pricelist.kilo').search(cr,uid,[('name','=',t['name']),\
                        ('company_id','=',company_id)])
                if t_id:
                    pool.get('pricelist.kilo').write(cr,uid,t_id,t)
                    t_id = t_id[0]
                else:    
                    t_id = pool.get('pricelist.kilo').create(cr,uid,t)

                
                preus = []
                if lin0[1]:
                    preus.append((lin0[1],lin0[2]))
                if lin0[3]:
                    preus.append((lin0[3],lin0[4]))
                if lin0[5]:
                    preus.append((lin0[5],lin0[6]))
                if lin0[7]:
                    preus.append((lin0[7],lin0[8]))
                if lin0[9]:
                    preus.append((lin0[9],lin0[10]))
                if lin0[11]:
                    preus.append((lin0[11],lin0[12]))
                
                for cant,preu in preus:
                    tl = {}
                    tl['name'] = cant
                    tl['quantity'] = cant
                    tl['price'] = preu
                    tl['pricelist_kilo_id'] = t_id
                    tl_id = pool.get('pricelist.kilo.line').search(cr,uid,[('name','=',tl['name']),\
                            ('pricelist_kilo_id','=',t_id)])
                    if tl_id:
                        pool.get('pricelist.kilo.line').write(cr,uid,tl_id,tl)
                        tl_id = tl_id[0]
                    else:    
                        tl_id = pool.get('pricelist.kilo.line').create(cr,uid,tl)

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
    
wizard_load_pricelist_kilo('carreras.load_pricelist_kilo')

