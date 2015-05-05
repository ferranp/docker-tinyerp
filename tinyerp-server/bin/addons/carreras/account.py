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
"""
  Posar el nom de l'empresa en el periode i any fiscals
"""
class account_period(osv.osv):
    _name = "account.period"
    _inherit = "account.period"

    def prev(self, cr, uid, period, step=1, context={}):
        ids = self.search(cr, uid, [('date_start','<',period.date_start)])
        if not ids:
            return False
        return ids[len(ids) -1]

    def name_get(self, cr, user, ids, context=None):
        if not context:
            context={}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        c = self.pool.get('res.company')
        return [(r['id'], r[self._rec_name]+' '+c.read(cr,user,[r['company_id']],['short_name'])[0]['short_name']) for r in self.read(cr, user, ids, [self._rec_name,'company_id'], context, load='_classic_write')]

    def get_fiscalyear_periods(self,cr,uid,fiscalyear_id,context={}):
        return self.search(cr,uid,[('fiscalyear_id','=',fiscalyear_id)])

account_period()

class account_fiscalyear(osv.osv):
    _name = "account.fiscalyear"
    _inherit = "account.fiscalyear"

    def name_get(self, cr, user, ids, context=None):
        if not context:
            context={}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        c = self.pool.get('res.company')
        return [(r['id'], r[self._rec_name]+' '+c.read(cr,user,[r['company_id']],['short_name'])[0]['short_name']) for r in self.read(cr, user, ids, [self._rec_name,'company_id'], context, load='_classic_write')]

account_fiscalyear()

class account_journal(osv.osv):
    _name = "account.journal"
    _inherit = "account.journal"

    def name_get(self, cr, user, ids, context=None):
        if not context:
            context={}
        if not ids:
            return []
        if isinstance(ids, (int, long)):
            ids = [ids]
        c = self.pool.get('res.company')
        return [(r['id'], r[self._rec_name] +' ' + str(c.read(cr,user,[r['company_id']],['short_name'])[0]['short_name'])) for r in self.read(cr, user, ids, [self._rec_name,'company_id'], context, load='_classic_write')]

account_journal()

class account_journal_period(osv.osv):
    _name = "account.journal.period"
    _inherit = "account.journal.period"
    _columns = {
        'company_id': fields.many2one('res.company', 'Empresa', required=True),
    }

    def create(self, cr, uid, vals, context={}):
        if 'company_id' not in vals and 'period_id' in vals:
            p = self.pool.get('account.period').browse(cr,uid,vals['period_id'])
            vals['company_id'] = p.company_id.id
        if 'company_id' not in vals and 'journal_id' in vals:
            j = self.pool.get('account.journal').browse(cr,uid,vals['journal_id'])
            vals['company_id'] = j.company_id.id
        return super(account_journal_period, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context={}):
        if 'company_id' not in vals and 'period_id' in vals:
            p = self.pool.get('account.period').browse(cr,uid,vals['period_id'])
            vals['company_id'] = p.company_id.id
        if 'company_id' not in vals and 'journal_id' in vals:
            j = self.pool.get('account.journal').browse(cr,uid,vals['journal_id'])
            vals['company_id'] = j.company_id.id
        return super(account_journal_period, self).write(cr, uid, ids, vals, context=context)
account_journal_period()

class account_move(osv.osv):
    _name = "account.move"
    _inherit = "account.move"
    _order = "period_id desc,id desc"

    def _credit(self, cr, uid, ids, field_name, arg, context={}):
        move_set = ",".join(map(str, ids))
        cr.execute(("SELECT move_id, COALESCE(SUM(credit),0) FROM account_move_line"+\
                    " where move_id in (%s) group by move_id") % (move_set, ))
        res2 = cr.fetchall()
        res = {}
        for id in ids:
            res[id] = 0.0
        for move_id, sum in res2:
            res[move_id] = sum
        return res

    def _debit(self, cr, uid, ids, field_name, arg, context={}):
        move_set = ",".join(map(str, ids))
        cr.execute(("SELECT move_id, COALESCE(SUM(debit),0) FROM account_move_line"+\
                    " where move_id in (%s) group by move_id") % (move_set, ))
        res2 = cr.fetchall()
        res = {}
        for id in ids:
            res[id] = 0.0
        for move_id, sum in res2:
            res[move_id] = sum
        return res

    def _balance(self, cr, uid, ids, field_name, arg, context={}):
        move_set = ",".join(map(str, ids))
        cr.execute(("SELECT move_id, COALESCE(SUM(debit - credit),0) FROM account_move_line"+\
                    " where move_id in (%s) group by move_id") % (move_set, ))
        res2 = cr.fetchall()
        res = {}
        for id in ids:
            res[id] = 0.0
        for move_id, sum in res2:
            res[move_id] = sum
        return res

    _columns = {
        'company_id': fields.many2one('res.company', 'Empresa', required=True),
        'balance': fields.function(_balance, digits=(16,2), method=True, string='Saldo'),
        'credit': fields.function(_credit, digits=(16,2), method=True, string='Credit'),
        'debit': fields.function(_debit, digits=(16,2), method=True, string='Debit'),
        
    }
    
    def create(self, cr, uid, vals, context={}):
        if 'company_id' not in vals and 'period_id' in vals:
            p = self.pool.get('account.period').browse(cr,uid,vals['period_id'],context)
            vals['company_id'] = p.company_id.id
        if 'company_id' not in vals and 'journal_id' in vals:
            j = self.pool.get('account.journal').browse(cr,uid,vals['journal_id'],context)
            vals['company_id'] = j.company_id.id
        return super(account_move, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context={}):
        if 'company_id' not in vals and 'period_id' in vals:
            p = self.pool.get('account.period').browse(cr,uid,vals['period_id'])
            vals['company_id'] = p.company_id.id
        if 'company_id' not in vals and 'journal_id' in vals:
            j = self.pool.get('account.journal').browse(cr,uid,vals['journal_id'])
            vals['company_id'] = j.company_id.id
        return super(account_move, self).write(cr, uid, ids, vals, context=context)
    
account_move()

#
# Consulta de desglos del saldo
# 
class report_account_balance(osv.osv):
    _name = "report.account.balance"
    _description = "Desglos de saldos"
    _auto = False
    _columns = {
        'name': fields.char('Nom', size=7, readonly=True),
        'code': fields.char('Codi Any', size=7, readonly=True,select=True),
        'period_id': fields.many2one('account.period', 'Periode'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Any'),
        'account_id': fields.many2one('account.account', 'Compte'),
        'balance':fields.float('Saldo', readonly=True),
        'debit':fields.float('Debit', readonly=True),
        'credit':fields.float('Credit', readonly=True),
    }
    _order = 'account_id,code desc,name desc'
    def init(self, cr):
        cr.execute("""
            create or replace view report_account_balance as (
                select
                    min(l.id) as id,
                    y.code,
                    p.name,
                    l.period_id,
                    p.fiscalyear_id,
                    l.account_id,
                    sum(l.debit-l.credit) as balance,
                    sum(l.debit) as debit,
                    sum(l.credit) as credit
                from
                    account_move_line l
                left join
                    account_period p on (l.period_id=p.id)
                left join
                    account_fiscalyear y on (p.fiscalyear_id=y.id)
                where
                    l.state <> 'draft'
                group by
                    y.code,p.name, p.fiscalyear_id, l.period_id,l.account_id
            )""")
report_account_balance()

class account_account(osv.osv):
    _name = "account.account"
    _inherit = "account.account"
    _columns = {
        'balance_ids' : fields.one2many('report.account.balance', 'account_id', 'Desglos de Saldos'),
        #'close_method': fields.selection([('none','None'), ('balance','Balance'), ('detail','Detail'),('unreconciled','Unreconciled')], 'Deferral Method', required=True, help="Tell Tiny ERP how to process the entries of this account when you close a fiscal year. None removes all entries to start with an empty account for the new fiscal year. Balance creates only one entry to keep the balance for the new fiscal year. Detail keeps the detail of all entries of the preceeding years. Unreconciled keeps the detail of unreconciled entries only."),
    }


    def unlink(self, cr, uid, ids, context={}):
        raise osv.except_osv(
                "Operació no permesa",
                "No es poden eliminar comptes")

account_account()

class account_financing(osv.osv):
    _name = "account.financing"
    _description = "Despeses de finançament"
    _columns = {
        'code': fields.char('Codi', size=7),
        'name': fields.char('Descripció', size=40),
        'percentage':fields.float('Percentatge', digits=(4,2)),
    }
    _order = 'code'

    def name_get(self, cr, uid, ids, context={}):
        res = []
        for r in self.browse(cr,uid,ids,context):
            res.append((r.id,"%s - %s" % (r.code,r.name)))
        return res

account_financing()


