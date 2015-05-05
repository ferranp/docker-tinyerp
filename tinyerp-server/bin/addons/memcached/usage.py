#!/usr/bin/python

import memcache
import os,sys,time
mc = memcache.Client(['127.0.0.1:11211'], debug=0)

items = [
'total_items',
'curr_items',
'get_misses',
'get_hits',
]
#bytes_written
#uptime
#bytes
#cmd_get
#pid     = 11405
#curr_connections        = 3
#connection_structures   = 4
#limit_maxbytes  = 524288000
#version         = 1.1.12
#'rusage_user',
#total_connections       = 764
#cmd_set         = 4694
#time    = 1200681337
#bytes_read      = 7607789
#rusage_system   = 0.232014
def title():
    for item in items:
        pass
        #print item.center(10) ,
    #print ""
    
def print_stats():
    stats = mc.get_stats()
    for server in stats:
        #print server[0]
        data = server[1]
        for key in items:
            pass
            #print str(data[key]).center(10) ,
        #print ""

      
i=0
while(True):
    if (i % 15) == 0:
        title()
    i=i+1
    print_stats()
    time.sleep(5)
