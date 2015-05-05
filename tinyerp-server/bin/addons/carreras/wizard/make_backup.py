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


backup_form = '''<?xml version="1.0"?>
<form string="Backup">
    <separator string="Generar còpia de seguretat?" colspan="4" />
    <field name="backup" nolabel="1" colspan="4"/>
</form>'''

backup_fields = {
    'backup': {
        'string': 'Fitxer de Backup',
        'type': 'char',
        'size':30,
        'readonly': True
    },
}

end_form = '''<?xml version="1.0"?>
<form string="Backup">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''

end_fields = {}

class wizard_backup(wizard.interface):

    def _defaults(self, cr, uid, data, context):
        data['form']['backup'] = time.strftime('TTC_%Y%m%d_%H%M%S.gz')
        return data['form']

    def _backup_process(self, cr, uid, data, context):
        pool=pooler.get_pool(cr.dbname)
        user=pool.get('res.users').browse(cr, uid, uid)
        path='/home/%s/COPIA OPENERP/' % user.login
        view=user.login
        
        if not os.path.isdir(path):
            os.system('sudo /bin/mkdir "%s"' % path)
            if not os.path.isdir(path):
                raise wizard.except_wizard('No es genera el fitxer de backup', 
                    "No es pot crear el directori 'COPIA OPENERP' de %s" % view)
        if not os.access(path,os.W_OK):
            os.system('sudo /bin/chmod a+w "%s"' % path)
            if not os.access(path,os.W_OK):
                raise wizard.except_wizard('No es genera el fitxer de backup', 
                    "No es pot gravar el fixer de backup en el 'COPIA OPENERP' de %s" % view)
        file=data['form']['backup']
        cmd = 'pg_dump %s | gzip > "%s"' % (cr.dbname,path+file)
        os.system(cmd)
        netsvc.Logger().notifyChannel("web-services", netsvc.LOG_INFO,cmd)
        return data['form']

    states = {
            'init': {
                'actions': [_defaults],
                'result': {'type':'form', 'arch':backup_form, 'fields':backup_fields,'state':[('end','Cancel·la'),('backup_process',"Procés")]}
                },
            'backup_process': {
                'actions': [_backup_process],
                'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
                },
            }

wizard_backup("carreras.backup_database")
