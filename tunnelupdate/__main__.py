from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from subprocess import check_call, call
from traceback import print_exc
from urllib.parse import urlparse, parse_qs
from signal import signal, SIGINT
from sys import exit
from yaml import safe_load, safe_dump
from os.path import join, dirname
from os import getenv


IDENTS = {}
IDENTS["10.99.1.1"] = {
    "name": "router-a-ipv6",
    "remote_ipv6": "2a0e:7d44:f000:a::2",
    "primary_route": "2a0e:7d44:f069::/48",
}
IDENTS["10.99.1.3"] = {
    "name": "router-b-ipv6",
    "remote_ipv6": "2a0e:7d44:f000:b::2",
    "primary_route": "2a0e:7d44:f069::/48",
}

NETPLAN_FILE = getenv("NETPLAN_FILE", join(dirname(__file__), "./tunnels-base.yml"))

IP_ARGS = set(["myip","ip"])

class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            _, args = self.parse_url()

            remote_ip = self.client_address[0]
            if remote_ip not in IDENTS:
                self.send_error(403, "Forbidden")
                return

            remote_ident = IDENTS[remote_ip]
            remote_ident_name = remote_ident["name"]

            set_ip_raw = None
            for ip_arg in IP_ARGS:
                if ip_arg not in args:
                    continue
                set_ip_raw = args[ip_arg][0]
            if not set_ip_raw:
                self.send_error(400, "Bad Request")
                return

            set_ip_split = set_ip_raw.split("/")
            set_ip = set_ip_split[0]

            is_primary = ("primary" in args and args["primary"][0] == "true")

            file = {}
            with open(NETPLAN_FILE, "r") as f:
                file = safe_load(f)

            tunnel_config = file["network"]["tunnels"][remote_ident_name]

            was_primary = False
            for routes in tunnel_config["routes"]:
                if routes["to"] == remote_ident["primary_route"]:
                    was_primary = True
                    break

            if tunnel_config["remote"] == set_ip and was_primary == is_primary:
                self.send_response(200, "OK")
                self.end_headers()
                self.wfile.write(f"nochg {set_ip}".encode("utf-8"))
                return

            if is_primary and not was_primary:
                tunnel_config["routes"].append({
                    "to": remote_ident["primary_route"],
                    "via": remote_ident["remote_ipv6"],
                })
                call(["ip", "-6", "route", "add", remote_ident["primary_route"], "via", remote_ident["remote_ipv6"]])
            elif not is_primary and was_primary:
                temp = []
                for routes in tunnel_config["routes"]:
                    if routes["to"] == remote_ident["primary_route"]:
                        continue
                    temp.append(routes)
                tunnel_config["routes"] = temp
                call(["ip", "-6", "route", "del", remote_ident["primary_route"], "via", remote_ident["remote_ipv6"]])

            check_call(["ip", "link", "set", "dev", remote_ident_name, "type", "sit", "remote", set_ip])

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
