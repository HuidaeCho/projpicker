#!/usr/bin/env python3
import argparse
import os
import sys
import json
import webbrowser
import http.server
import collections

import projpicker as ppik

module_path = os.path.dirname(__file__)

default_address = "localhost"
default_port = 8000


# https://gist.github.com/dideler/3814182
# https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
class Color:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.endswith("/query"):
            environ = {}
            environ["REMOTE_ADDR"]    = self.client_address
            environ["REQUEST_METHOD"] = self.command
            environ["PATH_INFO"]      = self.path
            environ["CONTENT_LENGTH"] = self.headers.get("content-length")

            run_application(
                environ,
                self.rfile,
                self.send_response,
                self.send_header,
                self.end_headers,
                self.wfile.write,
                lambda: None,
                False)


def verbose_args(*args):
    if ppik.is_verbose():
        ppik.message(*args)


def verbose_color(color, *args):
    verbose_args(color + "".join(*args) + Color.ENDC)


def verbose_line():
    verbose_color(Color.BOLD, "-" * 79)


def verbose_header(*args):
    verbose_color(Color.BOLD, *args)


def verbose_key_value(key, value):
    verbose_args(Color.BOLD + key + ": " + Color.ENDC + str(value))


def print_color(color, *args):
    ppik.message(color + "".join(*args) + Color.ENDC)


# Python Web Server Gateway Interface (WSGI)
# https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
def application(environ, start_response):
    remote_addr = environ["REMOTE_ADDR"]
    request_method = environ["REQUEST_METHOD"]
    path_info = environ.get("PATH_INFO", environ.get("REQUEST_URI"))

    status = "404 Not Found"
    content_type = "text/plain"
    response = "Invalid request"

    if request_method == "GET":
        file_path = None
        if path_info == "/":
            path_info = "/index.html"
        if path_info in ("/index.html",
                         "/projpicker.css",
                         "/utils.js",
                         "/projpicker.js"):
            file_path = os.path.join(module_path, path_info[1:])

        if file_path and os.path.isfile(file_path):
            status = "200 OK"
            if file_path.endswith(".html"):
                content_type = "text/html"
            elif file_path.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = "text/javascript"
            with open(file_path) as f:
                response = f.read()
    elif request_method == "POST" and path_info.endswith("/query"):
        content_length = int(environ["CONTENT_LENGTH"])
        geoms = environ["wsgi.input"].read(content_length).decode().strip()

        verbose_line()
        verbose_header("Requested query")
        verbose_args(geoms)

        geoms = ppik.parse_mixed_geoms(geoms)
        verbose_header("Parsed geometries")
        verbose_args(geoms)

        bbox = ppik.query_mixed_geoms(geoms)
        verbose_key_value("Number of queried CRSs", len(bbox))
        verbose_line()

        response = ppik.jsonify_bbox(bbox)

        status = "200 OK"
        content_type = "application/json"

    response_headers = [("Content-type", content_type)]
    start_response(status, response_headers)
    return [response.encode()]


def run_application(
        environ,
        reader,
        send_response,
        send_header,
        end_headers,
        write_data,
        flush_data,
        https=False):
    # https://www.python.org/dev/peps/pep-0333/#the-server-gateway-side
    def write(data):
        if not headers_set:
            raise AssertionError("write() before start_response()")
        elif not headers_sent:
            # Before the first output, send the stored headers
            status, response_headers = headers_sent[:] = headers_set
            s = status.split()
            code = int(s[0])
            message = " ".join(s[1:])
            send_response(code, message)
            for header in response_headers:
                send_header(*header)
            end_headers()
        write_data(data)
        flush_data()

    def start_response(status, response_headers, exc_info=None):
        if exc_info:
            try:
                if headers_sent:
                    # Re-raise original exception if headers sent
                    # https://www.python.org/dev/peps/pep-3109/#compatibility-issues
                    e = exc_info[0](exc_info[1])
                    e.__traceback__ = exc_info[2]
                    raise e
            finally:
                exc_info = None     # avoid dangling circular ref
        elif headers_set:
            raise AssertionError("Headers already set!")

        headers_set[:] = [status, response_headers]
        return write

    environ["wsgi.input"]        = reader
    environ["wsgi.errors"]       = sys.stderr
    environ["wsgi.version"]      = (1, 0)
    environ["wsgi.multithread"]  = False
    environ["wsgi.multiprocess"] = True
    environ["wsgi.run_once"]     = True
    environ["wsgi.url_scheme"]   = "https" if https else "http"

    headers_set = []
    headers_sent = []

    result = application(environ, start_response)
    try:
        for data in result:
            if data:    # don't send headers until body appears
                write(data)
        if not headers_sent:
            write("")   # send headers now if body was empty
    finally:
        if hasattr(result, "close"):
            result.close()


def start(server=f"{default_address}:{default_port}", start_client=False):
    if ":" in server:
        address, port, *_ = server.split(":")
        if not address:
            address = default_address
        if port:
            try:
                port = int(port)
            except:
                port = default_port
        else:
            port = default_port

    httpd = http.server.HTTPServer((address, port), HTTPRequestHandler)

    url = f"http://{address}:{port}"
    if start_client is True:
        webbrowser.open(url)

    try:
        print_color(Color.OKGREEN, f"Starting httpd server on {url}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print_color(Color.FAIL, f"\nClosed httpd server on {url}")


if os.environ.get("GATEWAY_INTERFACE") == "CGI/1.1":
    # run CGI
    SysStdinEncode = collections.namedtuple("SysStdinEncode", "read")

    run_application(
        os.environ.copy(),
        SysStdinEncode(lambda n: sys.stdin.read(n).encode()),
        lambda code, msg: sys.stdout.write(f"Status: {code} {msg}\r\n"),
        lambda *header: sys.stdout.write(f"{header[0]}: {header[1]}\r\n"),
        lambda: sys.stdout.write("\r\n"),
        lambda data: sys.stdout.write(data.decode()),
        sys.stdout.flush,
        os.environ["HTTPS"] == "on")
elif __name__ == "__main__":
    # run CLI
    parser = argparse.ArgumentParser(description="ProjPicker Web Server")
    parser.add_argument(
        "-S",
        "--server",
        default="localhost:8000",
        help="specify the IP address and port on which the server listens "
            "(default: localhost:8000)",
    )
    parser.add_argument(
        "-c",
        "--client",
        action="store_true",
        help="start a new client in the user's default browser",
    )
    args = parser.parse_args()

    start(server=args.server, start_client=args.client)
# else run WSGI
