"""
SecureXMLRPCServer module using pyOpenSSL 0.5
Extremely kludgey code written 0907.2002
by Michal Wallace ( http://www.sabren.net/ )

This acts as a drop-in replacement for
SimpleXMLRPCServer from the standard python
library.

This code is in the public domain and is
provided AS-IS WITH NO WARRANTY WHATSOEVER.
"""
import SocketServer
import os, socket, sys
import SimpleXMLRPCServer
from OpenSSL import SSL


class SSLBugFix:
    """
    SSL Connection tends to die on sendall,
    so I use send() as a workaround. This is
    called by socket._fileobject, which is needed
    so SocketServer (and kids) can treat the connection
    as a regular file.
    """
    def __init__(self, conn):
        """
        For some reason, I can't subclass Connection,
        so I'm making a proxy, instead.
        """
        self.__dict__["conn"] = conn
    def __getattr__(self,name):
        return getattr(self.__dict__["conn"], name)
    def __setattr__(self,name, value):
        setattr(self.__dict__["conn"], name, value)

    
#    def sendall(self, data):
#        """
#        This is the bugfix. Connection.sendall() segfaults
#        on socket._fileobject.flush(), so just rewire it
#        to use send() instead.
#        """
#        self.__dict__["conn"].send(data)

    def shutdown(self, how=1):
        """
        This isn't part of the bugfix. SimpleXMLRpcServer.doPOST
        calls shutdown(1), and Connection.shutdown() doesn't take
        an argument. So we just discard it:
        """
        self.__dict__["conn"].shutdown()

    def accept(self):
        """
        This is the other part of the shutdown() workaround.
        Since servers create new sockets, we have to infect
        them with our magic. :)
        """
        c, a = self.__dict__["conn"].accept()
        return (SSLBugFix(c), a)



class SecureTCPServer(SocketServer.TCPServer):
    """
    Just like TCPServer, but use a socket.
    This really ought to let you specify the key and certificate files.
    """
    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.BaseServer.__init__(self, server_address, RequestHandlerClass)

        ## Same as normal, but make it secure:
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.set_options(SSL.OP_NO_SSLv2)

        dir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
        ctx.use_privatekey_file (os.path.join(dir, 'server.pkey'))
        ctx.use_certificate_file(os.path.join(dir, 'server.cert'))

        self.socket = SSLBugFix(SSL.Connection(ctx, socket.socket(self.address_family,
                                                                  self.socket_type)))
        self.server_bind()
        self.server_activate()


class SecureXMLRPCRequestHandler(SimpleXMLRPCServer.SimpleXMLRPCRequestHandler):
    def setup(self):
        """
        We need to use socket._fileobject Because SSL.Connection
        doesn't have a 'dup'. Not exactly sure WHY this is, but
        this is backed up by comments in socket.py and SSL/connection.c
        """
        self.connection = self.request # for doPOST
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
    

class SecureXMLRPCServer(SimpleXMLRPCServer.SimpleXMLRPCServer, SecureTCPServer):
    def __init__(self, addr,
                 requestHandler=SecureXMLRPCRequestHandler,
                 logRequests=1):
        """
        This is the exact same code as SimpleXMLRPCServer.__init__
        except it calls SecureTCPServer.__init__ instead of plain
        old TCPServer.__init__
        """
        self.funcs = {}
        self.logRequests = logRequests
        self.instance = None
        SecureTCPServer.__init__(self, addr, requestHandler)

