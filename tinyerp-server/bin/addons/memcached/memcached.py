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
import memcache
from osv import osv

mc = memcache.Client(['127.0.0.1:11212'], debug=0)
mc.flush_all()

import threading
recursive_protect = threading.local()

class osv(osv.osv):

    def get_mc_key(self,cr,uid,args=[],context={}):
        """ the key is dbname:table:keys """
        keys = [cr.dbname,self._name]
        keys.extend([str(key) for key in args])
        if context:
            keys.append(str(hash( str(context) )))
        return ":".join(keys) + ":"

    def import_data(self, cr, uid, fields, datas,  mode='init',
                current_module=None, noupdate=False, context=None):
        val = super(osv,self).import_data(cr, uid, fields, datas,  mode,
                    current_module, noupdate, context)
        mc.flush()
        return val


    def read(self, cr, user, ids, fields=None, context=None,
                    load='_classic_read'):
        if fields:
            fields.append('id')

        key_prefix = self.get_mc_key(cr,user,context=context)
        val = mc.get_multi(ids,key_prefix=key_prefix)
        if val:
            ok = True
            keys = val.keys()
            res = []
            for id in ids:
                if id not in keys:
                    ok = False
                if id in keys:
                    if fields:
                        data = dict([(field,val[id][field]) for field in fields])
                    else:
                        data = val[id]
                    res.append(data)
            if ok:
                #print 'memcached_get:'+key_prefix+' %d keys' % (len(ids))
                return res
        # Only cache big querys
        if not getattr(recursive_protect,'read',False):
            fields = None
            recursive_protect.read = True

        val = super(osv,self).read(cr, user, ids, fields, 
                    context,load)
                    
        # Only cache big querys
        if not fields:
            data = dict(zip(ids,val))
            #print 'memcached_set:'+key_prefix+' %d keys' % (len(ids))
            mc.set_multi(data,key_prefix=key_prefix)
            recursive_protect.read = False
        return val

#	def default_get(self, cr, uid, fields, context=None):
#	    ES POT FER PERO PERDS EL POSATS PER L'USUARI

#	def perm_read(self, cr, user, ids, context=None, details=True):
    def unlink(self, cr, uid, ids, context=None):
        val = super(osv,self).unlink(cr, user, ids,context)
        key_prefix = self.get_mc_key(cr,user,context=context)
        mc.delete_multi(ids,key_prefix=key_prefix)
        return val

    def write(self, cr, user, ids, vals, context=None):
        val = super(osv,self).write(cr, user, ids,vals,context)
        key_prefix = self.get_mc_key(cr,user,context=context)
        mc.delete_multi(ids,key_prefix=key_prefix)
        return val

    def fields_get(self, cr, user, fields=None, context=None):
        key_prefix = self.get_mc_key(cr,user,['fields_get'],context=context)
        if fields:
            val = mc.get_multi(fields,key_prefix=key_prefix)
        if fields and val:
            #print 'memcached_get:'+key_prefix+' %d keys' % len(val)
            notfound = []
            for f in fields:
                if f not in val:
                    notfound.append(f)
            if len(notfound) == 0:
                return val
        else:
            notfount = fields
            val = {}
        val2 = super(osv,self).fields_get(cr, user, fields,context)
        mc.set_multi(val2,key_prefix=key_prefix)
        #print 'memcached_set:'+key_prefix+' %d keys' % len(val2)
        val.update(val2)
        return val
    
##	def view_header_get(self, cr, user, view_id=None, view_type='form',
##context=None):

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                    context=None, toolbar=False):
        key = self.get_mc_key(cr,user,['fields_view_get',
                            view_id,view_type,toolbar],context=context)
        val = mc.get(key)
        if val:
            #print 'memcached_get:'+key
            return val
        val = super(osv,self).fields_view_get(cr, user, view_id, view_type,
                    context, toolbar)
        mc.set(key,val)
        #print 'memcached_set:'+key
        return val

##	def name_get(self, cr, user, ids, context=None):
##	def name_search(self, cr, user, name='', args=None, operator='ilike',
##context=None, limit=80):
##	def copy(self, cr, uid, id, default=None, context=None):

##	def read_string(self, cr, uid, id, langs, fields=None, context=None):
##	    READ / UPDATE
##	def write_string(self, cr, uid, id, langs, vals, context=None):
##	    INVALIDATE O SET ???
##	def check_recursion(self, cr, uid, ids, parent=None):


