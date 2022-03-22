import wx
from dialog.settings_dialog import SettingsDialog


class MyApp(wx.App):
    def OnInit(self):
        frame = SettingsDialog(lambda: None, None, lambda x: None, "Hi", 'test')
        if frame.ShowModal() == wx.ID_OK:
            print("Should generate bom")
        frame.Destroy()
        return True


app = MyApp()
app.MainLoop()

print("Done")
