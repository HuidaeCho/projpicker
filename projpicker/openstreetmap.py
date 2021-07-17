"""
This module provides OpenStreetMap functions.
"""

import sys
import math
import urllib.request


class OpenStreetMap:
    def __init__(self,
                 create_image_func, draw_image_func,
                 create_tile_func, draw_tile_func,
                 verbose=False):
        self.create_image_func = create_image_func
        self.draw_image_func = draw_image_func
        self.create_tile_func = create_tile_func
        self.draw_tile_func = draw_tile_func
        self.verbose = verbose
        self.z_min = 0
        self.z_max = 18
        self.lat_min = -85.0511
        self.lat_max = 85.0511
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
                self.tiles[tile_key] = self.create_tile_func(f.read())
        tile_image = self.tiles[tile_key]
        return tile_image


    # Adapted from https://stackoverflow.com/a/62607111/16079666
    # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    # x from 0 at lon=-180 to 2**z-1 at lon=180
    # y from 0 at lat=85.0511 to 2**z-1 at lat=-85.0511
    # tilex, tiley = int(x), int(y)
    def latlon_to_tile(self, lat, lon, z):
        lat = max(min(lat, self.lat_max), self.lat_min)
        lat = math.radians(lat)
        n = 2**z
        x = (lon+180)/360*n
        y = (1-math.log(math.tan(lat)+(1/math.cos(lat)))/math.pi)/2*n
        return x, y


    def tile_to_latlon(self, x, y, z):
        n = 2**z
        lat = math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))))
        lon = x/n*360-180
        return lat, lon


    def latlon_to_canvas(self, lat, lon):
        x, y = self.latlon_to_tile(lat, lon, self.z)
        x = self.xoff + (x - self.x) * 256
        y = self.yoff + (y - self.y) * 256
        return x, y


    def canvas_to_latlon(self, x, y):
        x = self.x + (x - self.xoff) / 256
        y = self.y + (y - self.yoff) / 256
        lat, lon = self.tile_to_latlon(x, y, self.z)
        while lon < -180:
            lon += 360
        while lon > 180:
            lon -= 360
        return lat, lon


    def draw_map(self, lat, lon, z):
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
        xc, yc = self.latlon_to_tile(lat, lon, z)
        x, y = int(xc), int(yc)
        n, w = self.tile_to_latlon(x, y, z)
        s, e = self.tile_to_latlon(x + 1, y + 1, z)
        xo, yo = self.latlon_to_tile(n, w, z)

        xoff = self.width / 2 - (xc - xo) * 256
        yoff = self.height / 2 - (yc - yo) * 256

        xmin = x - math.ceil(xoff / 256)
        ymin = max(y - math.ceil(yoff / 256), 0)
        xmax = x + math.ceil((self.width - xoff - 256) / 256)
        ymax = min(y + math.ceil((self.height - yoff - 256) / 256),
                   num_tiles - 1)

        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.z = z
        self.num_tiles = num_tiles
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.xoff = xoff
        self.yoff = yoff

        image = self.create_image_func(self.width, self.height)

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
                    self.draw_tile_func(image, tile_image, tile_x, tile_y)
                    self.message(f"{tile_url} pasted at {tile_x},{tile_y}")
                except Exception as e:
                    self.message(f"Failed to download {tile_url}: {e}")
        self.draw_image_func(image)


    def start_dragging(self, x, y):
        self.drag_x = x
        self.drag_y = y


    def drag(self, x, y):
        dx = x - self.drag_x
        dy = y - self.drag_y
        self.start_dragging(x, y)
        x = self.width / 2 - dx
        y = self.height / 2 - dy
        lat, lon = self.canvas_to_latlon(x, y)
        old_lat = self.lat
        self.draw_map(lat, lon, self.z)
        return dx, dy if abs(old_lat - self.lat) > sys.float_info.epsilon else 0


    def reset_zoom(self):
        self.zoom_accum = 0


    def zoom(self, x, y, zoom_accum):
        zoomed = False
        self.zoom_accum += zoom_accum / 10
        if ((self.z < self.z_max and self.zoom_accum > 1) or
            (self.z > self.z_min and self.zoom_accum < -1)):
            dz = 1 if self.zoom_accum > 0 else -1
            z = self.z + dz
            if dz > 0:
                # each zoom in doubles
                x = (x + self.width / 2) / 2
                y = (y + self.height / 2) / 2
                self.message(f"zoom in: {z}")
            else:
                # each zoom out halves
                x = self.width - x
                y = self.height - y
                self.message(f"zoom out: {z}")
            # pinned zoom at x,y
            # lat,lon at x,y
            lat, lon = self.canvas_to_latlon(x, y)
            self.draw_map(lat, lon, z)
            self.reset_zoom()
            zoomed = True
        elif ((self.z == self.z_max and self.zoom_accum > 1) or
              (self.z == self.z_min and self.zoom_accum < -1)):
            self.reset_zoom()
        return zoomed


    def zoom_to_bbox(self, bbox):
        s, n, w, e = bbox

        lat = (s + n) / 2

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
        e = w + dlon

        xul, yul = self.latlon_to_tile(n, w, self.z)
        xlr, ylr = self.latlon_to_tile(s, e, self.z)
        lat, lon = self.tile_to_latlon((xul+xlr)/2, (yul+ylr)/2, self.z)

        z_lat = math.log2(180 / (n - s))
        z_lon = math.log2(360 / dlon)
        z = math.floor(min(z_lat, z_lon))

        self.draw_map(lat, lon, z)

        return [s, n, w, e]


    def get_xy(self, latlon):
        xy = []
        if not latlon:
            return xy

        c = []
        for coor in latlon:
            c.append(self.latlon_to_canvas(*coor))

        n = self.width // (256 * self.num_tiles)
        for i in range(-n//2-1, n//2+2):
            dx = i * 256 * self.num_tiles
            p = []
            for coor in c:
                x, y = coor
                x += dx
                p.append([x, y])
            xy.append(p)
        return xy
