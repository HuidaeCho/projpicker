import wx

class mainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='ProjPicker')
        panel = wx.Panel(self)

        # Add left size for layout
        left = wx.BoxSizer(wx.VERTICAL)


        # CRS Choice listbox
        lbox = wx.ListBox(panel,
                id=1,
                size=(300, 600),
                choices=['test1', 'test2'],
                )

        # Add CRS listbox to main left side
        left.Add(lbox, 1, wx.ALL | wx.BOTTOM, 0)
        # Create bottom left sizer for buttons
        bottom_left = wx.BoxSizer(wx.HORIZONTAL)
        # Ok button
        btn_ok = wx.Button(panel, label='ok')
        # Cancel button
        btn_cancel = wx.Button(panel, label='Cancel')
        # Add buttons to bottom left
        bottom_left.Add(btn_ok, 0, wx.ALIGN_LEFT)
        bottom_left.Add(btn_cancel, 0, wx.ALIGN_LEFT)

        # Add bottom left sizer to left side sizer
        left.Add(bottom_left, 0, wx.BOTTOM | wx.LEFT)

        # Set sizer for main container
        panel.SetSizer(left)

        # Set size of window last otherwise sizers wont work.
        size = wx.Size(800, 700)
        self.SetSize(size)

        self.Show()


if __name__ == '__main__':
    app = wx.App()
    frame = mainFrame()
    app.MainLoop()
