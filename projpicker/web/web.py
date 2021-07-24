#!/bin/env python3
import argparse
import http.server
import webbrowser
import json

import projpicker as ppik


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
    def message(self, *args):
        if hasattr(self.server, "message"):
            self.server.message(*args)
        else:
            print(*args)

    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/query":
            # http.client.HTTPResponse stores headers and implements
            # email.message.Message class'
            # https://docs.python.org/3/library/email.compat32-message.html#email.message.Message
            header = self.headers

            content_len = int(header.get("content-length"))
            content_charset = header.get_content_charset(failobj="utf-8")
            content_bytes = self.rfile.read(content_len)
            query = content_bytes.decode(content_charset)

            geoms = create_parsable_geoms(json.loads(query))
            self.message(f"{Color.BOLD}ProjPicker query{Color.ENDC}")
            self.message(f"{Color.BOLD}{'-'*79}{Color.ENDC}")
            self.message(geoms)
            self.message(f"{Color.BOLD}{'-'*79}{Color.ENDC}")

            geoms = ppik.parse_mixed_geoms(geoms)
            self.message(f"Query geometries: {geoms}")

            crs_list = ppik.query_mixed_geoms(geoms)
            self.message(f"Number of queried CRSs: {len(crs_list)}")

            outjson = bbox_to_json(crs_list)
            self.wfile.write(json.dumps(outjson).encode())


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


def run(server_class=http.server.HTTPServer,
        handler_class=HTTPRequestHandler,
        address="localhost",
        port=8000,
        start_client=False,
        verbose=False):
    server_address = (address, port)
    if address == "localhost":
        address += ":"
    httpd = server_class(server_address, handler_class)
    httpd.message = lambda *args: ppik.message(*args) if verbose else None

    try:
        ppik.message(f"{Color.OKGREEN}Starting httpd server on {address}{port}{Color.ENDC}")
        if start_client is True:
            webbrowser.open_new(f"{address}{port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        ppik.message(f"\n{Color.FAIL}Closed httpd server on {address}:{port}{Color.ENDC}")


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

    run(address=args.listen,
        port=args.port,
        start_client=args.client,
        verbose=args.verbose)
