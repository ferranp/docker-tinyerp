# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: cash.py 1070 2005-07-29 12:41:24Z nicoe $
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
  Fer backup de la BDD a un directori
"""
import wizard
import netsvc
import pooler
import tools
import os
from tempfile import mkstemp
import time


restart_form = '''<?xml version="1.0"?>
<form string="Reiniciar">
    <separator string="Reiniciar el servidor OpenERP?" colspan="4" />
</form>'''

restart_fields = {
}

end_form = '''<?xml version="1.0"?>
<form string="Traspàs">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''

end_fields = {}

class wizard_restart(wizard.interface):

    def _defaults(self, cr, uid, data, context):
        return data['form']

    def _restart(self, cr, uid, data, context):
        netsvc.Logger().notifyChannel("web-services", netsvc.LOG_INFO,'Reiniciant ...')
        cmd = 'sudo /etc/init.d/tinyerp-server restart'
        os.system(cmd)
        return data['form']

    states = {
            'init': {
                'actions': [_defaults],
                'result': {'type':'form', 'arch':restart_form, 'fields':restart_fields,'state':[('end','Cancel·la'),('restart',"Reiniciar")]}
                },
            'restart': {
                'actions': [_restart],
                'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
                },
            }

wizard_restart("carreras.openerp_restart")
