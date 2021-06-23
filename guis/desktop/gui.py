import wx
import wx.lib.plot as plot
import json

CNTRYJSON = "./data/countries.json"


def get_country(path):
    with open(path) as f:
        data = json.load(f)

    return data


class mainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='ProjPicker')
        panel = wx.Panel(self)

        # Add left size for layout
        main = wx.BoxSizer(wx.HORIZONTAL)
        left = wx.BoxSizer(wx.VERTICAL)
        right = wx.BoxSizer(wx.VERTICAL)

        #################################
        # LEFT
        st = wx.StaticText(panel, -1, "CRS List", pos=(0,0))
        left.Add(st, 0, wx.CENTER | wx.TOP | wx.BOTTOM, 10)

        # CRS Choice listbox
        lbox = wx.ListBox(panel,
                id=1,
                size=(300, 600),
                choices=['test1', 'test2'],
                )

        # Add CRS listbox to main left side
        left.Add(lbox, 1, wx.ALIGN_RIGHT| wx.ALL | wx.BOTTOM, 0)
        # Create bottom left sizer for buttons
        btm_left = wx.BoxSizer(wx.HORIZONTAL)
        # Ok button
        btn_ok = wx.Button(panel, label='Ok')
        # Cancel button
        btn_cancel = wx.Button(panel, label='Cancel')
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
        canvas = plot.PlotCanvas(panel)

        # test data
        c_json = get_country(CNTRYJSON)
        data = c_json['features'][0]['geometry']['coordinates']
        print(data[0][0])
        com_data = []
        for i in data:
            for j in i:
                for ii in j:
                    com_data.append(ii)

        print(com_data)



        line = plot.PolyLine(com_data, legend='', colour='pink', width=2)
        gc = plot.PlotGraphics([line], 'Line Graph', 'X Axis', 'Y Axis')
        canvas.Draw(gc, xAxis=(-90,90), yAxis=(-180,180))
        right.Add(canvas, 1, wx.EXPAND, 100)

        # Add right to main
        main.Add(right, wx.ALIGN_RIGHT)
        # Set sizer for main container
        panel.SetSizer(main)

        # Set size of window last otherwise sizers wont work.
        size = wx.Size(800, 800)
        self.SetSize(size)

        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = mainFrame()
    app.MainLoop()
