from dialog.settings_dialog import *

class MyApp(wx.App):
    def OnInit(self):
        frame = SettingsDialog(lambda: None, lambda x: None, "Hi", 'test')
        if frame.ShowModal() == wx.ID_OK:
            print("Should generate bom")
        frame.Destroy()
        return True


app = MyApp()
app.MainLoop()

print("Done")
