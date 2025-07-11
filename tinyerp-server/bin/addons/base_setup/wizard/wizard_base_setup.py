##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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
import time
import tools
import os

view_form_profit = """<?xml version="1.0"?>
<form string="Setup">
	<image name="gtk-dialog-info"/>
	<group>
		<separator string="Select a profile" colspan="2"/>
		<newline/>
		<field align="0.0" name="profile"/>
		<newline/>
		<label string="A profile sets a pre-selection of modules for enterprise needs." colspan="2" align="0.0"/>
		<newline/>
		<label string="You'll be able to install others modules later through the Administration menu." colspan="2" align="0.0"/>
	</group>
</form>"""

view_form_charts = """<?xml version="1.0"?>
<form string="Setup">
	<image name="gtk-dialog-info" colspan="2"/>
	<group>
		<separator string="Select a chart of accounts" colspan="2"/>
		<newline/>
		<field name="charts" align="0.0"/>
		<newline/>
		<label string="There is many other charts on http://www.tinyerp.com/" colspan="2" align="0.0"/>
		<newline/>
		<label string="(If you don't select a chart of accounts, you'll need to set up one manually)." colspan="2" align="0.0"/>
	</group>
</form>"""

view_form_company = """<?xml version="1.0"?>
<form string="Setup">
	<image name="gtk-dialog-info" colspan="2"/>
	<group>
		<separator string="Define main company" colspan="4"/>
		<newline/>
		<field name="name" align="0.0" colspan="4" required="True"/>
		<newline/>
		<field name="street" align="0.0"/>
		<field name="street2" align="0.0"/>
		<field name="zip" align="0.0"/>
		<field name="city" align="0.0"/>
		<field name="country_id" align="0.0"/>
		<field name="state_id" align="0.0"/>
		<field name="email" align="0.0"/>
		<field name="phone" align="0.0"/>
		<field name="currency" align="0.0"/>
		<separator string="Report header" colspan="4"/>
		<newline/>
		<field name="rml_header1" align="0.0" colspan="4"/>
		<field name="rml_footer1" align="0.0" colspan="4"/>
		<field name="rml_footer2" align="0.0" colspan="4"/>
	</group>
</form>"""

view_form_update = """<?xml version="1.0"?>
<form string="Setup">
	<image name="gtk-dialog-info" colspan="2"/>
	<group>
		<separator string="Summary" colspan="2"/>
		<newline/>
		<field name="profile" align="0.0" readonly="1"/>
		<newline/>
		<field name="charts" align="0.0" readonly="1"/>
		<newline/>
		<field name="name" align="0.0" readonly="1"/>
	</group>
</form>
"""

view_form_finish = """<?xml version="1.0"?>
<form string="Setup">
	<image name="gtk-dialog-info" colspan="2"/>
	<group colspan="2" col="4">
		<separator colspan="4" string="Installation done"/>
		<label align="0.0" colspan="4" string="Your new database is now fully installed."/>
		<label align="0.0" colspan="4" string="You can start using the system or continue the configuration using the menu Administration\Configuration"/>
	</group>
</form>
"""

class wizard_base_setup(wizard.interface):
	def _get_profiles(self, cr, uid, context):
		module_obj=pooler.get_pool(cr.dbname).get('ir.module.module')
		ids=module_obj.search(cr, uid, [('category_id', '=', 'Profile'), ('state', '<>', 'installed')])
		res=[(m.id, m.shortdesc) for m in module_obj.browse(cr, uid, ids)]
		res.append((-1, 'Minimal Profile'))
		res.sort()
		return res
	def _get_charts(self, cr, uid, context):
		module_obj=pooler.get_pool(cr.dbname).get('ir.module.module')
		ids=module_obj.search(cr, uid, [('category_id', '=', 'Account charts'), ('state', '<>', 'installed')])
		res=[(m.id, m.shortdesc) for m in module_obj.browse(cr, uid, ids)]
		res.append((-1, 'None'))
		res.sort(lambda x,y: cmp(x[1],y[1]))
		return res
	def _get_company(self, cr, uid, data, context):
		pool=pooler.get_pool(cr.dbname)
		company_obj=pool.get('res.company')
		ids=company_obj.search(cr, uid, [])
		if not ids:
			return {}
		company=company_obj.browse(cr, uid, ids)[0]
		self.fields['name']['default']=company.name
		self.fields['currency']['default']=company.currency_id.id
		return {}
		#self.fields['rml_header1']['default']=company.rml_header1
		#self.fields['rml_footer1']['default']=company.rml_footer1
		#self.fields['rml_footer2']['default']=company.rml_footer2
		#if not company.partner_id.address:
		#	return {}
		#address=company.partner_id.address[0]
		#self.fields['street']['default']=address.street
		#self.fields['street2']['default']=address.street2
		#self.fields['zip']['default']=address.zip
		#self.fields['city']['default']=address.city
		#self.fields['email']['default']=address.email
		#self.fields['phone']['default']=address.phone
		#if address.state_id:
		#	self.fields['state_id']['default']=address.state_id.id
		#else:
		#	self.fields['state_id']['default']=-1
		#if address.country_id:
		#	self.fields['country_id']['default']=address.country_id.id
		#else:
		#	self.fields['country_id']['default']=-1
		#return {}
	def _get_states(self, cr, uid, context):
		pool=pooler.get_pool(cr.dbname)
		state_obj=pool.get('res.country.state')
		ids=state_obj.search(cr, uid, [])
		res=[(state.id, state.name) for state in state_obj.browse(cr, uid, ids)]
		res.append((-1, ''))
		res.sort(lambda x,y: cmp(x[1],y[1]))
		return res
	def _get_countries(self, cr, uid, context):
		pool=pooler.get_pool(cr.dbname)
		country_obj=pool.get('res.country')
		ids=country_obj.search(cr, uid, [])
		res=[(country.id, country.name) for country in country_obj.browse(cr, uid, ids)]
		res.sort(lambda x,y: cmp(x[1],y[1]))
		return res
	def _update(self, cr, uid, data, context):
		pool=pooler.get_pool(cr.dbname)
		form=data['form']
		if 'profile' in data['form'] and data['form']['profile'] > 0:
			module_obj=pool.get('ir.module.module')
			module_obj.state_change(cr, uid, [data['form']['profile']], 'to install', context)
		if 'charts' in data['form'] and data['form']['charts'] > 0:
			module_obj=pool.get('ir.module.module')
			module_obj.state_change(cr, uid, [data['form']['charts']], 'to install', context)

		company_obj=pool.get('res.company')
		partner_obj=pool.get('res.partner')
		address_obj=pool.get('res.partner.address')
		ids=company_obj.search(cr, uid, [])
		company=company_obj.browse(cr, uid, ids)[0]
		company_obj.write(cr, uid, [company.id], {
				'name': form['name'],
				'rml_header1': form['rml_header1'],
				'rml_footer1': form['rml_footer1'],
				'rml_footer2': form['rml_footer2'],
				'currency_id': form['currency'],
			})
		partner_obj.write(cr, uid, [company.partner_id.id], {
				'name': form['name'],
			})
		values={
					'name': form['name'],
					'street': form['street'],
					'street2': form['street2'],
					'zip': form['zip'],
					'city': form['city'],
					'email': form['email'],
					'phone': form['phone'],
					'country_id': form['country_id'],
				}
		if form['state_id'] > 0:
			values['state_id']=form['state_id']
		if company.partner_id.address:
			address=company.partner_id.address[0]
			address_obj.write(cr, uid, [address.id], values)
		else:
			values['partner_id']=company.partner_id.id
			add_id=address_obj.create(cr, uid, values)

		cr.commit()
		(db, pool)=pooler.restart_pool(cr.dbname, update_module=True)

		lang_obj=pool.get('res.lang')
		lang_ids=lang_obj.search(cr, uid, [])
		langs=lang_obj.browse(cr, uid, lang_ids)
		for lang in langs:
			if lang.code and lang.code != 'en_US':
				filename=os.path.join(tools.config["root_path"], "i18n", lang.code + ".csv")
				tools.trans_load(cr.dbname, filename, lang.code)
		return {}

	def _menu(self, cr, uid, data, context):
		users_obj=pooler.get_pool(cr.dbname).get('res.users')
		action_obj=pooler.get_pool(cr.dbname).get('ir.actions.act_window')

		ids=action_obj.search(cr, uid, [('name', '=', 'Menu')])
		menu=action_obj.browse(cr, uid, ids)[0]

		ids=users_obj.search(cr, uid, [('action_id', '=', 'Setup')])
		users_obj.write(cr, uid, ids, {'action_id': menu.id})
		ids=users_obj.search(cr, uid, [('menu_id', '=', 'Setup')])
		users_obj.write(cr, uid, ids, {'menu_id': menu.id})

		return {
			'name': menu.name,
			'type': menu.type,
			'view_id': (menu.view_id and\
					(menu.view_id.id, menu.view_id.name)) or False,
			'domain': menu.domain,
			'res_model': menu.res_model,
			'src_model': menu.src_model,
			'view_type': menu.view_type,
			'view_mode': menu.view_mode,
			'views': menu.views,
		}

	def _next(self, cr, uid, data, context):
		if not data['form']['profile'] or data['form']['profile'] <= 0:
			return 'company'
		return 'charts'
	def _previous(self, cr, uid, data, context):
		if 'profile' not in data['form'] or data['form']['profile'] <= 0:
			return 'init'
		return 'charts'
	fields={
		'profile':{
			'string':'Profile',
			'type':'selection',
			'selection':_get_profiles,
			'default': -1,
			'required': True,
		},
		'charts':{
			'string':'Chart of accounts',
			'type':'selection',
			'selection':_get_charts,
			'default': -1,
			'required': True,
		},
		'name':{
			'string': 'Company Name',
			'type': 'char',
			'size': 64,
		},
		'street':{
			'string': 'Street',
			'type': 'char',
			'size': 128,
		},
		'street2':{
			'string': 'Street2',
			'type': 'char',
			'size': 128,
		},
		'zip':{
			'string': 'Zip code',
			'type': 'char',
			'size': 24,
		},
		'city':{
			'string': 'City',
			'type': 'char',
			'size': 128,
		},
		'state_id':{
			'string': 'State',
			'type': 'selection',
			'selection':_get_states,
		},
		'country_id':{
			'string': 'Country',
			'type': 'selection',
			'selection':_get_countries,
		},
		'email':{
			'string': 'E-mail',
			'type': 'char',
			'size': 64,
		},
		'phone':{
			'string': 'Phone',
			'type': 'char',
			'size': 64,
		},
		'currency': {
			'string': 'Currency',
			'type': 'many2one',
			'relation': 'res.currency',
			'required': True,
		},
		'rml_header1':{
			'string': 'Report Header',
			'type': 'char',
			'size': 200,
		},
		'rml_footer1':{
			'string': 'Report Footer 1',
			'type': 'char',
			'size': 200,
		},
		'rml_footer2':{
			'string': 'Report Footer 2',
			'type': 'char',
			'size': 200,
		},
	}
	states={
		'init':{
			'actions': [_get_company],
			'result': {'type': 'form', 'arch': view_form_profit, 'fields': fields,
				'state': [
					('menu', 'Cancel', 'gtk-cancel'),
					('next', 'Next', 'gtk-go-forward', True)
				]
			}
		},
		'next': {
			'actions': [],
			'result': {'type': 'choice', 'next_state': _next}
		},
		'charts':{
			'actions': [],
			'result': {'type': 'form', 'arch': view_form_charts, 'fields': fields,
				'state':[
					('init', 'Previous', 'gtk-go-back'),
					('company', 'Next', 'gtk-go-forward', True)
				]
			}
		},
		'company':{
			'actions': [],
			'result': {'type': 'form', 'arch': view_form_company, 'fields': fields,
				'state': [
					('previous', 'Previous', 'gtk-go-back'),
					('update', 'Next', 'gtk-go-forward', True)
				]
			}
		},
		'previous':{
			'actions': [],
			'result': {'type': 'choice', 'next_state': _previous}
		},
		'update':{
			'actions': [],
			'result': {'type': 'form', 'arch': view_form_update, 'fields': fields,
				'state': [
					('company', 'Previous', 'gtk-go-back'),
					('finish', 'Install', 'gtk-ok', True)
				]
			}
		},
		'finish':{
			'actions': [_update],
			'result': {'type': 'form', 'arch': view_form_finish, 'fields': {},
				'state': [
					('menu', 'Ok', 'gtk-ok', True)
				]
			}
		},
		'menu': {
			'actions': [],
			'result': {'type': 'action', 'action': _menu, 'state': 'end'}
		},
	}
wizard_base_setup('base_setup.base_setup')
