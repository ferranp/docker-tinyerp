##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: rappel.py 2514 2006-03-23 07:33:22Z pinky $
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
import time
import ir

import pooler
from osv import osv
from report import report_sxw

class report_rappel(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(report_rappel, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'time' : time,
			'ids_to_objects': self._ids_to_objects,
			'adr_get' : self._adr_get,
			'getLines' : self._lines_get,
		})

	def _ids_to_objects(self, partners_ids):
		pool = pooler.get_pool(self.cr.dbname)
		partners = pool.get('res.partner').browse(self.cr, self.uid, partners_ids)
		return partners

	def _adr_get(self, partner, type):
		res_partner = pooler.get_pool(self.cr.dbname).get('res.partner')
		res_partner_address = pooler.get_pool(self.cr.dbname).get('res.partner.address')
		adr = res_partner.address_get(self.cr, self.uid, [partner.id], [type])[type]
		return res_partner_address.read(self.cr, self.uid, [adr])[0]

	def _lines_get(self, partner):
		moveline_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		movelines = moveline_obj.search(self.cr, self.uid,
				[('partner_id', '=', partner.id),
					('account_id.type', '=', 'receivable'),
					('reconcile_id', '=', False), ('state', '<>', 'draft')])
		movelines = moveline_obj.read(self.cr, self.uid, movelines)
		return movelines

report_sxw.report_sxw('report.account_followup.followup.print',
		'res.partner', 'addons/account_followup/report/rappel.rml',
		parser=report_rappel)
