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

  Carrega de Factures de Comptats

"""
import time
import StringIO
import base64

import wizard
import pooler 
from common import *

select_form = '''<?xml version="1.0"?>
<form string="Carrega de Factures">
    <label string="Carrega de Factures" colspan="4"/>
    <newline/>
    <field name="load_file_comptats" colspan="4"/>
    <newline/>
    <field name="load_file_factures" colspan="4"/>
</form>'''


select_fields = {
    'load_file_comptats':{'string': 'Fitxer de Clients de Comptats','type': 'binary'},
    'load_file_factures':{'string': 'Fitxer de Factures','type': 'binary'},
}

def get_partner(cr,uid,cust):
    pool = pooler.get_pool(cr.dbname)
    ids = pool.get("res.partner.customer").search(cr,uid,[('name','=',cust)])
    if ids:
        c = pool.get("res.partner.customer").browse(cr,uid,ids[0])
        return c.partner_id
    else:
        return False


class wizard_load_cash(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        return data['form']

    def _load(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        _load_accounts(cr,uid)
        _load_journals(cr,uid)

        #if not data['form'].get('load_file_comptats',False):
        #    return {}
        #if not data['form'].get('load_file_factures',False):
        #    return {}

        #f = StringIO.StringIO(base64.decodestring(data['form']['load_file_comptats']))
        comptats={}
        f = open('/opt/docs/Carreras/COMPTATS')
        for lin in f:
            if len(lin.strip()) < 15:
                continue
            if lin.startswith('^TTCOMPT('):
                lin = lin.strip()
                cname = lin[10:12]
                company_id = get_company(cr,uid,cname)
                if not company_id:
                    continue
                comptats[lin[16:-1]]=f.next()

        f = open('/opt/docs/Carreras/fitxers/FRATTOCT2007')
        for lin in f:
            
            continue
                
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
wizard_load_cash('carreras.load_cash')

