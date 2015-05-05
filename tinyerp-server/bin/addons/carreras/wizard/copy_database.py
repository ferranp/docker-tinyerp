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
  Copiar la base de dades real a proves
"""
# 04.11.2010 Poder canviar el nom de la BDD de destí
import wizard
import netsvc
import pooler
import tools
import os
from tempfile import mkstemp

copy_form = '''<?xml version="1.0"?>
<form string="Traspàs">
    <separator string="Traspassar les dades de Producció a Proves?" colspan="4" />
    <field name="source_db" colspan="4"/>
    <field name="dest_db" colspan="4"/>
</form>'''

copy_fields = {
    'source_db': {
        'string': 'Base de dades origen',
        'type': 'char',
        'readonly': True,
    },
    'dest_db': {
        'string': 'Base de dades destí',
        'type': 'char',
        #'readonly': True,
    },
}

end_form = '''<?xml version="1.0"?>
<form string="Traspàs">
    <separator string="Procés finalitzat" colspan="4" />
</form>'''

end_fields = {}

class wizard_copy(wizard.interface):

    def _defaults(self, cr, uid, data, context):
        data['form']['source_db'] = cr.dbname
        data['form']['dest_db'] = "TTC_proves"
        return data['form']

    def _copy_process(self, cr, uid, data, context):
        orig = data['form']['source_db']
        dest = data['form']['dest_db']
        
        if dest.lower() == 'ttc':
            raise wizard.except_wizard('Operació Cancel·lada', \
                "No es pot generar la còpia sobre real.")
            
        
        pooler.close_db(dest)
        logger = netsvc.Logger()

        cmd = ['dropdb', '--quiet']
        #if tools.config['db_user']:
        #    cmd.append('--username=' + tools.config['db_user'])
        #if tools.config['db_host']:
        #    cmd.append('--host=' + tools.config['db_host'])
        #if tools.config['db_port']:
        #    cmd.append('--port=' + tools.config['db_port'])
        cmd.append(dest)
        res = tools.exec_pg_command(*tuple(cmd))

        if res:
            logger.notifyChannel("web-service", netsvc.LOG_ERROR,
                    'DROP DB: %s failed' % (dest,))
            #raise Exception, "Couldn't drop database"
        else:
            logger.notifyChannel("web-services", netsvc.LOG_INFO,
                    'DROP DB: %s' % (dest))
        
        cmd = ['createdb', '--quiet', '--encoding=unicode']
        #if tools.config['db_user']:
        #    cmd.append('--username=' + tools.config['db_user'])
        #if tools.config['db_host']:
        #    cmd.append('--host=' + tools.config['db_host'])
        #if tools.config['db_port']:
        #    cmd.append('--port=' + tools.config['db_port'])
        cmd.append(dest)
        res = tools.exec_pg_command(*tuple(cmd))

        if res:
            logger.notifyChannel("web-service", netsvc.LOG_ERROR,
                    'CREATE DB: %s failed' % (dest,))
            raise Exception, "Couldn't create database: %s" % ' '.join(cmd)
        else:
            logger.notifyChannel("web-services", netsvc.LOG_INFO,
                    'CREATE DB: %s' % (dest))
        
        #num,fname=mkstemp()
        cmd = "pg_dump %s | psql %s" % (orig,dest)
        #print cmd
        os.system(cmd)
        
        
        return data['form']

    states = {
            'init': {
                'actions': [_defaults],
                'result': {'type':'form', 'arch':copy_form, 'fields':copy_fields,'state':[('end','Cancel·la'),('copy_process',"Copiar")]}
                },
            'copy_process': {
                'actions': [_copy_process],
                'result': {'type':'form', 'arch':end_form, 'fields':end_fields,'state':[('end',"Tancar")]}
                },
            }

wizard_copy("carreras.copy_database")
