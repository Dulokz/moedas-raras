import sys
import os
import re
import time
import subprocess
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BACKEND_URL = "http://127.0.0.1:8001"
DEV_PORT = 3000


class ProxyHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Development HTTP Server: Serves frontend static files and proxies /api/* to FastAPI at localhost:8001."""

    def do_GET(self):
        if self.path.startswith("/api/"):
            self.proxy_request("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self.proxy_request("POST")
        else:
            self.send_error(405, "Method Not Allowed")

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self.proxy_request("OPTIONS")
        else:
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

    def proxy_request(self, method: str):
        target_url = f"{BACKEND_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req_headers = {}
        for header, val in self.headers.items():
            if header.lower() not in ["host"]:
                req_headers[header] = val

        try:
            req = urllib.request.Request(target_url, data=body, headers=req_headers, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for h_name, h_val in resp.headers.items():
                    if h_name.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(h_name, h_val)
                resp_body = resp.read()
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for h_name, h_val in e.headers.items():
                if h_name.lower() not in ["transfer-encoding", "content-length"]:
                    self.send_header(h_name, h_val)
            err_body = e.read()
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as err:
            print(f"[DEV PROXY ERROR] Proxying {self.path} failed: {err}")
            self.send_error(502, f"Bad Gateway: {err}")


def run_dev_proxy_and_tunnel():
    print("=" * 65)
    print(" MOEDAS RARAS V2 -- DEV SERVER FRONTEND/PROXY + HTTPS TUNNEL")
    print("=" * 65)

    os.chdir(Path(__file__).resolve().parent)

    # 1. Start HTTP Dev Proxy Server on localhost:3000
    server_address = ("0.0.0.0", DEV_PORT)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print(f"\n[1/2] Servidor Web Dev (Frontend + Proxy /api/* -> 8001) ativo em:")
    print(f"      http://localhost:{DEV_PORT}")

    # 2. Launch cloudflared tunnel process
    cloudflared_bin = Path(__file__).resolve().parent / "cloudflared.exe"
    if not cloudflared_bin.exists():
        cloudflared_cmd = "cloudflared"
    else:
        cloudflared_cmd = str(cloudflared_bin)

    print("\n[2/2] Iniciando Tunel HTTPS Cloudflare...")
    tunnel_cmd = [cloudflared_cmd, "tunnel", "--url", f"http://localhost:{DEV_PORT}"]

    proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    https_url = None

    # Read output lines to find the HTTPS URL
    def monitor_tunnel():
        nonlocal https_url
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match and not https_url:
                https_url = match.group(0)
                print("\n" + "=" * 65)
                print(" >>> URL HTTPS FINAL PARA ABRIR NO CELULAR COM CAMERA LIBERADA: <<<")
                print(f"     {https_url}")
                print("=" * 65 + "\n")

    import threading
    t = threading.Thread(target=monitor_tunnel, daemon=True)
    t.start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor dev e tunel...")
        httpd.server_close()
        proc.terminate()


if __name__ == "__main__":
    run_dev_proxy_and_tunnel()
