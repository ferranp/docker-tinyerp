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
import pooler 
import os.path

def fbackup(fitxer=False):
    if fitxer and os.path.isfile(fitxer):
        return open(fitxer)
    if os.path.isfile('/opt/public/cachebak/BACKUP'):
        return open('/opt/public/cachebak/BACKUP')
    if os.path.isfile('/opt/docs/Carreras/BACKUP'):
        return open('/opt/docs/Carreras/BACKUP')
    return False

_companies = {}
def get_company(cr,uid,name):
    pool = pooler.get_pool(cr.dbname)
    #if name not in ('TL','TJ','TC','BD'):
    #    return False
    if name in _companies:
        return _companies[name]
    s = [('short_name','=',name)]
    d = pool.get('res.company').search(cr,uid, s)
    if d:
        _companies[name] = d[0]
        return d[0]
    _companies[name] = False
    return False


complete_fields = {}
complete_form = '''<?xml version="1.0"?>
<form string="Proces de carrega">
    <label string="Proces finalitzat" colspan="4"/>
</form>'''

