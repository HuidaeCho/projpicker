#!/bin/env python3
import argparse
import os
import sys
import json
import webbrowser
import http.server

import projpicker as ppik

module_path = os.path.dirname(__file__)
is_verbose = False


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
        if self.path == "/query":
            # http.client.HTTPResponse stores headers and implements
            # email.message.Message class
            # https://docs.python.org/3/library/email.compat32-message.html#email.message.Message

            # https://www.python.org/dev/peps/pep-0333/#the-server-gateway-side
            environ = {}
            environ["REMOTE_ADDR"]       = self.client_address
            environ["REQUEST_METHOD"]    = self.command
            environ["PATH_INFO"]         = self.path
            environ["CONTENT_LENGTH"]    = self.headers.get("content-length")

            environ["wsgi.input"]        = self.rfile
            environ["wsgi.errors"]       = sys.stderr
            environ["wsgi.version"]      = (1, 0)
            environ["wsgi.multithread"]  = False
            environ["wsgi.multiprocess"] = True
            environ["wsgi.run_once"]     = True
            environ["wsgi.url_scheme"]   = "http"

            headers_set = []
            headers_sent = []

            def write(data):
                if not headers_set:
                    raise AssertionError("write() before start_response()")

                elif not headers_sent:
                    # Before the first output, send the stored headers
                    status, response_headers = headers_sent[:] = headers_set
                    s = status.split()
                    code = int(s[0])
                    message = " ".join(s[1:])
                    self.send_response(code, message)
                    for header in response_headers:
                        self.send_header(*header)
                    self.end_headers()
                self.wfile.write(data)

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


def verbose_args(*args):
    if is_verbose:
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
    path_info = environ["PATH_INFO"]

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
    elif request_method == "POST" and path_info == "/query":
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


def start(
        address="localhost",
        port=8000,
        start_client=False,
        verbose=False):
    global is_verbose

    is_verbose = verbose

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProjPicker Web Server")
    parser.add_argument(
        "-a",
        "--address",
        default="localhost",
        help="specify the IP address on which the server listens (default: "
            "localhost)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="specify the port on which the server listens (port: 8000)",
    )
    parser.add_argument(
        "-c",
        "--client",
        action="store_true",
        help="start a new client in the user's default browser",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print debugging messages verbosely",
    )
    args = parser.parse_args()

    start(address=args.address,
          port=args.port,
          start_client=args.client,
          verbose=args.verbose)
