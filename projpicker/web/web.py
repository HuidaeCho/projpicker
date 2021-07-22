#!/bin/env python3
from urllib import request, parse
import http.server
import json
import argparse
import projpicker as ppik
import time


VERBOSE = True

#################################
# Geometry
class Geometry:
    def __init__(self, type, coors):
        self.type = "poly" if type == "Polygon" else "point"

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


# Utility Functions
def create_parsable_geoms(geojson):
    # TODO: Logical operator buttons
    geoms = geojson['logicalOperator']
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

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def bbox_to_json(bbox_list):
    crs_json = {}
    for crs in bbox_list:
        entry = {}
        crs_dict = crs._asdict()
        for key in list(crs_dict.keys()):
            entry[key] = crs_dict[key]
        crs_json[f"{crs.crs_auth_name}:{crs.crs_code}"] = entry
    return crs_json


def query(geoms):
    crs_list = []
    crs = []
    if geoms is not None:
        print(f"{colors.BOLD}ProjPicker query{colors.ENDC}")
        print(f"{colors.BOLD}-----------------------------{colors.ENDC}")
        print(geoms)
        print(f"{colors.BOLD}-----------------------------{colors.ENDC}")
        parsed_geoms = ppik.parse_mixed_geoms(geoms)
        crs.extend(ppik.query_mixed_geoms(parsed_geoms))
        if VERBOSE:
            ppik.message(f"Query geometries: {parsed_geoms}")
            ppik.message(f"Number of queried CRSs: {len(crs)}")

    return crs



class HttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    global projpicker_query

    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

        elif self.path == '/projdata':
            time.sleep(2.5)
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            with open('projdata', 'r') as f:
                self.wfile.write(bytes(f.read(), "utf8"))
            #print(projpicker_query)



    def do_POST(self):
        if self.path == '/data':
            # http.client.HTTPResponse stores headers and implements
            # email.message.Message class'
            # https://docs.python.org/3/library/email.compat32-message.html#email.message.Message
            header = self.headers

            content_len = int(header.get('content-length'))
            content_charset = header.get_content_charset(failobj="utf-8")
            content_bytes = self.rfile.read(content_len)
            content_body = content_bytes.decode(content_charset)
            projpicker_query = content_body

            geoms = create_parsable_geoms(json.loads(content_body))
            crs_list = query(geoms)
            projpicker_query = bbox_to_json(crs_list)

            f = open("projdata", "w")
            f.write(json.dumps(projpicker_query))
            f.close()


def run(server_class=http.server.HTTPServer, handler_class=HttpRequestHandler, addr="localhost", port=8000):
    server_address = (addr, port)
    httpd = server_class(server_address, handler_class)

    try:
        print(f"{colors.OKGREEN}Starting httpd server on {addr}:{port}{colors.ENDC}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        print(f"\n{colors.FAIL}Closed httpd server on {addr}:{port}{colors.ENDC}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    args = parser.parse_args()
    run(addr=args.listen, port=args.port)