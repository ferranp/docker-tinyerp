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

  Carrega de tarifes de preus per recubriments
"""
import time
import wizard
import pooler 

from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega tarifes">
    <label string="Carrega de tarifes de preus per recubriments" colspan="4"/>
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


class wizard_load_pricelist_rec(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']


    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        
        uom_id = pool.get('product.uom').search(cr,uid,[('name','=','KGM')])[0]
        f = fbackup()
        i = 0
        for lin in f:
            if lin.startswith('^TTAREC("'):
                cname = lin[9:11]
                l =lin.split(",")
                pieza = l[1].strip().strip(' ")').strip()
                art = l[2].strip().strip(' ")').strip()
                long = int(l[3].strip().strip(' ")').strip())
                
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                print cname , pieza , art , long
                lin0 = f.next().split('#')
                
                minim = lin0[0]
                
                art_id = get_art(cr,uid,art)
                if not art_id:
                    continue
                artic = pool.get('product.product').read(cr,uid,[art_id])[0]
                piece_id = pool.get('pricelist.piece').search(cr,uid,[('code','=',pieza)])[0]
                piece = pool.get('pricelist.piece').read(cr,uid,[piece_id])[0]
                t = {}
                t['name'] = "[%s] %s %d" % (art,piece['name'],long)
                t['company_id'] = company_id
                t['piece_id'] = piece_id
                t['product_id'] = art_id
                t['long'] = long
                t['product_uom'] = uom_id
                t['minimum'] = minim
                t['apply_minimum'] = True
                
                t_id = pool.get('pricelist.rec').search(cr,uid,[('name','=',t['name']),\
                        ('company_id','=',company_id)])
                if t_id:
                    pool.get('pricelist.rec').write(cr,uid,t_id,t)
                    t_id = t_id[0]
                else:    
                    t_id = pool.get('pricelist.rec').create(cr,uid,t)

                
                preus = []
                for i in range(1,len(lin0),2):
                    if lin0[i]:
                        preus.append((lin0[i],lin0[i+1]))
                
                for cant,preu in preus:
                    tl = {}
                    tl['name'] = cant
                    tl['diameter'] = cant
                    tl['price'] = preu
                    tl['pricelist_rec_id'] = t_id
                    tl_id = pool.get('pricelist.rec.line').search(cr,uid,[('name','=',tl['name']),\
                            ('pricelist_rec_id','=',t_id)])
                    if tl_id:
                        pool.get('pricelist.rec.line').write(cr,uid,tl_id,tl)
                        tl_id = tl_id[0]
                    else:    
                        tl_id = pool.get('pricelist.rec.line').create(cr,uid,tl)

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
    
wizard_load_pricelist_rec('carreras.load_pricelist_rec')

