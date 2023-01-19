from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from subprocess import check_call
from tabnanny import check
from traceback import print_exc
from urllib.parse import urlparse, parse_qs
from signal import signal, SIGINT
from sys import exit
from yaml import safe_load, safe_dump
from os.path import join, dirname
from os import getenv


IDENTS = {}
IDENTS["10.99.0.1"] = "home-ipv6"

NETPLAN_FILE = getenv("NETPLAN_FILE", join(dirname(__file__), "./tunnels-base.yml"))

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            path, args = self.parse_url()
            if path != "/nic/update":
                self.send_error(404, "Not Found")
                return

            if "myip" not in args:
                self.send_error(400, "Bad request")
                return

            remote_ip = self.client_address[0]
            if remote_ip not in IDENTS:
                self.send_error(403, "Forbidden")
                return

            remote_ident = IDENTS[remote_ip]
            set_ip_raw = args["myip"][0]
            set_ip_split = set_ip_raw.split("/")
            set_ip = set_ip_split[0]

            file = {}
            with open(NETPLAN_FILE, "r") as f:
                file = safe_load(f)

            tunnel_config = file["network"]["tunnels"][remote_ident]

            if tunnel_config["remote"] == set_ip:
                self.send_response(200, "OK")
                self.end_headers()
                self.wfile.write(f"nochg {set_ip}".encode("utf-8"))
                return

            check_call(["ip", "link", "set", "dev", remote_ident, "type", "sit", "remote", set_ip])

            tunnel_config["remote"] = set_ip
            with open(NETPLAN_FILE, "w") as f:
                safe_dump(file, f)

            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write(f"good {set_ip}".encode("utf-8"))
        except:
            print_exc()
            self.send_error(500, "Internal Server Error")

    def parse_url(self):
        url_components = urlparse(self.path)
        return url_components.path, parse_qs(url_components.query)


def start_server(host, port):
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, HttpHandler)
    print(f"Server started on {host}:{port}")
    httpd.serve_forever()


def shutdown_handler(signum, frame):
    print('Shutting down server')
    exit(0)


def main():
    signal(SIGINT, shutdown_handler)
    start_server("0.0.0.0", 9999)


if __name__ == "__main__":
    main()
