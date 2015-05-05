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
  Crea un fitxer de norma 58 de la remesa seleccionada
"""
import time
import StringIO
import base64   
import wizard
import pooler 
import netsvc
import mx
import os,stat
from tools.misc import UpdateableStr
logger = netsvc.Logger()
#
# format dels registres de la norma 58
#
formats_58 ={
    '51': {
        'A1':(1,2),
        'A2':(3,2),
        'B1':(5,12),
        'B2':(17,6),
        'B3':(23,6),
        'C':(29,40),
        'D':(69,20),
        'E1':(89,4),
        'E2':(93,4),
        'E3':(97,12),
        'F':(109,40),
        'G':(149,14),
    },
    '53': {
        'A1':(1,2),
        'A2':(3,2),
        'B1':(5,12),
        'B2':(17,6),
        'B3':(23,6),
        'C':(29,40),
        'D':(69,20),
        'E1':(89,8),
        'E2':(97,2),
        'E3':(99,10),
        'F':(109,40),
        'G':(149,14),
    },
    '5670': {
        'A1':(1,2),
        'A2':(3,2),
        'B':(5,20),
            'B1':(5,12),
            'B2':(17,6),
        'C':(29,40),
        'D':(69,20),
            'D1':(69,4),
            'D2':(73,4),
            'D3':(77,2),
            'D4':(79,10),
        'E':(89,10),
        'F':(99,16),
            'F1':(99,6),
            'F2':(105,10),
        'G':(115,40),
        'H':(155,8),
            'H1':(155,6),
            'H2':(161,2),
    },
    '56': {
        'A1':(1,2),
        'A2':(3,2),
        'B':(5,20),
            'B1':(5,12),
            'B2':(17,6),
        'C':(29,40),
        'D':(69,40),
        'E':(109,40),
        'F':(149,14),
    },
    '5676': {
        'A1':(1,2),
        'A2':(3,2),
        'B':(5,20),
            'B1':(5,12),
            'B2':(17,6),
        'C':(29,40),
        'D':(69,40),
            'D1':(69,35),
            'D2':(104,5),
        'E':(109,40),
            'E1':(109,38),
            'E2':(147,2),
        'F':(149,14),
            'F1':(149,6),
            'F2':(155,8),
    },
    '58': {
        'A1':(1,2),
        'A2':(3,2),
        'B':(5,20),
            'B1':(5,12),
            'B2':(17,6),
        'C':(29,40),
        'D':(69,20),
            'D1':(69,4),
            'D2':(73,16),
        'E':(89,16),
            'E1':(89,10),
            'E2':(99,6),
        'F':(105,20),
            'F1':(105,10),
            'F2':(115,10),
    },
    '59': {
        'A1':(1,2),
        'A2':(3,2),
        'B':(5,20),
            'B1':(5,12),
            'B2':(17,6),
        'C':(29,40),
        'D':(69,20),
            'D1':(69,4),
            'D2':(73,16),
        'E':(89,16),
            'E1':(89,10),
            'E2':(99,6),
        'F':(105,20),
            'F1':(105,10),
            'F2':(115,10),
    },
}

pairs= [("ç","c"),("Ç","C"),("ñ","n"),("Ñ","N"),
        ("à","a"),("À","A"),("á","a"),("Á","A"),
        ("ò","o"),("Ò","O"),("ó","o"),("Ó","O"),
        ("è","e"),("È","E"),("é","e"),("É","E"),
        ("í","i"),("Í","I"),("ú","u"),("Ú","U"),
        ("º","o"),("ª","a"),
        ]

class Lin58(object):
    def __init__(self):
        pass
        
    def write_line(self,buff):
        lin = " " * 162
        reg = self.A1
        format = formats_58.get(self.A1 + self.A2,formats_58[reg])
        for item,pos_len in format.items():
            pos = pos_len[0] - 1
            l = pos_len[1]
            if hasattr(self,item):
                w= getattr(self,item)
                for old,new in pairs:
                    w= w.replace(old,new)
                w= w.decode('utf-8').encode('ascii','replace')
                if len(w) < l:
                    diff = l - len(w)
                    w = w + " " * diff
                lin = lin[:pos] + w[:l] + lin[pos + l:]
        
        buff.write(lin + '\n')
        

def norma58(cr, uid,buff,rem,data_norma58):
    pool = pooler.get_pool(cr.dbname)

    d58 = pool.get('account.receivable.norma58').read(cr,uid,[data_norma58])[0]

    total_amount = 0.0
    num_total = 0
    num_regs = 0

    # 51 70
    reg = Lin58()
    reg.A1 = '51'
    reg.A2 = '70'
    reg.B1 = d58['presentador']+d58['suf_pre']
    #reg.B2 = time.strftime('%d%m%y')
    reg.B2 = mx.DateTime.strptime(rem.date, '%Y-%m-%d').strftime('%d%m%y')
    reg.C = d58['nom_pre']
    reg.E1 = d58['ent_rec']
    reg.E2 = d58['ofi_rec']
    #reg.F = d58['ident1'][:14]
    reg.F = d58['ident1']
    reg.write_line(buff)
    num_regs += 1
    
    # 53,70
    reg = Lin58()
    reg.A1 = '53'
    reg.A2 = '70'
    id_ord=d58['ordenant']+d58['suf_ord']
    reg.B1 = id_ord
    #reg.B2 = time.strftime('%d%m%y')
    reg.B2 = mx.DateTime.strptime(rem.date, '%Y-%m-%d').strftime('%d%m%y')
    reg.C = d58['nom_ord']
    # el compte es xxxx.xxxx.xx.xxxxxxxxxx
    reg.D = d58['bank_acc'].replace('.','').replace('-','')
    reg.E2 = '06'
    #reg.F = d58['ident2'][:14]
    reg.F = d58['ident1']
    reg.G2 = d58['cod_ine']
    reg.write_line(buff)
    num_regs += 1

    for recv in rem.receivable_ids:
        num_total += 1
        referencia = recv.account_id.code[4:8]
        # 56,70
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '70'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = recv.partner_id and recv.partner_id.name or (recv.invoice_id and recv.invoice_id.partner_id.name or ' ')

        ccc = ''
        if recv.bank_id:
            ccc = recv.bank_id.acc_number
        else:
            if recv.partner_id:
                par = pool.get('res.partner').browse(cr,uid,[recv.partner_id.id])[0]
                if par.bank_ids and len(par.bank_ids):
                    ccc = par.bank_ids[0].acc_number
        
        ccc = ccc.strip().replace('.','').replace('-','')
        
        if len(ccc) == 0:
            reg.D="00000000000000000000"
        else:
            reg.D = ccc
        str_amount=str(recv.amount).split('.')
        reg_e=str_amount[0]+str_amount[1]+((2-len(str_amount[1]))*"0")
        reg.E = reg_e.zfill(10)
        # cliente
        #reg.F1 = referencia #codi per devolucions
        reg.F2 = recv.invoice_id and recv.invoice_id.name or recv.name
        reg.G = recv.invoice_id and "Factura %s del %s" % \
            (recv.invoice_id.name, \
            mx.DateTime.strptime(recv.invoice_id.date_invoice,'%Y-%m-%d').strftime('%d-%m-%Y')) or \
            ("Pagament %s" % recv.name)
        reg.H1 = mx.DateTime.strptime(recv.date_maturity, '%Y-%m-%d').strftime('%d%m%y')
        reg.write_line(buff)
        num_regs += 1
        """
        # 56,71
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '71'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = "concepto 2"
        reg.D = "concepto 3"
        reg.E = "concepto 4"
        reg.write_line(buff)
        num_regs += 1
        # 56,72
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '72'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = "concepto 5"
        reg.D = "concepto 6"
        reg.E = "concepto 7"
        reg.write_line(buff)
        num_regs += 1
        # 56,73
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '73'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = "concepto 8"
        reg.D = "concepto 9"
        reg.E = "concepto 10"
        reg.write_line(buff)
        num_regs += 1
        # 56,74
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '74'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = "concepto 11"
        reg.D = "concepto 12"
        reg.E = "concepto 13"
        reg.write_line(buff)
        num_regs += 1
        # 56,75
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '75'
        reg.B1 = id_ord
        reg.B2 = referencia
        reg.C = "concepto 14"
        reg.D = "concepto 15"
        reg.E = "concepto 16"
        reg.write_line(buff)
        num_regs += 1
        """
        # 56,76
        reg = Lin58()
        reg.A1 = '56'
        reg.A2 = '76'
        reg.B1 = id_ord
        reg.B2 = referencia
        
        a_id = pool.get('res.partner').address_get(cr,uid,[recv.partner_id.id],['invoice'])
        a_id  = a_id['invoice']
        addr = pool.get('res.partner.address').browse(cr,uid,[a_id])[0]
        
        reg.C = " ".join(filter(None,(addr.street,addr.street2))) 
        reg.C.strip()
        reg.D1 = addr.city
        reg.D2 = addr.zip
        reg.E1 = addr.city
        reg.E2 = addr.zip[0:2]
        if recv.invoice_id and recv.invoice_id.date_invoice:
            reg.F1 = mx.DateTime.strptime(recv.invoice_id.date_invoice, '%Y-%m-%d').strftime('%d%m%y')
        else:
            reg.F1 = "      "
        total_amount = total_amount + recv.amount
        reg.write_line(buff)
        num_regs += 1

    str_amount=str(total_amount).split('.')
    reg_e1=str_amount[0]+str_amount[1]+((2-len(str_amount[1]))*"0")
    
    # 58,70
    reg = Lin58()
    reg.A1 = '58'
    reg.A2 = '70'
    reg.B1 = id_ord
    #reg.E1 = ("%d" % int(total_amount * 100)).zfill(10) # 9(8)v99
    reg.E1 = reg_e1.zfill(10)# 9(8)v99
    reg.F1 = ("%d" % num_total).zfill(10)    # 9(10)
    reg.F2 = ("%d" % num_regs).zfill(10)     # 9(10)
    reg.write_line(buff)

    num_regs = num_regs + 2
    # 59,70
    reg = Lin58()
    reg.A1 = '59'
    reg.A2 = '70'
    reg.B1 = d58['presentador']+d58['suf_pre']
    reg.D1 = '0001'
    #reg.E1 = ("%d" % int(total_amount * 100)).zfill(10) # 9(8)v99
    reg.E1 = reg_e1.zfill(10)# 9(8)v99
    reg.F1 = ("%d" % num_total).zfill(10)    # 9(10)
    reg.F2 = ("%d" % num_regs).zfill(10)     # 9(10)
    reg.write_line(buff)

init_form = '''<?xml version="1.0"?>
<form string="Generar fitxer CSB Norma 58">
    <separator string="Es va a generar un fitxer de Norma 58 de la remesa seleccionada" colspan="4"/>
    <field name="data_norma58"/>
</form>'''

init_fields = {
    'data_norma58': {
        'string': 'Dades per a generar la norma',
        'type': 'many2one',
        'relation': 'account.receivable.norma58',
        'required': True,
    },
}

save_form = '''<?xml version="1.0"?>
<form string="Generar fitxer CSB Norma 58">
    <label string="Fitxer generat" colspan="4"/>
    <newline/>
    <field name="norma58" colspan="4"/>
</form>'''

save_fields = {
    'norma58': {
        'string': 'Fitxer',
        'type': 'binary',
        'readonly': True
    },
}

complete_fields = {}
complete_form= UpdateableStr()

class wizard_remittance_norma58(wizard.interface):
    def _set_default(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        if 'id' not in data or not data['id']:
            raise wizard.except_wizard('No es genera el fitxer N58',
                "La remesa no està creada")
        rem_obj=pool.get('account.receivable.remittance')
        rem= rem_obj.browse(cr,uid,[data['id']])[0]
        if rem.state == 'draft':
            raise wizard.except_wizard('No es genera el fitxer N58',
                "La remesa no està creada")
        rem_obj._validate_remittance(cr,uid,rem,'No es genera el fitxer N58')
        data['form']['data_norma58']=rem.channel_id.norma_58_id.id
        return data['form']

    def _gen_norma58(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        buf = StringIO.StringIO()
        rem = pool.get('account.receivable.remittance').browse(cr,uid,[data['id']])[0]
        norma58(cr,uid,buf,rem,data['form']['data_norma58'])
        
        user=pool.get('res.users').browse(cr, uid, uid)
        path='/home/%s/Remeses/' % user.login
        view=user.login
        if not os.path.isdir(path):
            os.system('sudo /bin/mkdir %s' % path)
            if not os.path.isdir(path):
                raise wizard.except_wizard('No es genera el fitxer N58', 
                    "No es pot crear el directori 'Remeses' de %s" % view)
        if not os.access(path,os.W_OK):
            os.system('sudo /bin/chmod a+w %s' % path)
            if not os.access(path,os.W_OK):
                raise wizard.except_wizard('No es genera el fitxer N58', 
                    "No es pot gravar el fixer de la norma al directori 'Remeses' de %s" % view)

        file= "R58" + rem.name.replace('/','')
        xml=['<?xml version="1.0"?>',
            '<form string="Norma 58">',
            '<label string="Fitxer %s gravat al directori \'Remeses\' de \'%s\'" colspan="4"/>' % (file,view),
            '</form>']
        complete_form.string='\n'.join(xml)

        f= open(path+file,'w')
        f.write(buf.getvalue())
        f.close()
        buf.close()
        stats=stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IROTH|stat.S_IWOTH
        os.chmod(path+file,stats)
        return data['form']

    states = {
        'init': {
            'actions': [_set_default], 
            'result': {'type':'form', 'arch':init_form, 'fields':init_fields, 'state':[('end','Cancelar'),('export','Continuar') ]}
        },
        'export': {
            'actions': [_gen_norma58], 
            'result': {'type':'form', 'arch':complete_form, 'fields':complete_fields, 'state':[('end','Tancar')]}
            #'result': {'type':'form', 'arch':save_form, 'fields':save_fields, 'state':[('end','Tancar')]}
        },
    }
wizard_remittance_norma58('remittance.norma58')
