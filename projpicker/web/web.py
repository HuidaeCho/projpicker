#!/usr/bin/env python3
"""
This module implements the standalone HTTP server, WSGI and CGI interfaces to
the ProjPicker Web client, index.html.
"""

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
default_server = f"{default_address}:{default_port}"


# https://gist.github.com/dideler/3814182
# https://gist.github.com/JBlond/2fea43a3049b38287e5e9cefc87b2124
class Color:
    """
    Define color constants using ANSI color codes.
    """
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
    """
    Implement the HTTP request handler for the standalone server.
    """
    # https://stackoverflow.com/a/52531444/16079666
    # how to specify a target directory?
    def __init__(self, *args, **kwargs):
        """
        Implement the constructor of the HTTP request handler.
        """
        return http.server.SimpleHTTPRequestHandler.__init__(
                self, *args, directory=module_path, **kwargs)

    def do_POST(self):
        """
        Override the do_POST method of the base class,
        http.server.SimpleHTTPRequestHandler.
        """
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
    """
    Print arguments if verbose printing is requested.

    Args:
        *args (arguments): Arguments to print.
    """
    if ppik.is_verbose():
        ppik.message(*args)


def verbose_color(color, *args):
    """
    Print colorized arguments if verbose printing is requested.

    Args:
        color (Color constant): Color for arguments.
        *args (arguments): Arguments to print.
    """
    verbose_args(color + "".join(*args) + Color.ENDC)


def verbose_line():
    """
    Print a bold line that is 79 columns wide if verbose printing is requested.
    """
    verbose_color(Color.BOLD, "-" * 79)


def verbose_header(*args):
    """
    Print arguments in bold if verbose printing is requested.

    Args:
        *args (arguments): Arguments to print.
    """
    verbose_color(Color.BOLD, *args)


def verbose_key_value(key, value):
    """
    Print a key-value pair if verbose printing is requested.

    Args:
        key (str): Key string.
        value (any type): Value object.
    """
    verbose_args(Color.BOLD + key + ": " + Color.ENDC + str(value))


def print_color(color, *args):
    """
    Print colorized arguments.

    Args:
        color (Color constant): Color for arguments.
        *args (arguments): Arguments to print.
    """
    ppik.message(color + "".join(*args) + Color.ENDC)


# Python Web Server Gateway Interface (WSGI)
# https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
def application(environ, start_response):
    """
    Implement the application function for the Web Server Gateway Interface
    (WSGI).

    Args:
        environ (dict): Dictionary of environment variables.
        start_response (function): Function to start a response.

    Returns:
        list: List of bytes responses.
    """
    remote_addr = environ["REMOTE_ADDR"]
    request_method = environ["REQUEST_METHOD"]
    path_info = environ.get("PATH_INFO", environ.get("REQUEST_URI"))

    status = "404 Not Found"
    content_type = "text/plain"
    response = "Invalid request"

    if request_method == "GET":
        file_path = None
        basename = os.path.basename(path_info)
        if basename == "":
            basename = "index.html"
        if basename in ("index.html",
                        "projpicker.css",
                        "projpicker.js"):
            file_path = os.path.join(module_path, basename)

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
    """
    Run the main application function for the standalone HTTP server and Common
    Gateway Interface (CGI).

    Args:
        environ (dict): Dictionary of environment variables.
        reader (function): Function to read data from the client. It should be
            able to read bytes data.
        send_response (function): Function to send the response to the client.
        send_header (function): Function to send headers to the client.
        end_headers (function): Function to stop sending headers to the client.
        write_data (function): Function to write data to the client. It should
            be able to write bytes data.
        flush_data (function): Function to top writing data to the client.
        https (bool): Whether or not the HTTP connection is secured. Defaults
            to False.

    Raises:
        AssertionError: If writing data is attempted before a new response is
            triggered or headers are being sent more than once.
        Exception: If exceptions are raised by the start_response() caller.
    """
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
    """
    Start the standalone HTTP server for the ProjPicker Web client. It should
    be only used for localhost desktop uses because it uses the standard
    http.server module, which is not recommended for production because it only
    implements basic security checks
    (https://docs.python.org/3/library/http.server.html). This server does not
    go into the background and uses the PROJPICKER_VERBOSE environment variable
    to verbosely print debugging messages. Set it to YES to print requested
    queries, parsed geometries, and queried CRSs. Do not set it or set it to NO
    to avoid these extra messages.

    Args:
        server (str): Server address and port number joined by a colon.
            Defaults to localhost:8000.
        start_client (bool): Whether or not to start the client in the browser.
            Defaults to False.

    Raises:
        Exception: If the server argument is not specified or the start fails
        to start.
    """
    server = server.strip()
    if not server:
        raise Exception("server:port is not specified")

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

    try:
        httpd = http.server.HTTPServer((address, port), HTTPRequestHandler)
    except:
        raise Exception(f"Failed to start HTTP server on {server}")

    url = f"http://{address}:{port}"
    if start_client is True:
        webbrowser.open(url)

    try:
        print_color(Color.OKGREEN, f"Starting HTTP server on {url}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print_color(Color.FAIL, f"\nClosed HTTP server on {url}")


def cgi():
    """
    Implement the Common Gateway Interface (CGI) of the web module.
    """
    SysStdinEncode = collections.namedtuple("SysStdinEncode", "read")

    run_application(
        os.environ.copy(),
        SysStdinEncode(lambda n: sys.stdin.read(n).encode()),
        lambda code, msg: sys.stdout.write(f"Status: {code} {msg}\r\n"),
        lambda *header: sys.stdout.write(f"{header[0]}: {header[1]}\r\n"),
        lambda: sys.stdout.write("\r\n"),
        lambda data: sys.stdout.write(data.decode()),
        sys.stdout.flush,
        os.environ.get("HTTPS", "off") == "on")


def main():
    """
    Implement the command-line interface to the standalone HTTP server.
    """
    parser = argparse.ArgumentParser(description="ProjPicker Web Server")
    parser.add_argument(
            "-S",
            "--server",
            default=default_server,
            help="specify the IP address and port on which the server listens "
                f"(default: {default_server})")
    parser.add_argument(
            "-c",
            "--client",
            action="store_true",
            help="start a new client in the user's default browser")
    args = parser.parse_args()

    start(server=args.server, start_client=args.client)


if __name__ == "__main__":
    if os.environ.get("GATEWAY_INTERFACE") == "CGI/1.1":
        sys.exit(cgi())
    else:
        sys.exit(main())
