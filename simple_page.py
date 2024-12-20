from http.server import SimpleHTTPRequestHandler, HTTPServer
import matplotlib.pyplot as plt # type: ignore
import io

print("Starting server")

class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/graph':
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            self.wfile.write(self.generate_graph())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Simple HTTP Server</title></head>
                <body>
                    <h1>Hello, this is a simple HTTP server for Brian!</h1>
                    <img src="/graph" alt="Simple Graph"/>
                </body>
                </html>
            """)

    def generate_graph(self):
        plt.figure()
        plt.plot([1, 2, 3, 4], [1, 4, 9, 16])
        plt.title('Simple Graph')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return buf.getvalue()

def run(server_class=HTTPServer, handler_class=MyHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
    