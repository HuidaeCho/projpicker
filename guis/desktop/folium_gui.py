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

MAP = "openstreet.html"


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
        panel = wx.Panel(self)

        # Add left size for layout
        main = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        right = wx.BoxSizer(wx.VERTICAL)

        #################################
        # LEFT
        st = wx.StaticText(panel, -1, "CRS List", pos=(0, 0))
        left.Add(st, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # CRS Choice listbox
        lbox = wx.ListBox(
            panel,
            id=1,
            size=(300, 600),
            choices=["test1", "test2"],
        )

        # Add CRS listbox to main left side
        left.Add(lbox, 1, wx.ALIGN_RIGHT | wx.ALL | wx.BOTTOM, 0)
        # Create bottom left sizer for buttons
        btm_left = wx.BoxSizer(wx.HORIZONTAL)
        # Ok button
        btn_ok = wx.Button(panel, label="Ok")
        # Cancel button
        btn_cancel = wx.Button(panel, label="Cancel")
        # Add buttons to bottom left
        btm_left.Add(btn_ok, 30, wx.LEFT | wx.RIGHT, 30)
        btm_left.Add(btn_cancel, 30, wx.LEFT | wx.RIGHT, 30)
        left.Add(btm_left, 0, wx.BOTTOM)

        # Add bottom left sizer to left side sizer
        main.Add(left, 0, wx.ALIGN_LEFT | wx.LEFT, 5)

        #################################
        # RIGHT

        # CRS INFO
        # Set static box
        crs_info_box = wx.StaticBox(panel, -1, "CRS Info")
        # Create sizer for the box
        crs_info_sizer = wx.StaticBoxSizer(crs_info_box, wx.VERTICAL)
        # Input text
        crs_info_text = wx.StaticText(panel, -1, "TEST\ntest1", style=wx.ALIGN_RIGHT)
        # Add text to correct sizer
        crs_info_sizer.Add(crs_info_text, 1, wx.EXPAND | wx.ALL | wx.CENTER, 200)
        # Create border
        # https://www.blog.pythonlibrary.org/2019/05/09/an-intro-to-staticbox-and-staticboxsizers/
        border = wx.BoxSizer()
        border.Add(crs_info_sizer, 1, wx.EXPAND | wx.ALL | wx.CENTER, 25)
        # Add to right column
        right.Add(border, 1, wx.ALIGN_RIGHT, 0)

        # CANVAS
        self.browser = wx.html2.WebView.New(panel)

        def confirm_load(event):
            print("OpenStreetMap loaded.")

        Url = wx.FileSystem.FileNameToURL(MAP)
        self.browser.LoadURL(Url)
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_LOADED, confirm_load)

        # Handler for the Document title change to read the json and trigger the ppik query
        wx.EvtHandler.Bind(self, wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.get_json)
        browser_size = wx.BoxSizer(wx.HORIZONTAL)
        right.Add(self.browser, 1, wx.EXPAND, 10)

        # Add right to main
        main.Add(right, wx.ALIGN_RIGHT)
        # Set sizer for main container
        panel.SetSizer(main)

        # Set size of window last otherwise sizers wont work.
        size = wx.Size(800, 800)
        self.SetSize(size)

    def get_json(self, event):
        # Change title of HTML document within webview to the json.
        # Super hacky solution in due to lack of Wx webview event handlers.
        # Reads in the EVT_WEBVIEW_TITLE_CHANGED event which will then trigger the ProjPicker query
        pp = pprint.PrettyPrinter(indent=4)
        # Get new JSON from title
        self.json = json.loads(self.browser.GetCurrentTitle())
        # temporary print
        pp.pprint(self.json)
        self.query()

    def __reverse_lat_lon(self, coors):
        """
        Switch lat lon
        """
        corrected_coors = []
        for i in coors[0]:
            corrected_coors.append(i[::-1])
        return corrected_coors

    def query(self):
        features = self.json["features"]
        if len(features) == 1:
            coors = features[0]["geometry"]["coordinates"]
            pprint.pprint(coors)
            corrected = self.__reverse_lat_lon(coors)
            bbox = ppik.query_polys(corrected)
            # Print bbox query for now
            ppik.print_bbox(bbox)
        else:
            print("Handle multiple geometry")

        # TODO: Modularize the code to enable event handlers based off the EVT_WEBVIEW_TITLE_CHANGED
        #       event.


if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame(None)
    frame.Show()
    app.MainLoop()
