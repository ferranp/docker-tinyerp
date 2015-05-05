##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
from report import report_sxw
import locale 
locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

locale.localeconv = localeconv

class account_balance_simple(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_balance_simple, self).__init__(cr, uid, name, context)
        self.sum_debit = 0.0
        self.sum_credit = 0.0
        
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'numf': self.numf,
            'fiscalyear': self.fiscalyear,
            'account': self.account,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
        })
        self.context = context

    def preprocess(self, objects, data, ids):
        self.data =data
        super(account_balance_simple, self).preprocess(objects, data, ids)
        
    def fiscalyear(self):
        return self.pool.get('account.fiscalyear').browse(self.cr,\
                self.uid,self.data['form']['fiscalyear'])        

    def account(self):
        return self.pool.get('account.account').browse(self.cr,\
                self.uid,self.ids[0])        

    def numf(self,val):
        if val == 0.0:
            return ""
        return locale.format("%0.2f",val,grouping=True)

    def lines(self, form, ids={}, done={}, level=1):
        if not ids:
            done = {}
            ids = self.ids
        if not ids:
            return []
        result = []
        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear']
        ctx['periods'] = form['periods'][0][2]
        code_min = form.get('code_start',' ')
        code_max = form.get('code_end','ZZZZZZZZZZ')
        detail = form.get('detail')
        accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids, ctx)
        def cmp_code(x, y):
            return cmp(x.code, y.code)
        accounts.sort(cmp_code)
        for account in accounts:
            if account.id in done:
                continue
            done[account.id] = 1
            res = {
                'code': account.code,
                'name': account.name,
                'level': level,
                #'debit': account.debit,
                #'credit': account.credit,
                'debit': account.balance > 0 and account.balance or 0.0,
                'credit': account.balance < 0 and -account.balance or 0.0,
                'balance': account.balance
            }
            if not (res['credit'] or res['debit']) and not account.child_id:
                continue
            self.sum_debit += account.debit
            self.sum_credit += account.credit
            if account.code >= code_min and account.code <= code_max:
                result.append(res)
            if detail or account.code.startswith('B') or \
                   account.code.startswith('E')  or account.code == '0':
                if account.child_id:
                    ids2 = [(x.code,x.id) for x in account.child_id]
                    ids2.sort()
                    result += self.lines(form, [x[1] for x in ids2], done, level+1)
        return result

    def _sum_credit(self):
        return self.sum_credit

    def _sum_debit(self):
        return self.sum_debit

class account_balance_detail(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_balance_detail, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'numf': self.numf,
            'fiscalyear': self.fiscalyear,
            'account': self.account,
            'get_period': self.get_period,
            'totals': self.totals,
        })
        self.context = context

    def preprocess(self, objects, data, ids):
        self.data =data
        self.sums={
            'prev_balance':0,
            'credit':0,
            'debit':0,
            'balance':0,
            'act_credit':0,
            'act_debit':0,
            'act_balance':0,
            }
        super(account_balance_detail, self).preprocess(objects, data, ids)
        
    def fiscalyear(self):
        return self.pool.get('account.fiscalyear').browse(self.cr,\
                self.uid,self.data['form']['fiscalyear'])        

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '/' + date1[1] + '/' + date1[0]
        else:
            return ""

    def get_period(self):
        return "Periode %s - %s" % (self.format_date(self.data['form']['date_start']),self.format_date(self.data['form']['date_end']))

    def account(self):
        return self.pool.get('account.account').browse(self.cr,\
                self.uid,self.ids[0])        

    def numf(self,val):
        if val == 0.0:
            return "0,00"
        return locale.format("%0.2f",val,grouping=True)

    def lines(self, form, ids={}, done={}, level=1):
        if not ids:
            done = {}
            ids = self.ids
        if not ids:
            return []

        ctx = self.context.copy()
        ctx['fiscalyear'] = form['fiscalyear']

        acc_set = ",".join(map(str, ids))
        query = self.pool.get('account.move.line')._query_get(self.cr, self.uid, context=ctx)
        query = "%s and l.date < '%s'" % (query,form.get('date_start'))
        query=  "SELECT a.code, COALESCE(SUM(l.credit*a.sign),0),COALESCE(SUM(l.debit*a.sign),0) " + \
            "FROM account_account a LEFT JOIN account_move_line l ON (a.id=l.account_id) " + \
            "WHERE a.type!='view' AND a.id IN (%s) AND %s GROUP BY a.code order by a.code" % (acc_set,query)
        self.cr.execute(query)
        rprev={}
        for account,credit,debit in self.cr.fetchall():
            rprev[account]=(credit,debit)
        query = self.pool.get('account.move.line')._query_get(self.cr, self.uid, context=ctx)
        query = "%s and l.date between '%s' and '%s'" % (query,form.get('date_start'),form.get('date_end'))
        query=  "SELECT a.code, COALESCE(SUM(l.credit*a.sign),0),COALESCE(SUM(l.debit*a.sign),0) " + \
            "FROM account_account a LEFT JOIN account_move_line l ON (a.id=l.account_id) " + \
            "WHERE a.type!='view' AND a.id IN (%s) AND %s GROUP BY a.code order by a.code" % (acc_set,query)
        self.cr.execute(query)
        ract={}
        for account,credit,debit in self.cr.fetchall():
            ract[account]=(credit,debit)
        result = []
        code_min = form.get('code_start',' ')
        code_max = form.get('code_end','ZZZZZZZZZZ')
        detail = form.get('detail')
        accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids, ctx)
        accounts.sort(lambda x,y: cmp(x.code,y.code))
        for account in accounts:
            if account.id in done:
                continue
            if not account.active:
                continue
            prev= account.code in rprev and rprev[account.code] or (0,0)
            act= account.code in ract and ract[account.code] or (0,0)
            done[account.id] = 1
            res = {
                'code': account.code,
                'name': account.name,
                'level': level,
                'prev_balance': round(prev[1] - prev[0],2),
                'debit': round(act[1],2),
                'credit': round(act[0],2),
                'balance': round(act[1] - act[0],2),
                'act_debit': round(prev[1] + act[1],2),
                'act_credit': round(prev[0] + act[0],2),
                'act_balance':  round(prev[1] - prev[0] + act[1] - act[0],2),
            }
            if not res['prev_balance'] and \
               not res['debit'] and \
               not res['credit'] and \
               not res['balance'] and \
               not res['act_debit'] and \
               not res['act_credit'] and \
               not res['act_balance'] and \
               not account.child_id:
                continue
            if account.code >= code_min and account.code <= code_max:
                result.append(res)
                self.sums['prev_balance'] += res['prev_balance']
                self.sums['debit'] += res['debit']
                self.sums['credit'] += res['credit']
                self.sums['balance'] += res['balance']
                self.sums['act_debit'] += res['act_debit']
                self.sums['act_credit'] += res['act_credit']
                self.sums['act_balance'] += res['act_balance']
            #print "%15s %d" % (account.code,account.id)
            if detail or account.code.startswith('B') or \
                   account.code.startswith('E')  or account.code == '0':
                if account.child_id:
                    ids2 = [(x.code,x.id) for x in account.child_id]
                    ids2.sort()
                    result += self.lines(form, [x[1] for x in ids2], done, level+1)
        return result

    def totals(self):
        return self.sums

report_sxw.report_sxw('report.account.account.situation_balance', 'account.account', 'addons/account/report/account_balance.rml', parser=account_balance_simple)
report_sxw.report_sxw('report.carreras.balance_detail', 'account.account', 'addons/carreras/report/balance_detail.rml', parser=account_balance_detail)
