"""
This module provides OpenStreetMap functions.
"""

import sys
import math
import urllib.request


class OpenStreetMap:
    def __init__(self, new_image_func, set_image_func, new_tile_func,
                 set_tile_func, verbose=False):
        self.new_image_func = new_image_func
        self.set_image_func = set_image_func
        self.new_tile_func = new_tile_func
        self.set_tile_func = set_tile_func
        self.verbose = verbose
        self.z_min = 0
        self.z_max = 18
        self.lat_min = 0
        self.lat_max = 0
        self.zoom_accum = 0
        # TODO: Tile caching mechanism
        self.tiles = {}


    def message(self, msg="", end=None):
        if self.verbose:
            print(msg, end=end, file=sys.stderr, flush=True)


    def set_map_size(self, width, height):
        self.width = width
        self.height = height
        self.max_cached_tiles = int(2 * (width / 256) * (height / 256))


    def get_tile_url(self, x, y, z):
        return f"http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"


    def download_tile(self, x, y, z):
        tile_url = self.get_tile_url(x, y, z)
        tile_key = f"{z}/{x}/{y}"
        if tile_key not in self.tiles:
            # need this header to successfully download tiles from the server
            req = urllib.request.Request(tile_url, headers={
                "User-Agent": "urllib.request"
            })
            with urllib.request.urlopen(req) as f:
                self.tiles[tile_key] = self.new_tile_func(f.read())
        tile_image = self.tiles[tile_key]
        return tile_image


    # Adapted from https://stackoverflow.com/a/62607111/16079666
    def latlon_to_tile(self, lat, lon, z):
        lat = math.radians(lat)
        n = 2**z
        x = int((lon+180)/360*n)
        y = int((1-math.log(math.tan(lat)+(1/math.cos(lat)))/math.pi)/2*n)
        return x, y


    def tile_to_nw_latlon(self, x, y, z):
        n = 2**z
        lat = math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))))
        lon = x/n*360-180
        return lat, lon


    def download_map(self, lat, lon, z):
        z = min(max(z, self.z_min), self.z_max)
        num_tiles = 2**z

        if num_tiles * 256 < self.height:
            lat = 0

        # cross the antimeridian
        if lon < -180:
            lon = 360 - lon
        elif lon > 180:
            lon -= 360

        # calculate x,y offsets to lat,lon within width,height
        x, y = self.latlon_to_tile(lat, lon, z)
        n, w = self.tile_to_nw_latlon(x, y, z)
        s, e = self.tile_to_nw_latlon(x + 1, y + 1, z)

        self.lat_dpp = (n - s) / 256
        self.lon_dpp = (w - e) / 256

        xoff = int(self.width / 2 + (lon - w) / self.lon_dpp)
        yoff = int(self.height / 2 + (lat - n) / self.lat_dpp)

        if num_tiles * 256 >= self.height:
            # restrict lat
            if yoff - y * 256 > 0:
                lat -= (yoff - y * 256) * self.lat_dpp

            # XXX: supposed to be < height - 1, but lat += (height - 1...
            # leaves a single-pixel border at the bottom; maybe, a rounding off
            # error
            elif yoff + (num_tiles - y) * 256 < self.height:
                lat += (self.height - yoff
                        - (num_tiles - y) * 256) * self.lat_dpp
            yoff = int(self.height / 2 + (lat - n) / self.lat_dpp)

        self.lat = lat
        self.lon = lon
        self.z = z

        xmin = x - math.ceil(xoff / 256)
        ymin = max(y - math.ceil(yoff / 256), 0)
        xmax = x + math.ceil((self.width - xoff - 256) / 256)
        ymax = min(y + math.ceil((self.height - yoff - 256) / 256),
                   num_tiles - 1)

        image = self.new_image_func(self.width, self.height)

        self.message(f"image size: {self.width} {self.height}")

        for xi in range(xmin, xmax + 1):
            xt = xi % num_tiles
            for yi in range(ymin, ymax + 1):
                try:
                    tile_url = self.get_tile_url(xt, yi, z)
                    tile_image = self.download_tile(xt, yi, z)
                    tile_x = xoff + (xi - x) * 256
                    while tile_x <= -256:
                        tile_x += 256 * num_tiles
                    while tile_x > self.width:
                        tile_x -= 256 * num_tiles
                    tile_y = yoff + (yi - y) * 256
                    self.set_tile_func(image, tile_image, tile_x, tile_y)
                    self.message(f"{tile_url} pasted at {tile_x},{tile_y}")
                except Exception as e:
                    self.message(f"Failed to download {tile_url}: {e}")
        return image


    def refresh_map(self, lat, lon, z):
        image = self.download_map(lat, lon, z)
        self.set_image_func(image)


    def start_dragging(self, x, y):
        self.drag_x = x
        self.drag_y = y


    def drag(self, x, y):
        dx = x - self.drag_x
        dy = y - self.drag_y
        lat = self.lat + self.lat_dpp * dy
        lon = self.lon + self.lon_dpp * dx
        self.start_dragging(x, y)
        self.refresh_map(lat, lon, self.z)
        return dx, dy


    def reset_zoom(self):
        self.zoom_accum = 0


    def zoom(self, x, y, zoom_accum):
        zoomed = False
        self.zoom_accum += zoom_accum / 10
        if ((self.z < self.z_max and self.zoom_accum > 1) or
            (self.z > self.z_min and self.zoom_accum < -1)):
            # pinned zoom at x,y
            # lat,lon at x,y
            lat = self.lat - self.lat_dpp * (y - self.height / 2)
            lon = self.lon - self.lon_dpp * (x - self.width / 2)
            dz = 1 if self.zoom_accum > 0 else -1
            z = self.z + dz
            if dz > 0:
                # each zoom up doubles
                lat = (lat + self.lat) / 2
                lon = (lon + self.lon) / 2
                self.message(f"zoom in: {z}")
            else:
                # each zoom down halves
                lat += (self.lat - lat) * 2
                lon += (self.lon - lon) * 2
                self.message(f"zoom out: {z}")
            self.refresh_map(lat, lon, z)
            self.reset_zoom()
            zoomed = True
        elif ((self.z == self.z_max and self.zoom_accum > 1) or
              (self.z == self.z_min and self.zoom_accum < -1)):
            self.reset_zoom()
        return zoomed


    def zoom_to_bbox(self, bbox):
        s, n, w, e = bbox

        lat = (s + n) / 2
        lat_dps = (n - s) / self.height

        if w == e or (w == -180 and e == 180):
            dlon = 360
            lon = e - 180 if e >= 0 else e
        elif w < e:
            dlon = e - w
            lon = (w + e) / 2
        else:
            dlon = 360 - w + e
            lon = (w + e) / 2
            lon = lon - 180 if lon >= 0 else lon + 180

        lon_dps = dlon / self.width

        z_lat = math.log2(180 / 256 / lat_dps)
        z_lon = math.log2(360 / 256 / lon_dps)
        z = math.floor(min(z_lat, z_lon))

        self.refresh_map(lat, lon, z)


    def get_xy(self, latlon):
        xy = []
        xc = self.width // 2
        yc = self.height // 2
        for coor in latlon:
            lat, lon = coor
            dlon = lon - self.lon
            if dlon > 180:
                dlon -= 360
            x = xc - dlon / self.lon_dpp
            y = yc - (lat - self.lat) / self.lat_dpp
            xy.append([x, y])
        return xy


    def get_latlon(self, xy):
        latlon = []
        xc = self.width // 2
        yc = self.height // 2
        for coor in xy:
            x, y = coor
            lat = self.lat - (y - yc) * self.lat_dpp
            lon = self.lon - (x - xc) * self.lon_dpp
            latlon.append([lat, lon])
        return latlon
