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

import collections
import sys
import math
import urllib.request


class Tile:
    def __init__(self, key, x, y, z):
        self.key = key
        self.x = x
        self.y = y
        self.z = z
        self.rescaled_image = None


class CachedTile:
    def __init__(self, image, raw):
        self.image = image
        self.raw = raw


class OpenStreetMap:
    def __init__(self, create_image, draw_image, create_tile, draw_tile,
                 width=256, height=256, lat=0, lon=0, z=0, verbose=False):
        self.create_image = create_image
        self.draw_image = draw_image
        self.create_tile = create_tile
        self.draw_tile = draw_tile
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
        self.tiles = []
        self.rescaled_tiles = []
        # TODO: Tile caching mechanism
        self.cached_tiles = {}
        self.cancel = False

        self.redownload()
        self.draw()

    def message(self, *args, end=None):
        if self.verbose:
            print(*args, end=end, file=sys.stderr, flush=True)

    def resize(self, width, height):
        self.width = width
        self.height = height
        self.max_cached_tiles = int(2 * (width / 256) * (height / 256))
        self.redownload()

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

    def get_tile_url(self, x, y, z):
        return f"http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

    def download_tile(self, x, y, z):
        tile_url = self.get_tile_url(x, y, z)
        tile_key = f"{z}/{x}/{y}"
        if tile_key not in self.cached_tiles:
            # need this header to successfully download tiles from the server
            req = urllib.request.Request(tile_url, headers={
                "User-Agent": "urllib.request"
            })
            try:
                with urllib.request.urlopen(req) as f:
                    self.cached_tiles[tile_key] = CachedTile(f.read(), True)
                    self.message(f"{tile_url} downloaded")
            except Exception as e:
                self.message(f"{tile_url}: Failed to download")
        return tile_key

    def download(self, lat, lon, z):
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

        self.tiles.clear()

        self.message("image size:", self.width, self.height)

        for xi in range(xmin, xmax + 1):
            xt = xi % ntiles
            for yi in range(ymin, ymax + 1):
                if self.cancel:
                    self.message("download_map cancelled")
                    break
                tile_url = self.get_tile_url(xt, yi, z)
                tile_key = self.download_tile(xt, yi, z)
                tile_x = xoff + (xi - x) * 256
                while tile_x <= -256:
                    tile_x += 256 * ntiles
                while tile_x > self.width:
                    tile_x -= 256 * ntiles
                tile_y = yoff + (yi - y) * 256
                self.tiles.append(Tile(tile_key, tile_x, tile_y, z))
            if self.cancel:
                break
        self.rescaled_tiles = self.tiles.copy()

    def redownload(self):
        self.download(self.lat, self.lon, self.z)

    def draw(self):
        image = self.create_image(self.width, self.height)
        for tile in self.tiles:
            if tile.key in self.cached_tiles:
                cached_tile = self.cached_tiles[tile.key]
                if cached_tile.raw:
                    cached_tile.image = self.create_tile(cached_tile.image)
                    cached_tile.raw = False
                self.draw_tile(image, cached_tile.image, tile.x, tile.y)
        self.draw_image(image)

    def grab(self, x, y):
        self.grab_x = x
        self.grab_y = y

    def drag(self, x, y, draw=True):
        dx = x - self.grab_x
        dy = y - self.grab_y
        self.grab(x, y)
        x = self.width / 2 - dx
        y = self.height / 2 - dy
        lat, lon = self.canvas_to_latlon(x, y)
        old_lat = self.lat
        self.download(lat, lon, self.z)
        if abs(old_lat - self.lat) <= sys.float_info.epsilon:
            dy = 0
        if draw:
            self.draw()
        return dx, dy

    # XXX: EXPERIMENTAL! works only in a single-threaded mode without draw(); a
    # race condition with download_map() in the background thread? self.tiles
    # can get cleared by download_map(); tight zoom can cause
    # _tkinter.TclError: not enough free memory for image buffer
    def rescale(self, x, y, dz):
        z = min(max(self.z + dz, self.z_min), self.z_max)
        dz = z - self.z
        if dz != 0:
            xc, yc = self.width / 2, self.height / 2
            for i in range(0, abs(dz)):
                if dz > 0:
                    # each zoom-in doubles
                    xc = (x + xc) / 2
                    yc = (y + yc) / 2
                else:
                    # each zoom-out halves
                    xc = 2 * xc - x
                    yc = 2 * yc - y

            # recalculate xoff,yoff
            lat, lon = self.canvas_to_latlon(xc, yc)
            xt, yt = self.latlon_to_tile(lat, lon, z)
            xi, yi = int(xt), int(yt)
            n, w = self.tile_to_latlon(xi, yi, z)
            s, e = self.tile_to_latlon(xi + 1, yi + 1, z)
            xo, yo = self.latlon_to_tile(n, w, z)

            self.lat = lat
            self.lon = lon
            self.x = xi
            self.y = yi
            self.z = z
            self.xoff = int(self.width / 2 - (xt - xo) * 256)
            self.yoff = int(self.height / 2 - (yt - yo) * 256)

            samp_fac = 2**abs(dz)
            fac = 2**dz

            image = self.create_image(self.width, self.height)
            idx = []
            for i in range(len(self.rescaled_tiles)):
                tile = self.rescaled_tiles[i]
                if tile.key not in self.cached_tiles:
                    idx.append(i)
                    continue

                tile.x = self.width / 2 - fac * (xc - tile.x)
                tile.y = self.height / 2 - fac * (yc - tile.y)
                tile_size = 2**(z - tile.z) * 256

                if (tile.x + tile_size < 0 or tile.y + tile_size < 0 or
                    tile.x >= self.width or tile.y >= self.height):
                    idx.append(i)
                    continue

                if tile.rescaled_image:
                    tile_image = tile.rescaled_image
                else:
                    cached_tile = self.cached_tiles[tile.key]
                    if cached_tile.raw:
                        cached_tile.image = self.create_tile(cached_tile.image)
                        cached_tile.raw = False
                    tile_image = cached_tile.image
                if dz > 0:
                    # XXX: tkinter .zoom()
                    tile.rescaled_image = tile_image.zoom(samp_fac)
                else:
                    # XXX: tkinter .subsample()
                    tile.rescaled_image = tile_image.subsample(samp_fac)
                self.draw_tile(image, tile.rescaled_image, tile.x, tile.y)
            self.draw_image(image)

            for i in reversed(idx):
                del self.rescaled_tiles[i]

    def reset_zoom(self):
        self.dz = 0

    def zoom(self, x, y, dz, draw=True):
        zoomed = True
        self.dz += dz
        if ((self.z < self.z_max and self.dz >= 1) or
            (self.z > self.z_min and self.dz <= -1)):
            dz = 1 if self.dz > 0 else -1
            z = self.z + dz
            # pinned zoom at x,y
            if dz > 0:
                # each zoom-in doubles
                xc = (x + self.width / 2) / 2
                yc = (y + self.height / 2) / 2
                self.message("zoom in:", z)
            else:
                # each zoom-out halves
                xc = self.width - x
                yc = self.height - y
                self.message("zoom out:", z)
            # lat,lon at xc,yc
            lat, lon = self.canvas_to_latlon(xc, yc)
        elif ((self.z == self.z_max and self.dz >= 1) or
              (self.z == self.z_min and self.dz <= -1)):
            # need to download map for z_max or z_min because when the first
            # event of either zoom level was canceled, there are no cached
            # tiles
            lat, lon, z = self.lat, self.lon, self.z
        else:
            zoomed = False
        if zoomed:
            self.download(lat, lon, z)
            self.reset_zoom()
            if draw:
                self.draw()
        return zoomed

    def zoom_to_bbox(self, bbox, draw=True):
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

        self.download(lat, lon, z)
        if draw:
            self.draw()

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
