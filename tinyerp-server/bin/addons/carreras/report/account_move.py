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

class account_move(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_move, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'fiscalyear': self.fiscalyear,
            'get_period': self.get_period,
            'get_moves': self.get_moves,
            'totals': self.totals,
        })
        self.context = context

    def preprocess(self, objects, data, ids):
        self.data =data
        self.process_lines()
        super(account_move, self).preprocess(objects, data, ids)
        
    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""
    def numf(self,val):
        if val == 0.0:
            return "0,00"
        return locale.format("%0.2f",val,grouping=True)

    def fiscalyear(self):
        return self.pool.get('account.fiscalyear').browse(self.cr,\
                self.uid,self.data['form']['fiscalyear'])        
    def get_period(self):
        return self.data['form']['date_start'] and "%s a %s" % (self.format_date(self.data['form']['date_start']),self.format_date(self.data['form']['date_end']))
    def get_moves(self):
        return self.data['form']['move_start'] and ("%s a %s" % (self.data['form']['move_start'],self.data['form']['move_end'])) or ' '


    def lines(self):
        return self.move_lines
    def process_lines(self):
        lines=[]
        spaces=[18]
        tcredit=0
        tdebit=0
        for move in self.pool.get('account.move').browse(self.cr,self.uid,self.data['form']['ids']):
            debit=0
            credit=0
            for i,line in enumerate(move.line_id):
                lines.append([
                    "%s-%03d" % (move.name,i),
                    self.format_date(line.date),
                    line.ref,
                    line.name,
                    line.account_id.code,
                    line.account_id.name.decode('utf8')[0:17],
                    self.numf(line.debit),
                    self.numf(line.credit),
                    line.journal_id.code
                    ])
                spaces.append(11)
                debit += line.debit
                credit += line.credit
            lines.append(['','','','*** TOTAL ***','','',
                self.numf(debit),self.numf(credit),''])
            spaces.append(18)
            tcredit += credit
            tdebit += debit
        spaces.append(18)
        
        self.line_spaces=spaces
        self.move_lines=lines
        self.sums=(self.numf(tdebit),self.numf(tcredit))
        return 

    def totals(self):
        return self.sums

    def _parse(self, rml_dom, objects, data, header=False):
        report_sxw.rml_parse._parse(self, rml_dom, objects, data, header)
        rowHeights=",".join(map(str,self.line_spaces))
        for elem in self.dom.getElementsByTagName("blockTable"):
            if elem.hasAttribute("style") and elem.getAttribute("style") == "Detall":
                elem.setAttribute("rowHeights",rowHeights)
                pass
            #if elem.hasAttribute("style") and elem.getAttribute("style") == "Cap":
            #    elem.setAttribute("rowHeights",("12,"*len(self.caps))[:-1])
                
        res = self.dom.documentElement.toxml('utf-8')
        return res

report_sxw.report_sxw('report.move.report', 'account.move', 'addons/carreras/report/move_report.rml', parser=account_move)
