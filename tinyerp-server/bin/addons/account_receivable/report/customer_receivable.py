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
  Llista cartera de un client/compte
"""
import pooler
import time
from report import report_sxw

class customer_receivable(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(customer_receivable, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'get_account': self.get_account,
            'format_date': self.format_date,
            'lines': self.lines,
        })
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        super(customer_receivable, self).preprocess(objects, data, ids)
    
    
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
        
        
    def get_account(self):
        a_obj = self.pool.get('account.account')
        account = self.datas['form']['account_id']
        return a_obj.browse(self.cr,self.uid,[account])[0]
    
    def lines(self):
        l_obj = self.pool.get('account.receivable')
        account = self.datas['form']['account_id']
        limits = [('account_id','=',account)]
        if self.datas['form']['state'] == 'pending':
            limits.append(('state','=','pending'))
        ids = l_obj.search(self.cr,self.uid,limits)
        return l_obj.browse(self.cr,self.uid,ids)


    
report_sxw.report_sxw('report.customer.receivable', 'account.account', 'addons/account_receivable/report/customer_receivable.rml',parser=customer_receivable)

