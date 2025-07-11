##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: subscription.py 1005 2005-07-25 08:41:42Z nicoe $
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

# TODO:
#	Error treatment: exception, request, ... -> send request to user_id

from mx import DateTime
import time
from osv import fields,osv

class subscription_document(osv.osv):
	_name = "subscription.document"
	_description = "Subscription document"
	_columns = {
		'name': fields.char('Name', size=60, required=True),
		'active': fields.boolean('Active'),
		'model': fields.many2one('ir.model', 'Model', required=True),
		'field_ids': fields.one2many('subscription.document.fields', 'document_id', 'Fields')
	}
	_defaults = {
		'active' : lambda *a: True,
	}
subscription_document()

class subscription_document_fields(osv.osv):
	_name = "subscription.document.fields"
	_description = "Subscription document fields"
	_rec_name = 'field'
	_columns = {
		'field': fields.many2one('ir.model.fields', 'Field', domain="[('model_id', '=', parent.model)]", required=True),
		'value': fields.selection([('false','False'),('date','Current Date')], 'Default Value', size=40),
		'document_id': fields.many2one('subscription.document', 'Subscription Document', ondelete='cascade'),
	}
	_defaults = {}
subscription_document_fields()

def _get_document_types(self, cr, uid, context={}):
	cr.execute('select m.model, s.name from subscription_document s, ir_model m WHERE s.model = m.id order by s.name')
	return cr.fetchall()

class subscription_subscription(osv.osv):
	_name = "subscription.subscription"
	_description = "Subscription"
	_columns = {
		'name': fields.char('Name', size=60, required=True),
		'active': fields.boolean('Active'),
		'partner_id': fields.many2one('res.partner', 'Partner'),
		'notes': fields.text('Notes'),
		'user_id': fields.many2one('res.users', 'User', required=True),
		'interval_number': fields.integer('Interval Qty'),
		'interval_type': fields.selection([('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], 'Interval Unit'),
		'exec_init': fields.integer('Number of documents'),
		'date_init': fields.datetime('First Date'),
		'state': fields.selection([('draft','Draft'),('running','Running'),('done','Done')], 'State'),
		'doc_source': fields.reference('Source Document', required=True, selection=_get_document_types, size=128),
		'doc_lines': fields.one2many('subscription.subscription.history', 'subscription_id', 'Documents created', readonly=True),
		'cron_id': fields.many2one('ir.cron', 'Cron Job')
	}
	_defaults = {
		'date_init': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
		'user_id': lambda obj,cr,uid,context: uid,
		'active': lambda *a: True,
		'interval_number': lambda *a: 1,
		'interval_type': lambda *a: 'months',
		'doc_source': lambda *a: False,
		'state': lambda *a: 'draft'
	}

	def set_process(self, cr, uid, ids, context={}):
		for row in self.read(cr, uid, ids):
			mapping = {'name':'name','interval_number':'interval_number','interval_type':'interval_type','exec_init':'numbercall','date_init':'nextcall'}
			res = {'model':'subscription.subscription', 'args': repr([[row['id']]]), 'function':'model_copy', 'priority':6, 'user_id':row['user_id'] and row['user_id'][0]}
			for key,value in mapping.items():
				res[value] = row[key]
			id = self.pool.get('ir.cron').create(cr, uid, res)
			self.write(cr, uid, [row['id']], {'cron_id':id, 'state':'running'})
		return True

	def model_copy(self, cr, uid, ids, context={}):
		for row in self.read(cr, uid, ids):
			cron_ids = [row['cron_id'][0]]
			remaining = self.pool.get('ir.cron').read(cr, uid, cron_ids, ['numbercall'])[0]['numbercall']
			try:
				(model_name, id) = row['doc_source'].split(',')
				id = int(id)
				model = self.pool.get(model_name)
			except:
				raise osv.except_osv('Wrong Source Document !', 'Please provide another source document.\nThis one does not exist !')

			default = {'state':'draft'}
			doc_obj = self.pool.get('subscription.document')
			document_ids = doc_obj.search(cr, uid, [('model.model','=',model_name)])
			doc = doc_obj.browse(cr, uid, document_ids)[0]
			for f in doc.field_ids:
				if f.value=='date':
					value = time.strftime('%Y-%m-%d')
				else:
					value = False
				default[f.field.name] = value

			state = 'running'

			# if there was only one remaining document to generate
			# the subscription is over and we mark it as being done
			if remaining == 1:
				state = 'done'
			id = self.pool.get(model_name).copy(cr, uid, id, default, context)
			self.pool.get('subscription.subscription.history').create(cr, uid, {'subscription_id': row['id'], 'date':time.strftime('%Y-%m-%d %H:%M:%S'), 'document_id': model_name+','+str(id)})
			self.write(cr, uid, [row['id']], {'state':state})
		return True

	def set_done(self, cr, uid, ids, context={}):
		res = self.read(cr,uid, ids, ['cron_id'])
		ids2 = [x['cron_id'][0] for x in res if x['id']]
		self.pool.get('ir.cron').write(cr, uid, ids2, {'active':False})
		self.write(cr, uid, ids, {'state':'done'})
		return True

	def set_draft(self, cr, uid, ids, context={}):
		self.write(cr, uid, ids, {'state':'draft'})
		return True
subscription_subscription()

class subscription_subscription_history(osv.osv):
	_name = "subscription.subscription.history"
	_description = "Subscription history"
	_rec_name = 'date'
	_columns = {
		'date': fields.datetime('Date'),
		'subscription_id': fields.many2one('subscription.subscription', 'Subscription', ondelete='cascade'),
		'document_id': fields.reference('Source Document', required=True, selection=[('account.invoice','Invoice'),('sale.order','Sale Order')], size=128),
	}
subscription_subscription_history()

