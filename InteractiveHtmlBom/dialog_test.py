import wx
from dialog.settings_dialog import *


class MyApp(wx.App):
    def OnInit(self):
        frame = SettingsDialog(None)
        frame.ShowModal()
        frame.Destroy()
        return True


app = MyApp()
app.MainLoop()

print("Done")
