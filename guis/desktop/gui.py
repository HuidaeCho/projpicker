# Use folium to stream in OpenStreetMap
#
# Has both pros and cons.
# If we use OpenStreetMap we will have to download and stream data in somehow.
# It would not be feasible to have an up to data OSM database with all levels of
# tiles.
# Folium allows us to use OSM quickly.
# It however would not allow easy integration into GRASS if we fail to make the
# GUi modular enough.
# So if we make it modular, say split core widgets from the actual view itself,
# it could be realistically used with any WX framework.
# But if our widgets are designed to get the events from one specific source,
# then it would not be able to used as fluidly as first hoped.
import json
import textwrap
import pprint
import wx
import wx.html2
import folium
from folium.plugins import Draw
from pathlib import Path
import projpicker as ppik
from dataclasses import dataclass


MAP = "openstreet.html"


@dataclass
class Geometry:
    type: str
    coors: list or tuple

    def flip(self):
        """
        Switch lat lon
        """
        corrected_coors = []
        if self.type == 'Point':
            corrected_coors = self.coors[1], self.coors[0]
        else:
            self.coors = self.coors[0]
            for i in self.coors:
                corrected_coors.append(i[::-1])
        self.coors = list(corrected_coors)


def generate_map():
    map_path = Path(MAP)
    print(str(map_path))
    if map_path.is_file():
        print("Map exists")
    else:
        print("Creating map")
        fmap = folium.Map([34.2347566, -83.8676613], zoom_start=5)
        Draw(
            export=False,
            filename="my_data.geojson",
            position="topleft",
            draw_options={"polyline": {"allowIntersection": False}},
            edit_options={"poly": {"allowIntersection": False}},
        ).add_to(fmap)
        fmap.save(MAP)


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.panel = wx.Panel(self)

        # Add left size for layout
        self.main = wx.BoxSizer(wx.HORIZONTAL)
        self.left = wx.BoxSizer(wx.VERTICAL)
        self.right = wx.BoxSizer(wx.VERTICAL)

        self.crs_list_box()
        self.buttons()

        # Add bottom left sizer to left side sizer
        self.main.Add(self.left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        self.crs_info("CRS Info")
        self.osm_map()

        # Add right to main
        self.main.Add(self.right, wx.ALIGN_RIGHT)
        # Set sizer for main container
        self.panel.SetSizer(self.main)

        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_LOADED, self.confirm_load)

        # Handler for the Document title change to read the json and trigger the ppik query
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.get_json)

        wx.EvtHandler.Bind(self, wx.EVT_LISTBOX, self.pop_info)


        # Set size of window last otherwise sizers wont work.
        width = 900
        height = 700
        size = wx.Size(width, height)
        self.SetMaxSize(size)
        self.SetMinSize(size)
        self.SetSize(size)

    #################################
    # LEFT
    def crs_list_box(self):
        st = wx.StaticText(self.panel, 0, "CRS List", pos=(0, 0))
        self.left.Add(st, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        self.left_width = 500
        self.left_height = 700

        # CRS Choice listbox
        self.lbox = wx.ListBox(
            self.panel,
            id=1,
            size=(self.left_width, self.left_height),
            choices=["Draw geometry to query CRS's"],
        )

        # Add CRS listbox to main left side
        self.left.Add(self.lbox, 1, wx.ALIGN_RIGHT | wx.ALL | wx.BOTTOM, 0)

    def buttons(self):
        width = self.left_width // 7
        # Create bottom left sizer for buttons
        btm_left = wx.BoxSizer(wx.HORIZONTAL)
        # Ok button
        self.btn_ok = wx.Button(self.panel, label="Ok")
        # Cancel button
        self.btn_cancel = wx.Button(self.panel, label="Cancel")
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.close)
        # Add buttons to bottom left
        btm_left.Add(self.btn_ok, 1, wx.LEFT | wx.RIGHT, width)
        btm_left.Add(self.btn_cancel, 1, wx.LEFT | wx.RIGHT, width)
        self.left.Add(btm_left, 0, wx.BOTTOM)


    #################################
    # RIGHT
    def crs_info(self, text):
        # CRS INFO
        # Set static box
        crs_info_box = wx.StaticBox(self.panel, 0, "CRS Info")
        # Create sizer for the box
        crs_info_vsizer = wx.StaticBoxSizer(crs_info_box, wx.HORIZONTAL)
        crs_info_hsizer = wx.BoxSizer(wx.VERTICAL)
        # Input text
        self.crs_info_text = wx.StaticText(self.panel, -1, text, style=wx.ALIGN_LEFT, size=(600, 300))
        # Set font
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(15)
        self.crs_info_text.SetFont(font)

        # Add text to correct sizer
        crs_info_vsizer.Add(self.crs_info_text, 1, wx.EXPAND, 100)
        crs_info_hsizer.Add(crs_info_vsizer, 1, wx.EXPAND, 10)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer(wx.HORIZONTAL)
        border.Add(crs_info_hsizer, 0, wx.ALL | wx.EXPAND, 10)
        # Add to right column
        self.right.Add(border, 1, wx.ALIGN_RIGHT, 100)

    def osm_map(self):

        # CANVAS
        self.browser = wx.html2.WebView.New(self.panel)


        Url = wx.FileSystem.FileNameToURL(MAP)
        self.browser.LoadURL(Url)
        browser_size = wx.BoxSizer(wx.HORIZONTAL)
        self.right.Add(self.browser, 1, wx.EXPAND | wx.ALL, 10)

    def pop_info(self, event):
        selection_index = self.lbox.GetSelection()
        selection_name = self.lbox.GetString(selection_index)

        try:
            for i in self.crs:
                if i.crs_name == selection_name:
                    crs_info = self.__crs_string(i)
            self.crs_info_text.SetLabel(crs_info)
        except AttributeError:
            self.crs_info_text.SetLabel('')

    def vertices_alert(self):
        wx.MessageBox("Too many vertices, please delete geometry.")

    def get_json(self, event):
        # Change title of HTML document within webview to the json.
        # Super hacky solution in due to lack of Wx webview event handlers.
        # Reads in the EVT_WEBVIEW_TITLE_CHANGED event which will then trigger the ProjPicker query
        pp = pprint.PrettyPrinter(indent=4)
        # Get new JSON from title
        # Document title can only grow to 999 chars so catch that error and alert
        try:
            self.json = json.loads(self.browser.GetCurrentTitle())
        except json.decoder.JSONDecodeError:
            self.vertices_alert()
            raise RuntimeError("Too many vertices. Delete geometry.")
        # temporary print
        #pp.pprint(self.json)
        self.query()

    def __crs_string(self, crs: list):
        return textwrap.dedent(f"""\
        CRS Type: {crs.proj_table.replace("_crs", "").capitalize()}
        CRS Code: {crs.crs_auth_name}:{crs.crs_code}
        Unit:     {crs.unit}
        South:    {crs.south_lat}°
        North:    {crs.north_lat}°
        West:     {crs.west_lon}°
        East:     {crs.east_lon}°
        Area:     {crs.area_sqkm:n} sqkm""")


    def query(self):
        features = self.json["features"]

        geoms = []
        for i in features:
            json_geo = i['geometry']
            geo_type = json_geo['type']
            coors = json_geo['coordinates']
            geo = Geometry(json_geo['type'], json_geo['coordinates'])
            geo.flip()
            geoms.extend(self.construct_ppik(geo))

        print(geoms)
        self.crs = ppik.query_mixed_geoms(geoms)
        #ppik.print_bbox(crs)


        self.lbox.Clear()
        crs_names = [i.crs_name for i in self.crs]
        self.lbox.InsertItems(crs_names, 0)

        # TODO: Modularize the code to enable event handlers based off the EVT_WEBVIEW_TITLE_CHANGED
        #       event.

    def construct_ppik(self, geo: Geometry):
        if geo.type == "Polygon":
            ppik_type = "poly"
            return [ppik_type, geo.coors]
        return ['latlon', geo.coors]

    def close(self, event):
        self.Close()

    def confirm_load(self, event):
        print("OpenStreetMap loaded.")




if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()
