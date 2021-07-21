################################################################################
# Project:  GetOSM <https://github.com/HuidaeCho/getosm>
# Authors:  Huidae Cho
# Since:    July 11, 2021
#
# Copyright (C) 2021 Huidae Cho <https://idea.isnew.info/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################
"""
This module provides an OpenStreetMap downloader.
"""

import sys
import math
import urllib.request


class OpenStreetMap:
    def __init__(self,
                 create_image_func, draw_image_func,
                 create_tile_func, draw_tile_func,
                 width=256, height=256,
                 lat=0, lon=0, z=0,
                 verbose=False):
        self.create_image_func = create_image_func
        self.draw_image_func = draw_image_func
        self.create_tile_func = create_tile_func
        self.draw_tile_func = draw_tile_func
        self.width = width
        self.height = height
        self.lat = lat
        self.lon = lon
        self.z = z
        self.verbose = verbose

        self.z_min = 0
        self.z_max = 18
        self.lat_min = -85.0511
        self.lat_max = 85.0511
        self.dz = 0
        # TODO: Tile caching mechanism
        self.tiles = {}

        self.redraw_map()

    def message(self, *args, end=None):
        if self.verbose:
            print(*args, end=end, file=sys.stderr, flush=True)

    def resize_map(self, width, height):
        self.width = width
        self.height = height
        self.max_cached_tiles = int(2 * (width / 256) * (height / 256))
        self.redraw_map()

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
        ntiles = 2**z

        if ntiles * 256 < self.height:
            lat = 0

        # calculate x,y offsets to lat,lon within width,height
        xc, yc = self.latlon_to_tile(lat, lon, z)
        x, y = int(xc), int(yc)
        n, w = self.tile_to_latlon(x, y, z)
        s, e = self.tile_to_latlon(x + 1, y + 1, z)
        xo, yo = self.latlon_to_tile(n, w, z)

        xoff = int(self.width / 2 - (xc - xo) * 256)
        yoff = int(self.height / 2 - (yc - yo) * 256)

        xmin = x - math.ceil(xoff / 256)
        ymin = max(y - math.ceil(yoff / 256), 0)
        xmax = x + math.ceil((self.width - xoff - 256) / 256)
        ymax = min(y + math.ceil((self.height - yoff - 256) / 256), ntiles - 1)

        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.z = z
        self.ntiles = ntiles
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.xoff = xoff
        self.yoff = yoff

        image = self.create_image_func(self.width, self.height)

        self.message("image size:", self.width, self.height)

        for xi in range(xmin, xmax + 1):
            xt = xi % ntiles
            for yi in range(ymin, ymax + 1):
                try:
                    tile_url = self.get_tile_url(xt, yi, z)
                    tile_image = self.download_tile(xt, yi, z)
                    tile_x = xoff + (xi - x) * 256
                    while tile_x <= -256:
                        tile_x += 256 * ntiles
                    while tile_x > self.width:
                        tile_x -= 256 * ntiles
                    tile_y = yoff + (yi - y) * 256
                    self.draw_tile_func(image, tile_image, tile_x, tile_y)
                    self.message(f"{tile_url} pasted at {tile_x},{tile_y}")
                except Exception as e:
                    self.message(f"Failed to download {tile_url}: {e}")
        self.draw_image_func(image)

    def redraw_map(self):
        self.draw_map(self.lat, self.lon, self.z)

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
        if abs(old_lat - self.lat) <= sys.float_info.epsilon:
            dy = 0
        return dx, dy

    def reset_zoom(self):
        self.dz = 0

    def zoom(self, x, y, dz):
        zoomed = False
        self.dz += dz
        if ((self.z < self.z_max and self.dz > 1) or
            (self.z > self.z_min and self.dz < -1)):
            dz = 1 if self.dz > 0 else -1
            z = self.z + dz
            if dz > 0:
                # each zoom in doubles
                x = (x + self.width / 2) / 2
                y = (y + self.height / 2) / 2
                self.message("zoom in:", z)
            else:
                # each zoom out halves
                x = self.width - x
                y = self.height - y
                self.message("zoom out:", z)
            # pinned zoom at x,y
            # lat,lon at x,y
            lat, lon = self.canvas_to_latlon(x, y)
            self.draw_map(lat, lon, z)
            self.reset_zoom()
            zoomed = True
        elif ((self.z == self.z_max and self.dz > 1) or
              (self.z == self.z_min and self.dz < -1)):
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

        # find the center
        l, t = self.latlon_to_tile(n, w, self.z)
        r, b = self.latlon_to_tile(s, e, self.z)
        lat, lon = self.tile_to_latlon((l + r) / 2, (t + b) / 2, self.z)

        # estimate z
        z_lat = math.log2((self.lat_max - self.lat_min) / (n - s))
        z_lon = math.log2(360 / dlon)
        z = math.ceil(min(z_lat, z_lon))

        # check if z covers the entire bbox
        l, t = self.latlon_to_tile(n, w, z)
        r, b = self.latlon_to_tile(s, e, z)
        width = (r - l) * 256
        height = (b - t) * 256

        if 2 * width <= self.width and 2 * height <= self.height:
            # if z is too loose, tighten it
            z += 1
        elif width > self.width or height > self.height:
            # if z is too tight, loosen it
            z -= 1

        self.draw_map(lat, lon, z)

        return [s, n, w, e]

    def repeat_xy(self, xy):
        outxy = []
        n = self.width // (256 * self.ntiles)
        for i in range(-n//2-1, n//2+2):
            dx = i * 256 * self.ntiles
            p = []
            for coor in xy:
                x, y = coor
                x += dx
                p.append([x, y])
            outxy.append(p)
        return outxy

    def get_xy(self, latlon):
        outxy = []
        if latlon:
            xy = []
            for coor in latlon:
                xy.append(self.latlon_to_canvas(*coor))
            outxy.extend(self.repeat_xy(xy))
        return outxy

    def get_bbox_xy(self, bbox):
        outxy = []
        if bbox:
            s, n, w, e = bbox
            l, t = self.latlon_to_canvas(n, w)
            r, b = self.latlon_to_canvas(s, e)
            if w > e:
                l -= 256 * self.ntiles
            xy = [[l, t], [r, b]]
            outxy.extend(self.repeat_xy(xy))
        return outxy
