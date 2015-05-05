##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
  Fa el llistat de quadre de efectes amb comptabilitat
"""
import pooler
import time
from report import report_sxw

class account_receivable_match(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_receivable_match, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'get_account': self.get_account,
        })
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        super(account_receivable_match, self).preprocess(objects, data, ids)
        a_obj = self.pool.get('account.account')
        code_min = a_obj.read(self.cr,self.uid,[self.datas['form']['account_start_id']],['code'])[0]['code']
        code_max = a_obj.read(self.cr,self.uid,[self.datas['form']['account_end_id']],['code'])[0]['code']
        c_id = self.pool.get('res.users').browse(self.cr, self.uid, self.uid).company_id.id
        self.cr.execute(("select id,name,code from account_account where " + 
                        "code between '%s' and '%s' and company_id=%d " +
                        " and type='receivable'") % (code_min , code_max , c_id))
        self.lins = []
        for acc in self.cr.dictfetchall():
            total_rec = self._sum_receivables(acc)
            total_mov = self._sum_moves(acc)
            if total_rec != total_mov:
                self.lins.append((acc,total_rec,total_mov))
    
    def get_account(self,acc):
        a_obj = self.pool.get('account.account')
        return a_obj.browse(self.cr,self.uid,[acc])[0]
        
    def _sum_receivables(self,acc):
        self.cr.execute("select sum(amount) from account_receivable where account_id=%d"\
                "and state<>'received'"%acc['id'])
        total =  self.cr.fetchone()
        if total and total[0]:
            return total[0]
        else:
            return 0.0

    def _sum_moves(self,acc):
        a_obj = self.pool.get('account.account')
        return a_obj.read(self.cr,self.uid,[acc['id']],['balance'])[0]['balance']        
        #self.cr.execute("select sum(credit - debit) from account_move_line where account_id=%d"%acc['id'])
        #total =  self.cr.fetchone()
        #if total and total[0]:
        #    return total[0]
        #else:
        #    return 0.0
    
    def lines(self):
        return self.lins


    
report_sxw.report_sxw('report.account.receivable.match', 'account.account', 'addons/account_receivable/report/receivable_match.rml',parser=account_receivable_match)

