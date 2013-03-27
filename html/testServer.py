import BaseHTTPServer, SimpleHTTPServer, CGIHTTPServer

# Starts a CGI-capable http server listening on port 8000

class myRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):
	def is_executable(self, path):
		return self.is_python(path)

if __name__ == '__main__':
	SimpleHTTPServer.test(myRequestHandler, BaseHTTPServer.HTTPServer)
