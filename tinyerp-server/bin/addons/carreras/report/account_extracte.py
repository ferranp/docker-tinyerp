# -*- coding: utf-8 -*-
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
  Fa el llistat de un extracte de un compte 
"""
import pooler
import time
import locale
import netsvc
from report import report_sxw
locale.setlocale(locale.LC_ALL, '')
_real_localeconv = locale.localeconv
def localeconv():
    d = _real_localeconv()
    d['grouping'] = [3, 3, 0]
    d['thousands_sep'] = '.'
    return d

locale.localeconv = localeconv

"""
    account_extracte
    account_extracte2 -> no es fa servir
    account_pending_payment

"""
class account_extracte2(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_pending_payment, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_accounts': self.get_accounts,
            'saldo': self.saldo,
            'format_date': self.format_date,
            'lines': self.lines,
            'totals': self.totals,
        })
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        super(account_pending_payment, self).preprocess(objects, data, ids)
        self.proc_lines()

    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)

    def saldo(self,l=None):
        if l:
            self.saldo = self.saldo - l.credit + l.debit
        return self.numf(self.saldo)

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_accounts(self):
        if len(self.ids) == 1:
            o=self.objects[0]
            return "Compte %s - %s" % (o.code,o.name)

        max_code=self.objects[0].code
        min_code=self.objects[0].code
        for o in self.objects:
            if o.code > max_code:
                max_code=o.code
            if o.code < min_code:
                min_code=o.code
        return "Comptes %s - %s" % (min_code,max_code)
        logger= netsvc.Logger()
        logger.notifyChannel("info", netsvc.LOG_INFO,self.objects)
        logger.notifyChannel("info", netsvc.LOG_INFO,self.objects[-1])

    def proc_lines(self):
        fy = self.datas['form']['fiscalyear_id']
        periods = self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',fy)])

        s=[]
        s.append(('account_id','in',self.ids))
        s.append(('period_id','in',periods))
        s.append(('date','>=',self.datas['form']['date_start']))
        s.append(('date','<=',self.datas['form']['date_end']))
        if self.datas['form']['entries']=='no':
            s.append(('reconcile_id','=',False))

        l_obj = self.pool.get('account.move.line')
        ids = l_obj.search(self.cr,self.uid,s)
        
        #logger= netsvc.Logger()
        lines=[]
        for l in l_obj.browse(self.cr,self.uid,ids):
            line=[]
            line.append(l.account_id.code)
            line.append(l.date)
            line.append(l.move_id.name)
            line.append(l.name)
            #line.append(l.partner_id and l.partner_id.name[0:20].decode('utf8') or '')
            line.append(l.ref and l.ref or '')
            line.append(l.date_maturity)
            line.append(l.debit)
            line.append(l.credit)
            lines.append(line)
        
        lines.sort(lambda x,y: cmp(x[2],y[2]))
        lines.sort(lambda x,y: cmp(x[1],y[1]))
        lines.sort(lambda x,y: cmp(x[0],y[0]))
        
        lins=[]
        lins.append(['','','','','','','','',''])
        last_account=False
        sum_debit=0
        sum_credit=0
        saldo=0
        self.tot_debit=0
        self.tot_credit=0
        for l in lines:
            #logger.notifyChannel("info", netsvc.LOG_INFO,l)
            if last_account and last_account != l[0]:
                lins.append([
                    last_account,'','','','','',
                    sum_debit and self.numf(sum_debit) or '',
                    sum_credit and self.numf(sum_credit) or '',
                    self.numf(saldo)])
                lins.append(['','','','','','','','',''])
                self.tot_debit+=sum_debit
                self.tot_credit+=sum_credit
                sum_debit=0
                sum_credit=0
                saldo=0
            
            last_account=l[0]
            sum_debit+=l[6]
            sum_credit+=l[7]
            saldo=sum_debit - sum_credit
            lins.append([
                l[0],
                self.format_date(l[1]),
                l[2],
                l[3],
                l[4],
                self.format_date(l[5]),
                l[6] and self.numf(l[6]) or '',
                l[7] and self.numf(l[7]) or '',
                self.numf(saldo)])

        lins.append([
            last_account,'','','','','',
            sum_debit and self.numf(sum_debit) or '',
            sum_credit and self.numf(sum_credit) or '',
            self.numf(saldo)])
        lins.append(['','','','','','','','',''])
        self.tot_debit+=sum_debit
        self.tot_credit+=sum_credit
            
        lins.append(['','','','','','','','',''])
        
        self.account_lines=lins
        return 

    def lines(self):
        return self.account_lines

    def totals(self):
        return [self.numf(self.tot_debit),
                self.numf(self.tot_credit),
                self.numf(self.tot_debit - self.tot_credit)]


class account_extracte(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_extracte, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_account': self.get_account,
            'inicial': self.inicial,
            'total': self.total,
            'format_date': self.format_date,
            'lines': self.lines,
        })

    def preprocess(self, objects, data, ids):
        l_obj = self.pool.get('account.move.line')
        account = data['form']['account_id']
        fy = data['form']['fiscalyear_id']
        periods = self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',fy)])
        
        self.saldo = 0.0
        s = [('account_id','=',account),('period_id','in',periods)]
        s.append(('date','<',data['form']['date_start']))
        s.append(('state','<>','draft'))
        ids = l_obj.search(self.cr,self.uid,s,order='date,id')
        for l in l_obj.read(self.cr,self.uid,ids,['debit','credit']):
            self.saldo = self.saldo - l['credit'] + l['debit']
        self.inicial=self.saldo
        
        super(account_extracte, self).preprocess(objects, data, ids)
    
    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)

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
        l_obj = self.pool.get('account.move.line')
        account = self.datas['form']['account_id']
        fy = self.datas['form']['fiscalyear_id']
        periods = self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',fy)])
        
        """
        self.saldo = 0.0
        s = [('account_id','=',account),('period_id','in',periods)]
        s.append(('date','<',self.datas['form']['date_start']))
        s.append(('state','<>','draft'))
        ids = l_obj.search(self.cr,self.uid,s,order='date,id')
        for l in l_obj.read(self.cr,self.uid,ids,['debit','credit']):
            self.saldo = self.saldo - l['credit'] + l['debit']
        """
        
        s = [('account_id','=',account),('period_id','in',periods)]
        s.append(('date','>=',self.datas['form']['date_start']))
        s.append(('date','<=',self.datas['form']['date_end']))
        s.append(('state','<>','draft'))
        ids = l_obj.search(self.cr,self.uid,s,order='date,id')
        
        lines=[]
        for l in l_obj.browse(self.cr,self.uid,ids):
            row=[]
            row.append(self.format_date(l.date))
            row.append(l.move_id.name)
            row.append(l.name.decode('utf8')[0:30])
            row.append(l.ref)
            row.append(self.format_date(l.date_maturity))
            row.append((l.debit != 0.0) and self.numf(l.debit))
            row.append((l.credit != 0.0) and  self.numf(l.credit))
            self.saldo = self.saldo - l.credit + l.debit
            row.append(self.numf(self.saldo))
            lines.append(row)
        return lines

    def total(self):
        return self.numf(self.saldo)

    def inicial(self):
        return self.numf(self.inicial)

class account_pending_payment(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(account_pending_payment, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'locale': locale,
            'numf': self.numf,
            'get_accounts': self.get_accounts,
            'format_date': self.format_date,
            'lines': self.lines,
            'caps': self.caps,
            'total': self.total,
            'get_bank': self.get_bank,
        })
        self.logger= netsvc.Logger()
        self.saldo = 0.0

    def preprocess(self, objects, data, ids):
        self.account_lines=[]
        self.tot_debit=0
        self.tot_credit=0
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'preprocess')
        super(account_pending_payment, self).preprocess(objects, data, ids)
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'proclines')
        self.proc_lines()
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'proclines')

    def numf(self,val):
        return locale.format("%0.2f",val,grouping=True)

    def format_date(self,date):
        if date and len(date) > 5:
            date1 = date.split('-')
            return date1[2] + '-' + date1[1] + '-' + date1[0]
        else:
            return ""

    def get_accounts(self):
        return ""
        if len(self.ids) == 1:
            o=self.objects[0]
            return "Compte %s - %s" % (o.code,o.name)

        max_code=self.objects[0].code
        min_code=self.objects[0].code
        for o in self.objects:
            if o.code > max_code:
                max_code=o.code
            if o.code < min_code:
                min_code=o.code
        return "Comptes %s - %s" % (min_code,max_code)

    def proc_lines(self):
        #logger= netsvc.Logger()
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'hola')
        fy = self.datas['form']['fiscalyear_id']
        periods = self.pool.get('account.period').search(self.cr,self.uid,[('fiscalyear_id','=',fy)])
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,periods)

        query= "SELECT a.code,l.ref,l.date_maturity,a.name,l.name,i.date_supplier,l.debit,l.credit " +\
                "FROM account_account a, account_move_line l LEFT JOIN account_invoice i " +\
                "ON (l.move_id = i.move_id) WHERE " +\
                "l.account_id = a.id AND " +\
                "l.period_id IN ("+','.join(map(str,periods))+") AND " +\
                "l.reconcile_id IS NULL AND " +\
                "a.company_id = '%d' AND " % (self.datas['form']['company_id']) +\
                "a.code BETWEEN '%s' AND '%s'" % (self.datas['form']['account_1'],self.datas['form']['account_2'])
        
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,query)
        self.cr.execute(query)
        #logger= netsvc.Logger()
        
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'adeu')
        #vector=
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,vector)
        # generar partides vives
        vives={}
        for l in self.cr.fetchall():
            key=(l[0],l[1])
            print key
            #self.logger.notifyChannel("info", netsvc.LOG_INFO,l)
            if key not in vives:
                line=list(l)
                line.append(l[6]-l[7])
            else:
                line=vives[key]
                if not line[2] and l[2]:
                    line[2]=l[2]
                line[6]+=l[6]
                line[7]+=l[7]
                line[8]+= l[6] - l[7]
            vives[key]=line
        
        lines=vives.values()

        # només càrrec, abonament o saldo
        if self.datas['form']['type']=='A':
            index=6
        elif self.datas['form']['type']=='C':
            index=7
        else:
            index=8
        lines=map(lambda x: x[:-3]+[x[index]],lines)

        # filtres per venciment i import
        lines=filter(lambda x: x[2] >= self.datas['form']['date_1'] and x[2] <= self.datas['form']['date_2'], lines)
        lines=filter(lambda x: x[6] >= self.datas['form']['import_1'] and x[6] <= self.datas['form']['import_2'], lines)

        # ordenar per venciment, compte o import
        if self.datas['form']['order']=='V':
            lines.sort(lambda x,y: cmp(x[1],y[1]))
            lines.sort(lambda x,y: cmp(x[0],y[0]))
            lines.sort(lambda x,y: cmp(x[2],y[2]))
            k=2
        if self.datas['form']['order']=='C':
            lines.sort(lambda x,y: cmp(x[1],y[1]))
            lines.sort(lambda x,y: cmp(x[2],y[2]))
            lines.sort(lambda x,y: cmp(x[0],y[0]))
            k=0
        if self.datas['form']['order']=='I':
            lines.sort(lambda x,y: cmp(x[0],y[0]))
            lines.sort(lambda x,y: cmp(x[2],y[2]))
            lines.sort(lambda x,y: cmp(x[6],y[6]))
            k=6

        lins=[]
        lins.append(['','','','','','',''])
        last_key=False
        sum=0
        self.tot_sum=0
        for l in lines:
            #self.logger.notifyChannel("info", netsvc.LOG_INFO,l)
            if k!=6 and last_key and last_key != l[k]:
                lins.append([
                    '','','',
                    k and ("Total Venciment %s" % self.format_date(last_key)) or ("Total Compte %s" % last_key),
                    '','',
                    sum and self.numf(sum) or ''])
                lins.append(['','','','','','',''])
                sum=0

            last_key=l[k]
            sum+=l[6]
            self.tot_sum+=l[6]
            
            lins.append([
                l[0],
                l[1],
                self.format_date(l[2]),
                l[3],
                l[4],
                self.format_date(l[5]),
                l[6] and self.numf(l[6]) or ''])

        if k!=6 and last_key:
            lins.append([
                '','','',
                k and ("Total Venciment %s" % self.format_date(last_key)) or ("Total Compte %s" % last_key),
                '','',
                sum and self.numf(sum) or ''])
        lins.append(['','','','','','',''])
        
        self.account_lines=lins
        return 

    def lines(self):
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'lines')
        return self.account_lines

    def caps(self):
        return []

    def get_bank(self):
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'bank')
        if not self.datas['form']['channel_id']:
            return " "
        channel=self.pool.get('account.receivable.channel').browse(self.cr,self.uid,self.datas['form']['channel_id'])
        ccc=channel.code.strip().replace('.','').replace('-','')
        return "%s  ag.%s ct.%s" % (channel.name,ccc[4:8],ccc[10:20])

    def total(self):
        #self.logger.notifyChannel("info", netsvc.LOG_INFO,'total')
        return self.tot_sum and self.numf(self.tot_sum) or ''

report_sxw.report_sxw('report.account.extracte', 'account.move.line', 'addons/carreras/report/account_extracte.rml',parser=account_extracte)
report_sxw.report_sxw('report.account.pending.payment', 'account.account', 'addons/carreras/report/account_pending_payment.rml',parser=account_pending_payment)
