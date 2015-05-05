#!/usr/bin/python

import sys
import xmlrpclib
import time
user = 'admin'
pwd = 'admin'
dbname = 'carreras'
url = 'http://10.10.0.11:8073/xmlrpc/'

sock = xmlrpclib.ServerProxy(url + 'common')
uid = sock.login(dbname ,user ,pwd)

sock_obj = xmlrpclib.ServerProxy(url + 'object')
sock_wiz = xmlrpclib.ServerProxy(url + 'wizard')

             
s = []
res = sock_obj.execute(dbname, uid, pwd, 'res.partner','search', s)

ids=res[:80]
print time.time()
res = sock_obj.execute(dbname, uid, pwd, 'res.partner','read', ids,['name'])
print time.time()
for i in range(5):
     res = sock_obj.execute(dbname, uid, pwd, 'res.partner','read', ids,['name'])
print time.time()


