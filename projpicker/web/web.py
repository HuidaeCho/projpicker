#!/bin/env python3
import argparse
import os
import sys
import json
import webbrowser
import http.server

import projpicker as ppik

is_verbose = False


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


class Geometry:
    def __init__(self, typ, coors):
        self.type = "poly" if typ == "Polygon" else "point"

        # Reverse coordinates as leaflet returns opposite order of what
        # ProjPicker takes
        if self.type == "point":
            # Coordinates in "Point" type are single-depth tuple [i, j]
            self.coors = coors[::-1]
        else:
            # Coordinates in "Poly" type are in multi-depth array of size
            # [[[i0, j0], [i1, j1], ...]]; Move down array depth for easier
            # iteration
            latlon_coors = []
            for lonlat in coors[0]:
                latlon_coors.append(lonlat[::-1])
            self.coors = list(latlon_coors)


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


def message(*args):
    if is_verbose:
        ppik.message(*args)


def create_parsable_geoms(geojson):
    # TODO: Logical operator buttons
    geoms = geojson["logicalOperator"]
    for feature in geojson["features"]:
        json_geom = feature["geometry"]
        coors = json_geom["coordinates"]
        geom = Geometry(json_geom["type"], json_geom["coordinates"])
        geoms += f"\n{geom.type}"
        if geom.type == "point":
            geoms += f"\n{geom.coors[0]},{geom.coors[1]}"
        else:
            for coors in geom.coors:
                geoms += f"\n{coors[0]},{coors[1]}"
    return geoms


def bbox_to_json(bbox_list):
    crs_json = {}
    for crs in bbox_list:
        entry = {}
        crs_dict = crs._asdict()
        for key in list(crs_dict.keys()):
            entry[key] = crs_dict[key]
        crs_json[f"{crs.crs_auth_name}:{crs.crs_code}"] = entry
    return crs_json


# Python Web Server Gateway Interface (WSGI)
# https://www.python.org/dev/peps/pep-0333/#the-application-framework-side
def application(environ, start_response):
    remote_addr = environ["REMOTE_ADDR"]
    request_method = environ["REQUEST_METHOD"]
    path_info = environ["PATH_INFO"]

    status = "404 Not Found"
    content_type = "text/plain"
    response = b"Invalid request"

    if request_method == "GET":
        filename = None
        if path_info == "/":
            filename = "index.html"
        elif path_info in ("/index.html",
                           "/projpicker.css",
                           "/utils.js",
                           "/projpicker.js"):
            filename = path_info[1:]

        if filename and os.path.isfile(filename):
            status = "200 OK"
            if filename.endswith(".html"):
                content_type = "text/html"
            elif filename.endswith(".css"):
                content_type = "text/css"
            else:
                content_type = "text/javascript"
            with open(filename) as f:
                response = f.read().encode()
    elif request_method == "POST" and path_info == "/query":
        content_length = int(environ["CONTENT_LENGTH"])
        geoms = environ["wsgi.input"].read(content_length)#.decode()

        geoms = create_parsable_geoms(json.loads(geoms))
        message(f"{Color.BOLD}ProjPicker query{Color.ENDC}")
        message(f"{Color.BOLD}{'-'*79}{Color.ENDC}")
        message(geoms)
        message(f"{Color.BOLD}{'-'*79}{Color.ENDC}")

        geoms = ppik.parse_mixed_geoms(geoms)
        message(f"Query geometries: {geoms}")

        bbox = ppik.query_mixed_geoms(geoms)
        message(f"Number of queried CRSs: {len(bbox)}")

        response = json.dumps(bbox_to_json(bbox)).encode()

        status = "200 OK"
        content_type = "application/json"

    response_headers = [("Content-type", content_type)]
    start_response(status, response_headers)
    return [response]


def start(
        address="localhost",
        port=8000,
        start_client=False,
        verbose=False):
    global is_verbose

    is_verbose = verbose

    server_address = (address, port)
    httpd = http.server.HTTPServer(server_address, HTTPRequestHandler)

    if start_client is True:
        webbrowser.open_new(f"{address}:{port}")

    try:
        ppik.message(f"{Color.OKGREEN}Starting httpd server on "
                     f"{address}:{port}{Color.ENDC}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        ppik.message(f"\n{Color.FAIL}Closed httpd server on "
                     f"{address}:{port}{Color.ENDC}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ProjPicker Web Server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="specify the port on which the server listens",
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

    start(address=args.listen,
          port=args.port,
          start_client=args.client,
          verbose=args.verbose)
