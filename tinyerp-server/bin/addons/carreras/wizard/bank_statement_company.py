##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
from osv import osv
import pooler

class wiz_journal(wizard.interface):

    def _action_open_window(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.bank.statement', 'tree'))
        view_res = cr.fetchone()

        user = pool.get('res.users').read(cr,uid,[uid],['company_id'])[0]
        company_id = user['company_id'][0]
        
        journal_ids=pool.get('account.journal').search(cr,uid,[])
        period_ids=pool.get('account.period').search(cr,uid,[])
        s=[('journal_id','in',journal_ids),('period_id','in',period_ids)]
        ids=pool.get('account.bank.statement').search(cr,uid,s)

        domain = "[('id','in',%s)]" % str(ids)
        return {
            'name': 'Pagaments',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.bank.statement',
            'view_id': view_res,
            'domain': domain,
            'context': {},
            'type': 'ir.actions.act_window'
        }
    
    states = {
        'init': {
            'actions': [],
            'result': {'type': 'action', 'action': _action_open_window, 'state':'end'}
        }
    }
wiz_journal('carreras.bank_statement_company')

