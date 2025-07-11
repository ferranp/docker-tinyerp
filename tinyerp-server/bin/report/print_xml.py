##############################################################################
#
# Copyright (c) 2004 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: print_xml.py 1005 2005-07-25 08:41:42Z nicoe $
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

import os,types
from xml.dom import minidom

import netsvc
import tools
import print_fnc

from osv.orm import browse_null, browse_record
import pooler

class InheritDict(dict):
	# Might be usefull when we're doing name lookup for call or eval.

	def __init__(self, parent=None):
		self.parent = parent
	
	def __getitem__(self, name):
		if name in self:
			return super(InheritDict, self).__getitem__(name)
		else:
			if not self.parent:
				raise KeyError
			else:
				return self.parent[name]

def tounicode(val):
	if isinstance(val, str):
		unicode_val	= unicode(val, 'utf-8')
	elif isinstance(val, unicode):
		unicode_val = val
	else:
		unicode_val = unicode(val) 
	return unicode_val

class document(object):
	def __init__(self, cr, uid, datas, func=False):
		# create a new document
		self.cr = cr 
		self.pool = pooler.get_pool(cr.dbname)
		self.doc = minidom.Document()
		self.func = func or {}
		self.datas = datas
		self.uid = uid
		self.bin_datas = {}

	def node_attrs_get(self, node):
		attrs = {}
		nattr = node.attributes
		for i in range(nattr.length):
			attr = nattr.item(i)
			attrs[attr.localName] = attr.nodeValue
#			attrs[attr.name] = attr.nodeValue
		return attrs
		
	def get_value(self, browser, field_path):
		fields = field_path.split('.')

		if not len(fields):
			print "WARNING: field name is empty!"
			return ''
					
		value = browser
		for f in fields:
			if isinstance(value, list):
				if len(value)==0:
					print "WARNING: empty list found!"
					return ''
#				elif len(value)>1:
#					print "WARNING:", len(value), "possibilities for", value[0]._table_name , "picking first..."
				value = value[0]
			if isinstance(value, browse_null):
				return ''
			else:
				value = value[f]
			
		if isinstance(value, browse_null) or (type(value)==bool and not value):
			return ''
		else:	
			return value
		
	def get_value2(self, browser, field_path):
		value = self.get_value(browser, field_path)
		if isinstance(value, browse_record):
			return value.id
		elif isinstance(value, browse_null):
			return False
		else:
			return value
			
	def eval(self, record, expr):
#TODO: support remote variables (eg address.title) in expr
# how to do that: parse the string, find dots, replace those dotted variables by temporary 
# "simple ones", fetch the value of those variables and add them (temporarily) to the _data
# dictionary passed to eval

#FIXME: it wont work if the data hasn't been fetched yet... this could
# happen if the eval node is the first one using this browse_record
# the next line is a workaround for the problem: it causes the resource to be loaded
#Pinky: Why not this ? eval(expr, browser) ?
#		name = browser.name
#		data_dict = browser._data[self.get_value(browser, 'id')]
		return eval(expr)

	def parse_node(self, node, parent, browser, datas=None):
		# node is the node of the xml template to be parsed
		# parent = the parent node in the xml data tree we are creating
		
		if node.nodeType == node.ELEMENT_NODE:
#			print '-'*60
#			print "parse_node", node
#			print "parent: ", parent
#			print "ids:", ids
#			print "model:", model
#			print "datas:", datas
			
			# convert the attributes of the node to a dictionary
			
			attrs = self.node_attrs_get(node)
			if 'type' in attrs:
				if attrs['type']=='field':
					value = self.get_value(browser, attrs['name'])
#TODO: test this
					if value == '' and 'default' in attrs:
						value = attrs['default']
					el = self.doc.createElement(node.localName)
					parent.appendChild(el)
					el_txt = self.doc.createTextNode(tounicode(value))
					el.appendChild(el_txt)

#TODO: test this
					for key, value in attrs.iteritems():
						if key not in ('type', 'name', 'default'):
							el.setAttribute(key, value)

				elif attrs['type']=='attachment':
					if isinstance(browser, list):
						model = browser[0]._table_name
					else: 
						model = browser._table_name

					value = self.get_value(browser, attrs['name'])
					
					service = netsvc.LocalService("object_proxy")
					ids = service.execute(self.cr.dbname, self.uid, 'ir.attachment', 'search', [('res_model','=',model),('res_id','=',int(value))])
					datas = service.execute(self.cr.dbname, self.uid, 'ir.attachment', 'read', ids)
	
					if len(datas):
						# if there are several, pick first
						datas = datas[0]
						fname = str(datas['datas_fname'])
						ext = fname.split('.')[-1].lower()
						if ext in ('jpg','jpeg', 'png'):
							import base64, StringIO
							dt = base64.decodestring(datas['datas'])
							fp = StringIO.StringIO(dt)
							i = str(len(self.bin_datas))
							self.bin_datas[i] = fp
							
							el = self.doc.createElement(node.localName)
							parent.appendChild(el)
							# node content is the length of the image
							el_txt = self.doc.createTextNode(i)
							el.appendChild(el_txt)
	
				elif attrs['type']=='data':
#TODO: test this
					el = self.doc.createElement(node.localName)
					parent.appendChild(el)
					txt = self.datas.get('form', {}).get(attrs['name'], '')
					el_txt = self.doc.createTextNode(tounicode(txt))
					el.appendChild(el_txt)

				elif attrs['type']=='function':
					el = self.doc.createElement(node.localName)
					parent.appendChild(el)
					if attrs['name'] in self.func:
						txt = self.func[attrs['name']](node)
					else:
						txt = print_fnc.print_fnc(attrs['name'], node)
					el_txt = self.doc.createTextNode(txt)
					el.appendChild(el_txt)

				elif attrs['type']=='eval':
#TODO: faire ca plus proprement
					if isinstance(browser, list):
						print "ERROR: EVAL!"
					el = self.doc.createElement(node.localName)
					parent.appendChild(el)
					value = self.eval(browser, attrs['expr'])
					el_txt = self.doc.createTextNode(str(value))
					el.appendChild(el_txt)

				elif attrs['type']=='fields':
					fields = attrs['name'].split(',')
					vals = {}
					for b in browser:
						value = tuple([self.get_value2(b, f) for f in fields])
						if not value in vals:
							vals[value]=[]
						vals[value].append(b)
					keys = vals.keys()
					keys.sort()

					if 'order' in attrs and attrs['order']=='desc':
						keys.reverse()

					v_list = [vals[k] for k in keys]
					for v in v_list: 
						el = self.doc.createElement(node.localName)
						parent.appendChild(el)
						el_cld = node.firstChild
						while el_cld:
							self.parse_node(el_cld, el, v)
							el_cld = el_cld.nextSibling

				elif attrs['type']=='call':
					if len(attrs['args']):
#TODO: test this					
						# fetches the values of the variables which names where passed in the args attribute
						args = [self.eval(browser, arg) for arg in attrs['args'].split(',')]
					else:
						args = []
						
					# get the object
					if attrs.has_key('model'):
						obj = self.pool.get(attrs['model'])
					else: 
						if isinstance(browser, list):
							obj = browser[0]._table
						else:
							obj = browser._table

					# get the ids
					if attrs.has_key('ids'):
						ids = self.eval(browser, attrs['ids'])
					else: 
						if isinstance(browser, list):
							ids = [b.id for b in browser] 
						else:
							ids = [browser.id]
					
					# call the method itself
					newdatas = getattr(obj, attrs['name'])(self.cr, self.uid, ids, *args)
	
					def parse_result_tree(node, parent, datas):
						if node.nodeType == node.ELEMENT_NODE:
							el = self.doc.createElement(node.localName)
							parent.appendChild(el)
							atr = self.node_attrs_get(node)
							if 'value' in atr:
								#print "type=>",type(datas[atr['value']])
								#print "value=>",datas[atr['value']]
								if not isinstance(datas[atr['value']], (str, unicode)):
									txt = self.doc.createTextNode(str(datas[atr['value']]))
								else:
									txt = self.doc.createTextNode(datas[atr['value']].decode('utf-8'))
								el.appendChild(txt)
							else:
								el_cld = node.firstChild
								while el_cld:
									parse_result_tree(el_cld, el, datas)
									el_cld = el_cld.nextSibling
						elif node.nodeType==node.TEXT_NODE:
							el = self.doc.createTextNode(node.nodeValue)
							parent.appendChild(el)
						else:
							pass
	
					if not isinstance(newdatas, list):
						newdatas = [newdatas]
					for newdata in newdatas:
						parse_result_tree(node, parent, newdata)

				elif attrs['type']=='zoom':
					value = self.get_value(browser, attrs['name'])
					
					if value:
						if not isinstance(value, list):
							v_list = [value]
						else:
							v_list = value
						for v in v_list:
							el = self.doc.createElement(node.localName)
							parent.appendChild(el)
							el_cld = node.firstChild
							while el_cld:
								self.parse_node(el_cld, el, v)
								el_cld = el_cld.nextSibling
			else:
				# if there is no "type" attribute in the node, copy it to the xml data and parse its childs
				el = self.doc.createElement(node.localName)
				parent.appendChild(el)
				el_cld = node.firstChild
				while el_cld:
					self.parse_node(el_cld, el, browser)
					el_cld = el_cld.nextSibling

		elif node.nodeType==node.TEXT_NODE:
			# if it's a text node, copy it to the xml data
			el = self.doc.createTextNode(node.nodeValue)
			parent.appendChild(el)
		else:
			pass

	def xml_get(self):
		return self.doc.toxml('utf-8')

	def parse_tree(self, ids, model, context=None):
		if not context:
			context={}
		browser = self.pool.get(model).browse(self.cr, self.uid, ids, context)
		self.parse_node(self.dom.documentElement, self.doc, browser)
		
	def parse_string(self, xml, ids, model, context=None):
		if not context:
			context={}
		# parses the xml template to memory
		self.dom = minidom.parseString(xml)
		
		# create the xml data from the xml template
		self.parse_tree(ids, model, context)

	def parse(self, filename, ids, model, context=None):
		if not context:
			context={}
		# parses the xml template to memory
		self.dom = minidom.parseString(tools.file_open(
				os.path.join(tools.config['root_path'],
					filename)).read())

		# create the xml data from the xml template
		self.parse_tree(ids, model, context)

	def close(self):
		self.doc = None
		self.dom = None

