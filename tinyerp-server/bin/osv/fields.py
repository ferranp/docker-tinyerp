# -*- encoding: iso-8859-1 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id$
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

# . Fields:
#      - simple
#      - relations (one2many, many2one, many2many)
#      - function
#
# Fields Attributes:
#   _classic_read: is a classic sql fields
#   _type   : field type
#   readonly
#   required
#   size
#
import string
import netsvc

import psycopg
import warnings

import tools

def _symbol_set(symb):
	if symb==None or symb==False:
		return None
	elif isinstance(symb, unicode):
		return symb.encode('utf-8')
	return str(symb)

class _column(object):
	_classic_read = True
	_classic_write = True
	_properties = False
	_type = 'unknown'
	_obj = None
	_symbol_c = '%s'
	_symbol_f = _symbol_set
	_symbol_set = (_symbol_c, _symbol_f)
	_symbol_get = None

	def __init__(self, string='unknown', required=False, readonly=False, domain=None, context='', states=None, priority=0, change_default=False, size=None, ondelete="set null", translate=False, select=False, **args):
		self.states = states or {}
		self.string = string
		self.readonly = readonly
		self.required = required
		self.size = size
		self.help = args.get('help', '')
		self.priority = priority
		self.change_default = change_default
		self.ondelete = ondelete
		self.translate = translate
		self._domain = domain or []
		self.relate =False
		self._context = context
		self.group_name = False
		self.view_load = 0
		self.select=select
		for a in args:
			if args[a]:
				setattr(self, a, args[a])
		if self.relate:
			warnings.warn("The relate attribute doesn't work anymore, use act_window tag instead", DeprecationWarning)

	def restart(self):
		pass

	def set(self, cr, obj, id, name, value, user=None, context=None):
		cr.execute('update '+obj._table+' set '+name+'='+self._symbol_set[0]+' where id=%d', (self._symbol_set[1](value),id) )

	def get(self, cr, obj, ids, name, context=None, values=None):
		raise Exception, 'undefined get method !'

	def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None):
		ids = obj.search(cr, uid, args+self._domain+[(name,'ilike',value)], offset, limit)
		res = obj.read(cr, uid, ids, [name])
		return [x[name] for x in res]

# ---------------------------------------------------------
# Simple fields
# ---------------------------------------------------------
class boolean(_column):
	_type = 'boolean'
	_symbol_c = '%s'
	_symbol_f = lambda x: x and 'True' or 'False'
	_symbol_set = (_symbol_c, _symbol_f)

class integer(_column):
	_type = 'integer'
	_symbol_c = '%d'
	_symbol_f = lambda x: int(x or 0)
	_symbol_set = (_symbol_c, _symbol_f)

class reference(_column):
	_type = 'reference'
	def __init__(self, string, selection, size, **args):
		_column.__init__(self, string=string, size=size, selection=selection, **args)

class char(_column):
	_type = 'char'
	
	def __init__(self, string, size, **args):
		_column.__init__(self, string=string, size=size, **args)
		self._symbol_set = (self._symbol_c, self._symbol_set_char)
		
	# takes a string (encoded in utf8) and returns a string (encoded in utf8)
	def _symbol_set_char(self, symb):
		#TODO: 
		# * we need to remove the "symb==False" from the next line BUT 
		#   for now too many things rely on this broken behavior
		# * the symb==None test should be common to all data types
		if symb==None or symb==False:
			return None

		# we need to convert the string to a unicode object to be able 
		# to evaluate its length (and possibly truncate it) reliably
		if isinstance(symb, str):
			u_symb = unicode(symb, 'utf8')
		elif isinstance(symb, unicode):
			u_symb = symb
		else:
			u_symb = unicode(symb)
			
		if len(u_symb) > self.size:
			raise Exception, '%s size greater than %d' % (self.string, self.size)
		else:
			return u_symb.encode('utf8')

class text(_column):
	_type = 'text'

import __builtin__

class float(_column):
	_type = 'float'
	_symbol_c = '%f'
	_symbol_f = lambda x: __builtin__.float(x or 0.0)
	_symbol_set = (_symbol_c, _symbol_f)
	def __init__(self, string='unknown', digits=None, **args):
		_column.__init__(self, string=string, **args)
		self.digits = digits

# We'll need to use decimal one day or another
#try:
#	import decimal
#except ImportError:
#	from tools import decimal
#
#class float(_column):
#	_type = 'float'
#	_symbol_c = '%f'
#	def __init__(self, string='unknown', digits=None, **args):
#		_column.__init__(self, string=string, **args)
#		self._symbol_set = (self._symbol_c, self._symbol_set_decimal)
#		self.digits = digits
#		if not digits:
#			scale = 4
#		else:
#			scale = digits[1]
#		self._scale = decimal.Decimal(str(10**-scale))
#		self._context = decimal.Context(prec=scale, rounding=decimal.ROUND_HALF_UP)
#
#	def _symbol_set_decimal(self, symb):
#		if isinstance(symb, __builtin__.float):
#			return decimal.Decimal('%f' % symb)
#		return decimal.Decimal(symb)

class date(_column):
	_type = 'date'

class datetime(_column):
	_type = 'datetime'

class time(_column):
	_type = 'time'

class binary(_column):
	_type = 'binary'
	_symbol_c = '%s'
	_symbol_f = lambda symb: symb and psycopg.Binary(symb) or None
	_symbol_set = (_symbol_c, _symbol_f)

class selection(_column):
	_type = 'selection'
	
	def __init__(self, selection, string='unknown', **args):
		_column.__init__(self, string=string, **args)
		self.selection = selection

	def set(self, cr, obj, id, name, value, user=None, context=None):
		if not context:
			context={}
#CHECKME: a priori, ceci n'est jamais appel� puisque le test ci-dessous est mauvais
# la raison est que selection n'est pas en classic_write = false
# a noter qu'on pourrait fournir un _symbol_set specifique, et ca suffirait
		if value in self.selection:
			raise Exception, 'BAD VALUE'
		_column.set(self, cr, obj, id, name, value, user=None, context=context)


# ---------------------------------------------------------
# Relationals fields
# ---------------------------------------------------------

#
# Values: (0, 0,  { fields })    create
#         (1, ID, { fields })    modification
#         (2, ID)                remove (delete)
#         (3, ID)                unlink one (target id or target of relation)
#         (4, ID)                link
#         (5)                    unlink all (only valid for one2many)
#
#CHECKME: dans la pratique c'est quoi la syntaxe utilisee pour le 5? (5) ou (5, 0)?
class one2one(_column):
	_classic_read = False
	_classic_write = True
	_type = 'one2one'
	
	def __init__(self, obj, string='unknown', **args):
		warnings.warn("The one2one field doesn't work anymore", DeprecationWarning)
		_column.__init__(self, string=string, **args)
		self._obj = obj

	def set(self, cr, obj_src, id, field, act, user=None, context=None):
		if not context:
			context={}
		obj = obj_src.pool.get(self._obj)
		self._table = obj_src.pool.get(self._obj)._table
		if act[0]==0:
			id_new = obj.create(cr, user, act[1])
			cr.execute('update '+obj_src._table+' set '+field+'=%d where id=%d', (id_new,id))
		else:
			cr.execute('select '+field+' from '+obj_src._table+' where id=%d', (act[0],))
			id =cr.fetchone()[0]
			obj.write(cr, user, [id] , act[1], context=context)

	def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None):
		return obj.pool.get(self._obj).search(cr, uid, args+self._domain+[('name','like',value)], offset, limit)


class many2one(_column):
	_classic_read = False
	_classic_write = True
	_type = 'many2one'
	
	def __init__(self, obj, string='unknown', **args):
		_column.__init__(self, string=string, **args)
		self._obj = obj

	#
	# TODO: speed improvement
	#
	# name is the name of the relation field
	def get(self, cr, obj, ids, name, user=None, context=None, values=None):
		if not context:
			context={}
		if not values:
			values={}
		res = {}
		for r in values:
			res[r['id']] = r[name]
		for id in ids:
			res.setdefault(id, '')
		obj = obj.pool.get(self._obj)
		# build a dictionary of the form {'id_of_distant_resource': name_of_distant_resource}
		from orm import except_orm
		try:
			names = dict(obj.name_get(cr, user, filter(None, res.values()), context))
		except except_orm:
			names={}
			for id in filter(None, res.values()):
				try:
					names[id] = dict(obj.name_get(cr, user, [id], context))[id]
				except except_orm, e:
					if e.name == 'AccessError':
						names[id] = "== Access denied =="
					else :
						raise
		for r in res.keys():
			if res[r] and res[r] in names:
				res[r] = (res[r], names[res[r]])
			else:
				res[r] = False
		return res

	def set(self, cr, obj_src, id, field, values, user=None, context=None):
		if not context:
			context={}
		obj = obj_src.pool.get(self._obj)
		self._table = obj_src.pool.get(self._obj)._table
		if type(values)==type([]):
			for act in values:
				if act[0]==0:
					id_new = obj.create(cr, act[2])
					cr.execute('update '+obj_src._table+' set '+field+'=%d where id=%d', (id_new,id))
				elif act[0]==1:
					obj.write(cr, [act[1]], act[2], context=context)
				elif act[0]==2:
					cr.execute('delete from '+self._table+' where id=%d', (act[1],))
				elif act[0]==3 or act[0]==5:
					cr.execute('update '+obj_src._table+' set '+field+'=null where id=%d', (id,))
				elif act[0]==4:
					cr.execute('update '+obj_src._table+' set '+field+'=%d where id=%d', (act[1],id))
		else:
			if values:
				cr.execute('update '+obj_src._table+' set '+field+'=%d where id=%d', (values,id))
			else:
				cr.execute('update '+obj_src._table+' set '+field+'=null where id=%d', (id,))

	def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None):
		return obj.pool.get(self._obj).search(cr, uid, args+self._domain+[('name','like',value)], offset, limit)

class one2many(_column):
	_classic_read = False
	_classic_write = False
	_type = 'one2many'
	
	def __init__(self, obj, fields_id, string='unknown', limit=None, **args):
		_column.__init__(self, string=string, **args)
		self._obj = obj
		self._fields_id = fields_id
		self._limit = limit
		#one2many can't be used as condition for defaults
		assert(self.change_default != True)
	
	def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
		if not context:
			context = {}
		if not values:
			values = {}
		res = {}
		for id in ids:
			res[id] = []
		ids2 = obj.pool.get(self._obj).search(cr, user, [(self._fields_id,'in',ids)], limit=self._limit)
		for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
			res[r[self._fields_id]].append( r['id'] )
		return res

	def set(self, cr, obj, id, field, values, user=None, context=None):
		if not context:
			context={}
		if not values:
			return
		_table = obj.pool.get(self._obj)._table
		obj = obj.pool.get(self._obj)
		for act in values:
			if act[0]==0:
				act[2][self._fields_id] = id
				obj.create(cr, user, act[2], context=context)
			elif act[0]==1:
				obj.write(cr, user, [act[1]] , act[2], context=context)
			elif act[0]==2:
				obj.unlink(cr, user, [act[1]], context=context)
			elif act[0]==3:
				cr.execute('update '+_table+' set '+self._fields_id+'=null where id=%d', (act[1],))
			elif act[0]==4:
				cr.execute('update '+_table+' set '+self._fields_id+'=%d where id=%d', (id,act[1]))
			elif act[0]==5:
				cr.execute('update '+_table+' set '+self._fields_id+'=null where '+self._fields_id+'=%d', (id,))
			elif act[0]==6:
				if not act[2]:
					ids2 = [0]
				else:
					ids2 = act[2]
				cr.execute('update '+_table+' set '+self._fields_id+'=NULL where '+self._fields_id+'=%d and id not in ('+','.join(map(str, ids2))+')', (id,))
				if act[2]:
					cr.execute('update '+_table+' set '+self._fields_id+'=%d where id in ('+','.join(map(str, act[2]))+')', (id,))
	def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None, operator='like'):
		return obj.pool.get(self._obj).name_search(cr, uid, value, self._domain, offset, limit)

#
# Values: (0, 0,  { fields })    create
#         (1, ID, { fields })    modification
#         (2, ID)                remove
#         (3, ID)                unlink
#         (4, ID)                link
#         (5, ID)                unlink all
#         (6, ?, ids)            set a list of links
#
class many2many(_column):
	_classic_read = False
	_classic_write = False
	_type = 'many2many'
	
	def __init__(self, obj, rel, id1, id2, string='unknown', limit=None, **args):
		_column.__init__(self, string=string, **args)
		self._obj = obj
		self._rel = rel
		self._id1 = id1
		self._id2 = id2
		self._limit = limit

	def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
		if not context:
			context={}
		if not values:
			values={}
		res = {}
		if not ids:
			return res
		for id in ids:
			res[id] = []
		ids_s = ','.join(map(str,ids))
		limit_str = self._limit is not None and ' limit %d' % self._limit or ''
		obj = obj.pool.get(self._obj)

		d1, d2 = obj.pool.get('ir.rule').domain_get(cr, user, obj._name)
		if d1:
			d1 = ' and '+d1

		cr.execute('SELECT '+self._rel+'.'+self._id2+','+self._rel+'.'+self._id1+' \
				FROM '+self._rel+' , '+obj._table+' \
				WHERE '+self._rel+'.'+self._id1+' in ('+ids_s+') \
					AND '+self._rel+'.'+self._id2+' = '+obj._table+'.id '+d1
				+limit_str+' order by '+obj._table+'.'+obj._order+' offset %d',
				d2+[offset])
		for r in cr.fetchall():
			res[r[1]].append(r[0])
		return res

	def set(self, cr, obj, id, name, values, user=None, context=None):
		if not context:
			context={}
		if not values:
			return
		obj = obj.pool.get(self._obj)
		for act in values:
			if act[0]==0:
				idnew = obj.create(cr, user, act[2])
				cr.execute('insert into '+self._rel+' ('+self._id1+','+self._id2+') values (%d,%d)', (id,idnew))
			elif act[0]==1:
				obj.write(cr, user, [act[1]] , act[2], context=context)
			elif act[0]==2:
				obj.unlink(cr, user, [act[1]], context=context)
			elif act[0]==3:
				cr.execute('delete from '+self._rel+' where ' +  self._id1 + '=%d and '+ self._id2 + '=%d', (id,act[1]))
			elif act[0]==4:
				cr.execute('insert into '+self._rel+' ('+self._id1+','+self._id2+') values (%d,%d)', (id,act[1]))
			elif act[0]==5:
				cr.execute('update '+self._rel+' set '+self._id2+'=null where '+self._id2+'=%d', (id,))
			elif act[0]==6:

				d1, d2 = obj.pool.get('ir.rule').domain_get(cr, user, obj._name) 
				if d1:
					d1 = ' and '+d1
				cr.execute('delete from '+self._rel+' where '+self._id1+'=%d AND '+self._id2+' IN (SELECT '+self._rel+'.'+self._id2+' FROM '+self._rel+', '+obj._table+' WHERE '+self._rel+'.'+self._id1+'=%d AND '+self._rel+'.'+self._id2+' = '+obj._table+'.id '+ d1 +')', [id, id]+d2 )

				for act_nbr in act[2]: 
					cr.execute('insert into '+self._rel+' ('+self._id1+','+self._id2+') values (%d, %d)', (id, act_nbr))

	#
	# TODO: use a name_search
	#
	def search(self, cr, obj, args, name, value, offset=0, limit=None, uid=None, operator='like'):
		return obj.pool.get(self._obj).search(cr, uid, args+self._domain+[('name',operator,value)], offset, limit)

# ---------------------------------------------------------
# Function fields
# ---------------------------------------------------------

class function(_column):
	_classic_read = False
	_classic_write = False
	_type = 'function'
	_properties = True
	
	def __init__(self, fnct, arg=None, fnct_inv=None, fnct_inv_arg=None, type='float', fnct_search=None, obj=None, method=False, store=False, **args):
		_column.__init__(self, **args)
		self._obj = obj
		self._method = method
		self._fnct = fnct
		self._fnct_inv = fnct_inv
		self._arg = arg
		if 'relation' in args:
			self._obj = args['relation']
		self._fnct_inv_arg = fnct_inv_arg
		if not fnct_inv:
			self.readonly = 1
		self._type = type
		self._fnct_search = fnct_search
		self.store = store
		if type == 'float':
			self._symbol_c = '%f'
			self._symbol_f = lambda x: __builtin__.float(x or 0.0)
			self._symbol_set = (self._symbol_c, self._symbol_f)
		
	def search(self, cr, uid, obj, name, args):
		if not self._fnct_search:
			#CHECKME: should raise an exception
			return []
		return self._fnct_search(obj, cr, uid, obj, name, args)

	def get(self, cr, obj, ids, name, user=None, context=None, values=None):
		if not context:
			context={}
		if not values:
			values={}
		res = {}
		table = obj._table
		if self._method:
			# TODO get HAS to receive uid for permissions !
			return self._fnct(obj, cr, user, ids, name, self._arg, context)
		else:
			return self._fnct(cr, table, ids, name, self._arg, context)

	def set(self, cr, obj, id, name, value, user=None, context=None):
		if not context:
			context={}
		if self._fnct_inv:
			self._fnct_inv(obj, cr, user, id, name, value, self._fnct_inv_arg, context)

# ---------------------------------------------------------
# Serialized fields
# ---------------------------------------------------------
class serialized(_column):
	def __init__(self, string='unknown', serialize_func=repr, deserialize_func=eval, type='text', **args):
		self._serialize_func = serialize_func
		self._deserialize_func = deserialize_func
		self._type = type
		self._symbol_set = (self._symbol_c, self._serialize_func)
		self._symbol_get = self._deserialize_func
		super(serialized, self).__init__(string=string, **args)

class property(function):
	def _fnct_write(self2, self, cr, uid, id, prop, id_val, val, context=None):
		if not context:
			context={}
		(obj_dest,) = val
		definition_id = self2._field_get(self, cr, uid, prop)

		property = self.pool.get('ir.property')
		nid = property.search(cr, uid, [('fields_id','=',definition_id),('res_id','=',self._name+','+str(id))])
		while len(nid):
			cr.execute('delete from ir_property where id=%d', (nid.pop(),))

		nid = property.search(cr, uid, [('fields_id','=',definition_id),('res_id','=',False)])
		default_val = False
		if nid:
			default_val = property.browse(cr, uid, nid[0], context).value

		company_id = self.pool.get('res.users').company_get(cr, uid, uid)
		res = False
		newval = (id_val and obj_dest+','+str(id_val)) or False
		if (newval != default_val) and newval:
			propdef = self.pool.get('ir.model.fields').browse(cr, uid, definition_id, context=context)
			res = property.create(cr, uid, {
				'name': propdef.name,
				'value': newval,
				'res_id': self._name+','+str(id),
				'company_id': company_id,
				'fields_id': definition_id
			}, context=context)
		return res

	def _fnct_read(self2, self, cr, uid, ids, prop, val, context=None):
		if not context:
			context={}
		property = self.pool.get('ir.property')
		definition_id = self2._field_get(self, cr, uid, prop)

		nid = property.search(cr, uid, [('fields_id','=',definition_id),('res_id','=',False)])
		default_val = False
		if nid:
			d = property.browse(cr, uid, nid[0], context).value
			default_val = (d and int(d.split(',')[1])) or False

		vids = map(lambda id: self._name+','+str(id), ids)
		nids = property.search(cr, uid, [('fields_id','=',definition_id),('res_id','in', vids)])

		res = {}
		for id in ids:
			res[id]= default_val
		for prop in property.browse(cr, uid, nids):
			res[int(prop.res_id.split(',')[1])] = (prop.value and int(prop.value.split(',')[1])) or False

		obj = self.pool.get(self2._obj)
		names = dict(obj.name_get(cr, uid, filter(None, res.values()), context))
		for r in res.keys():
			if res[r] and res[r] in names:
				res[r] = (res[r], names[res[r]])
			else:
				res[r] = False
		return res

	def _field_get(self, self2, cr, uid, prop):
		if not self.field_id.get(cr.dbname):
			cr.execute('select id from ir_model_fields where name=%s and model=%s', (prop, self2._name))
			res = cr.fetchone()
			self.field_id[cr.dbname] = res and res[0]
		return self.field_id[cr.dbname]

	def __init__(self, obj_prop, **args):
		self.field_id = {}
		function.__init__(self, self._fnct_read, False, self._fnct_write, (obj_prop, ), **args)

	def restart(self):
		self.field_id = {}
