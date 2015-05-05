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
import time
import netsvc
from osv import fields, osv

from tools.misc import currency

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

logger = netsvc.Logger()

"""
  formes de pagament
  Calcul de forma de pagament amb el nou tipus de calcul de mesos
"""
class account_payment_term_type(osv.osv):
    _name = "account.payment.term.type"
    _description = "Tipus de formes de pagament"
    _columns = { 
        'code' : fields.char('Codi',size=10,required=True),
        'name' : fields.char('Nom',size=20,required=True),
    }
    
account_payment_term_type()

class account_payment_term(osv.osv):
    _name = "account.payment.term"
    _inherit = "account.payment.term"

    def _get_types(self, cr, uid, context={}):
        obj = self.pool.get('account.payment.term.type')
        ids = obj.search(cr, uid, [])
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        res = [(r['code'], r['name']) for r in res]
        return res

    _columns = { 
        'type' : fields.selection(_get_types, 'Tipus',size=10, required=True),
    }
    
    def compute(self, cr, uid, id, value, date_ref=False, context={}):
        
        if not date_ref:
            date_ref = now().strftime('%Y-%m-%d')
        pt = self.browse(cr, uid, id, context)
        amount = value
        result = []
        for line in pt.line_ids:
            if line.value=='fixed':
                amt = line.value_amount
            elif line.value=='procent':
                amt = round(amount * line.value_amount,2)
            elif line.value=='balance':
                amt = amount
            if amt:
                next_date = mx.DateTime.strptime(date_ref, '%Y-%m-%d') + RelativeDateTime(days=line.days)
                if line.condition == 'end of month':
                    next_date += RelativeDateTime(day=-1)
                elif line.condition == 'months':
                    next_date = mx.DateTime.strptime(date_ref, '%Y-%m-%d')
                    day= next_date.day
                    next_date = next_date + RelativeDateTime(day=1)
                    next_date = next_date + RelativeDateTime(months=line.days)
                    next_date = mx.DateTime.DateTime(
                                            next_date.year,
                                            next_date.month,
                                            self._adjust_day(next_date,day))
                    
                    #day= next_date.day
                    #next_date = next_date + RelativeDateTime(day=1)
                    #next_date = next_date + RelativeDateTime(months=line.days+1)
                    #next_date = next_date - RelativeDateTime(days=1)
                    #if day < next_date.day:
                    #    next_date = next_date + RelativeDateTime(day=day)
                    
                    #month=next_date.month + line.days
                    #if month > 12:
                    #    month = month - 12
                    #next_date = next_date + RelativeDateTime(months=line.days)
                    # bug del febrer
                    #if next_date.month > month:
                    #    next_date = next_date + RelativeDateTime(day=1)
                    #    next_date = next_date + RelativeDateTime(days=-1)
                
                if context.get('partner_id',False):
                    # Si tinc partner, ajusto dia de pagament i periode no pago
                    next_date = self._adjust_partner(cr,uid,next_date,context['partner_id'])
                
                result.append( (next_date.strftime('%Y-%m-%d'), amt) )
                amount -= amt
        return result
    
    def _adjust_partner(self,cr,uid,next_date,partner_id):
        partner = self.pool.get('res.partner').browse(cr,uid,partner_id)
        
        pay_days = filter(None,[partner.pay_day1,partner.pay_day2,partner.pay_day3])
        pay_days.sort()
        
        if len(pay_days):
            day = 0
            for d in pay_days:
                if d >= next_date.day:
                    day = d
                    break
            if day == 0:
                next_date = next_date + RelativeDateTime(day=1)
                next_date = next_date + RelativeDateTime(months=+1)
                day = pay_days[0]
            next_date = mx.DateTime.DateTime(next_date.year,
                                             next_date.month,
                                             self._adjust_day(next_date,day))

        # periode no pago
        if partner.start_no_pay and partner.end_no_pay:
            start = partner.start_no_pay.split('-')[1:]
            start = mx.DateTime.DateTime(next_date.year,int(start[0]),int(start[1]))
            end = partner.end_no_pay.split('-')[1:]
            end = mx.DateTime.DateTime(next_date.year,int(end[0]),int(end[1]))
            if next_date > start and next_date < end:
                next_date = end + RelativeDateTime(days=+1)
                # si la data ha caigut en el periode de no pago es torna a mirar
                # el dia de pagament
                if len(pay_days):
                    day=0
                    for d in pay_days:
                        if d >= next_date.day:
                            day = d
                            break
                    if day == 0:
                        next_date = next_date + RelativeDateTime(day=1)
                        next_date = next_date + RelativeDateTime(months=+1)
                        day = pay_days[0]
                    
                    next_date = mx.DateTime.DateTime(next_date.year,
                                                     next_date.month,
                                                     self._adjust_day(next_date,day))

        return next_date

    def _adjust_day(self,next_date,day):
        max_date = next_date + RelativeDateTime(months=+1,day=1) 
        max_date = max_date - RelativeDateTime(days=1)
        if day > max_date.day:
            return max_date.day
        return day

account_payment_term()
"""
  Linies formes de pagament
  Nou tipus de interval per mesos
"""
class account_payment_term_line(osv.osv):
    _name = "account.payment.term.line"
    _inherit = "account.payment.term.line"
    _columns = {
        'days': fields.integer('Numero de dies/mesos',required=True),
        'condition': fields.selection([('months','Mesos'),('net days','Net Days'),('end of month','End of Month')], 'Condition', required=True, help="The payment delay condition id a number of days expressed in 2 ways: net days or end of the month. The 'net days' condition implies that the paiment arrive after 'Number of Days' calendar days. The 'end of the month' condition requires that the paiement arrives before the end of the month that is that is after 'Number of Days' calendar days."),
    }

account_payment_term_line()

