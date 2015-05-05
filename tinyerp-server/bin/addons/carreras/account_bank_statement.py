# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import tools
import ir
import pooler
import netsvc

from osv import fields,osv
#import memcached as osv

class account_bank_statement(osv.osv):
    _name = "account.bank.statement"
    _inherit = "account.bank.statement"

    def button_confirm(self, cr, uid, ids, context=None):
        #logger= netsvc.Logger()
        #logger.notifyChannel("info", netsvc.LOG_INFO,str(ids)+" " +str(balance))
        res = super(account_bank_statement, self).button_confirm(cr, uid, ids, context)
        for st in self.browse(cr, uid, ids, context):
            if st.state!='confirm':
                continue
            for move in st.line_ids:
                if not move.amount:
                    continue
                cr.execute('SELECT id,debit,credit \
                         FROM account_move_line \
                         WHERE (reconcile_id is null) \
                            AND partner_id = %d \
                            AND ref = %s \
                            AND account_id=%d', \
                            (move.partner_id.id, move.ref, move.account_id.id))
                balance=0.0
                ids=[]
                for id,debit,credit in cr.fetchall():
                    balance += debit - credit
                    ids.append(id)
                balance=round(balance,2)
                if balance==0.0:
                    logger= netsvc.Logger()
                    logger.notifyChannel("info", netsvc.LOG_INFO,ids)
                    self.pool.get('account.move.line').reconcile(cr,uid,ids)
        return res

account_bank_statement()

class account_bank_statement_line(osv.osv):
    _name = "account.bank.statement.line"
    _inherit = "account.bank.statement.line"

    def onchange_partner_id(self, cr, uid, line_id, ref, type, partner_id, 
            account_id, currency_id, context={}):
        if not partner_id:
            return {}
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        
        company_currency_id = res_users_obj.browse(cr, uid, uid,
                context=context).company_id.currency_id.id

        if not currency_id:
            currency_id = company_currency_id

        partner= self.pool.get('res.partner').browse(cr, uid, partner_id,context=context)
        
        if not account_id:
            if type == 'supplier':
                account_id = partner.property_account_payable.id
            else:
                account_id =  partner.property_account_receivable.id

        if not ref:
            return {'value': {'account_id': account_id}}
        
        cr.execute('SELECT sum(debit-credit)'+ \
                ' FROM account_move_line'+ \
                ' WHERE (reconcile_id is null)'+ \
                '    AND partner_id = %d'+ \
                '    AND ref = %s'+ \
                '    AND account_id=%d', \
                     (partner_id, ref,account_id))
        
        res = cr.fetchone()
        balance = res and res[0] or 0.0

        balance = res_currency_obj.compute(cr, uid, company_currency_id,
                currency_id, balance, context=context)
        return {'value': {'amount': balance, 'account_id': account_id}}

account_bank_statement_line()
