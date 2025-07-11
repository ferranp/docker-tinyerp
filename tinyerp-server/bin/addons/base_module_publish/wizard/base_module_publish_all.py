##############################################################################
#
# Copyright (c) 2005-2007 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import wizard
import pooler
import module_zip
from base_module_publish import post_multipart
from urllib import urlopen

intro_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="Publication information" colspan="4"/>
	<field name="text" colspan="4" nolabel="1"/>
</form>'''

intro_fields = {
	'text': {'string': 'Introduction', 'type': 'text', 'readonly': True,
		'default': lambda *a: """
This system will automatically publish and upload the selected modules to the
Tiny ERP official website. You can use it to quickly update a set of
module (new version).

Make sure you read the publication manual and modules guidlines
before continuing:
  http://www.tinyerp.com/

Thanks you for contributing!
"""},
}

login_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="User information" colspan="4"/>
	<label string="Please provide here your login on the Tiny ERP website."
	align="0.0" colspan="4"/>
	<label string="If you don't have an access, you can create one http://www.tinyerp.com/"
	align="0.0" colspan="4"/>
	<field name="login"/>
	<newline/>
	<field name="password"/>
	<newline/>
	<field name="email"/>
</form>'''

login_fields = {
	'login': {'string':'Login', 'type':'char', 'size':32, 'required':True},
	'email': {'string':'Email', 'type':'char', 'size':100, 'required':True},
	'password': {'string':'Password', 'type':'char', 'size':32, 'required':True,
		'invisible':True},
}

end_form = '''<?xml version="1.0"?>
<form string="Module publication">
	<separator string="Upload information" colspan="4"/>
	<field name="update" colspan="4"/>
	<field name="already" colspan="4"/>
	<field name="error" colspan="4"/>
</form>'''

end_fields= {
	'update': {'type': 'text', 'string': 'Modules updated', 'readonly': True},
	'already': {'type': 'text', 'string': 'Modules already updated',
		'readonly': True},
	'error': {'type': 'text', 'string': 'Modules in error', 'readonly': True},
}

def _upload(self, cr, uid, datas, context):
	pool = pooler.get_pool(cr.dbname)
	modules = pool.get('ir.module.module').browse(cr, uid, datas['ids'])
	log = [[], [], []] # [update, already, error]
	for mod in modules: # whoooouuuuffff update
		if mod.state != 'installed':
			result[2].append(mod.name)
			continue
		res = module_zip.createzip(cr, uid, mod.id, context, b64enc=False,
				src=(mod.license in ('GPL-2')))
		download = 'http://www.tinyerp.com/download/modules/'+res['module_filename']
		result = post_multipart('www.tinyerp.com', '/mtree_upload.php',
				[('login', datas['form']['login']),
					('password', datas['form']['password']),
					('module_name', mod.name)
				], [('module', res['module_filename'],
					res['module_file'])
				])
		if result[0] == "1":
			raise wizard.except_wizard('Error', 'Login failed!')
		elif result[0] == "0":
			log[0].append(mod.name)
		elif result[0] == "2":
			log[1].append(mod.name)
		else:
			log[2].append(mod.name)
		updata = {
			'link_name': mod.shortdesc or '',
			'link_desc': (mod.description or '').replace('\n','<br/>\n'),
			'website': mod.website or '',
			'email': datas['form']['email'] or '',
			'cust_1': download,
			'cust_3': mod.url or '/',
			'cust_6': mod.installed_version or '0',
			'cust_7': mod.name,
			'option': 'com_mtree',
			'task': 'savelisting',
			'Itemid': '99999999',
			'cat_id': '0',
			'adminForm': '',
			'auto_login': datas['form']['login'],
			'auto_password': datas['form']['password']
		}
		a = urlopen('http://www.tinyerp.com/mtree_interface.php?module=%s' % (mod.name,))
		aa = a.read()
		if aa[0]<>'0':
			updata['link_id']=aa.split('\n')[0]
			updata['option'] = 'mtree'
		result = post_multipart('www.tinyerp.com', '/index.php', updata.items(), [])
	return {'update': '\n'.join(log[0]), 'already': '\n'.join(log[1]),
		'error': '\n'.join(log[2])}

class base_module_publish_all(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {
				'type': 'form',
				'arch': intro_form,
				'fields': intro_fields,
				'state': [
					('end', 'Cancel'),
					('login', 'Ok'),
				]
			}
		},
		'login': {
			'actions': [],
			'result': {
				'type': 'form',
				'arch': login_form,
				'fields': login_fields,
				'state': [
					('end', 'Cancel'),
					('publish', 'Publish')
				]
			}
		},
		'publish': {
			'actions': [_upload],
			'result': {
				'type': 'form',
				'arch': end_form,
				'fields': end_fields,
				'state': [
					('end', 'Close')
				]
			}
		},
	}
base_module_publish_all('base_module_publish.module_publish_all')
