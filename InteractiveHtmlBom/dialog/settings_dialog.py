import os
import re

import wx
import wx.grid

from . import dialog_base

if hasattr(wx, "GetLibraryVersionInfo"):
    WX_VERSION = wx.GetLibraryVersionInfo()  # type: wx.VersionInfo
    WX_VERSION = (WX_VERSION.Major, WX_VERSION.Minor, WX_VERSION.Micro)
else:
    # old kicad used this (exact version doesnt matter)
    WX_VERSION = (3, 0, 2)


def pop_error(msg):
    wx.MessageBox(msg, 'Error', wx.OK | wx.ICON_ERROR)


def get_btn_bitmap(bitmap):
    path = os.path.join(os.path.dirname(__file__), "bitmaps", bitmap)
    png = wx.Bitmap(path, wx.BITMAP_TYPE_PNG)

    if WX_VERSION >= (3, 1, 6):
        return wx.BitmapBundle(png)
    else:
        return png


class SettingsDialog(dialog_base.SettingsDialogBase):
    def __init__(self, extra_data_func, extra_data_wildcard, config_save_func,
                 file_name_format_hint, version):
        dialog_base.SettingsDialogBase.__init__(self, None)
        self.panel = SettingsDialogPanel(
            self, extra_data_func, extra_data_wildcard, config_save_func,
            file_name_format_hint)
        best_size = self.panel.BestSize
        # hack for some gtk themes that incorrectly calculate best size
        best_size.IncBy(dx=0, dy=30)
        self.SetClientSize(best_size)
        self.SetTitle('InteractiveHtmlBom %s' % version)

    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 4
            super(SettingsDialog, self).SetSizeHints(sz1, sz2)
        except TypeError:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)

    def set_extra_data_path(self, extra_data_file):
        self.panel.fields.extraDataFilePicker.Path = extra_data_file
        self.panel.fields.OnExtraDataFileChanged(None)


# Implementing settings_dialog
class SettingsDialogPanel(dialog_base.SettingsDialogPanel):
    def __init__(self, parent, extra_data_func, extra_data_wildcard,
                 config_save_func, file_name_format_hint):
        self.config_save_func = config_save_func
        dialog_base.SettingsDialogPanel.__init__(self, parent)
        self.general = GeneralSettingsPanel(self.notebook,
                                            file_name_format_hint)
        self.html = HtmlSettingsPanel(self.notebook)
        self.fields = FieldsPanel(self.notebook, extra_data_func,
                                  extra_data_wildcard)
        self.notebook.AddPage(self.general, "General")
        self.notebook.AddPage(self.html, "Html defaults")
        self.notebook.AddPage(self.fields, "Fields")

        self.save_menu = wx.Menu()
        self.save_locally = self.save_menu.Append(
            wx.ID_ANY, u"Locally", wx.EmptyString, wx.ITEM_NORMAL)
        self.save_globally = self.save_menu.Append(
            wx.ID_ANY, u"Globally", wx.EmptyString, wx.ITEM_NORMAL)

        self.Bind(
            wx.EVT_MENU, self.OnSaveLocally, id=self.save_locally.GetId())
        self.Bind(
            wx.EVT_MENU, self.OnSaveGlobally, id=self.save_globally.GetId())

    def OnExit(self, event):
        self.GetParent().EndModal(wx.ID_CANCEL)

    def OnGenerateBom(self, event):
        self.GetParent().EndModal(wx.ID_OK)

    def finish_init(self):
        self.html.OnBoardRotationSlider(None)

    def OnSave(self, event):
        # type: (wx.CommandEvent) -> None
        pos = wx.Point(0, event.GetEventObject().GetSize().y)
        self.saveSettingsBtn.PopupMenu(self.save_menu, pos)

    def OnSaveGlobally(self, event):
        self.config_save_func(self)

    def OnSaveLocally(self, event):
        self.config_save_func(self, locally=True)


# Implementing HtmlSettingsPanelBase
class HtmlSettingsPanel(dialog_base.HtmlSettingsPanelBase):
    def __init__(self, parent):
        dialog_base.HtmlSettingsPanelBase.__init__(self, parent)

    # Handlers for HtmlSettingsPanelBase events.
    def OnBoardRotationSlider(self, event):
        degrees = self.boardRotationSlider.Value * 5
        self.rotationDegreeLabel.LabelText = u"{}\u00B0".format(degrees)


# Implementing GeneralSettingsPanelBase
class GeneralSettingsPanel(dialog_base.GeneralSettingsPanelBase):

    def __init__(self, parent, file_name_format_hint):
        dialog_base.GeneralSettingsPanelBase.__init__(self, parent)

        self.file_name_format_hint = file_name_format_hint

        bmp_arrow_up = get_btn_bitmap("btn-arrow-up.png")
        bmp_arrow_down = get_btn_bitmap("btn-arrow-down.png")
        bmp_plus = get_btn_bitmap("btn-plus.png")
        bmp_minus = get_btn_bitmap("btn-minus.png")
        bmp_question = get_btn_bitmap("btn-question.png")

        self.m_btnSortUp.SetBitmap(bmp_arrow_up)
        self.m_btnSortDown.SetBitmap(bmp_arrow_down)
        self.m_btnSortAdd.SetBitmap(bmp_plus)
        self.m_btnSortRemove.SetBitmap(bmp_minus)
        self.m_btnNameHint.SetBitmap(bmp_question)
        self.m_btnBlacklistAdd.SetBitmap(bmp_plus)
        self.m_btnBlacklistRemove.SetBitmap(bmp_minus)

        self.Layout()

    # Handlers for GeneralSettingsPanelBase events.
    def OnComponentSortOrderUp(self, event):
        selection = self.componentSortOrderBox.Selection
        if selection != wx.NOT_FOUND and selection > 0:
            item = self.componentSortOrderBox.GetString(selection)
            self.componentSortOrderBox.Delete(selection)
            self.componentSortOrderBox.Insert(item, selection - 1)
            self.componentSortOrderBox.SetSelection(selection - 1)

    def OnComponentSortOrderDown(self, event):
        selection = self.componentSortOrderBox.Selection
        size = self.componentSortOrderBox.Count
        if selection != wx.NOT_FOUND and selection < size - 1:
            item = self.componentSortOrderBox.GetString(selection)
            self.componentSortOrderBox.Delete(selection)
            self.componentSortOrderBox.Insert(item, selection + 1)
            self.componentSortOrderBox.SetSelection(selection + 1)

    def OnComponentSortOrderAdd(self, event):
        item = wx.GetTextFromUser(
            "Characters other than A-Z will be ignored.",
            "Add sort order item")
        item = re.sub('[^A-Z]', '', item.upper())
        if item == '':
            return
        found = self.componentSortOrderBox.FindString(item)
        if found != wx.NOT_FOUND:
            self.componentSortOrderBox.SetSelection(found)
            return
        self.componentSortOrderBox.Append(item)
        self.componentSortOrderBox.SetSelection(
            self.componentSortOrderBox.Count - 1)

    def OnComponentSortOrderRemove(self, event):
        selection = self.componentSortOrderBox.Selection
        if selection != wx.NOT_FOUND:
            item = self.componentSortOrderBox.GetString(selection)
            if item == '~':
                pop_error("You can not delete '~' item")
                return
            self.componentSortOrderBox.Delete(selection)
            if self.componentSortOrderBox.Count > 0:
                self.componentSortOrderBox.SetSelection(max(selection - 1, 0))

    def OnComponentBlacklistAdd(self, event):
        item = wx.GetTextFromUser(
            "Characters other than A-Z 0-9 and * will be ignored.",
            "Add blacklist item")
        item = re.sub('[^A-Z0-9*]', '', item.upper())
        if item == '':
            return
        found = self.blacklistBox.FindString(item)
        if found != wx.NOT_FOUND:
            self.blacklistBox.SetSelection(found)
            return
        self.blacklistBox.Append(item)
        self.blacklistBox.SetSelection(self.blacklistBox.Count - 1)

    def OnComponentBlacklistRemove(self, event):
        selection = self.blacklistBox.Selection
        if selection != wx.NOT_FOUND:
            self.blacklistBox.Delete(selection)
            if self.blacklistBox.Count > 0:
                self.blacklistBox.SetSelection(max(selection - 1, 0))

    def OnNameFormatHintClick(self, event):
        wx.MessageBox(self.file_name_format_hint, 'File name format help',
                      style=wx.ICON_NONE | wx.OK)

    def OnSize(self, event):
        # Trick the listCheckBox best size calculations
        tmp = self.componentSortOrderBox.GetStrings()
        self.componentSortOrderBox.SetItems([])
        self.Layout()
        self.componentSortOrderBox.SetItems(tmp)


# Implementing FieldsPanelBase
class FieldsPanel(dialog_base.FieldsPanelBase):
    NONE_STRING = '<none>'
    FIELDS_GRID_COLUMNS = 3

    def __init__(self, parent, extra_data_func, extra_data_wildcard):
        dialog_base.FieldsPanelBase.__init__(self, parent)
        self.extra_data_func = extra_data_func
        self.extra_field_data = None

        self.m_btnUp.SetBitmap(get_btn_bitmap("btn-arrow-up.png"))
        self.m_btnDown.SetBitmap(get_btn_bitmap("btn-arrow-down.png"))

        self.set_file_picker_wildcard(extra_data_wildcard)
        self._setFieldsList([])
        for i in range(2):
            box = self.GetTextExtent(self.fieldsGrid.GetColLabelValue(i))
            if hasattr(box, "x"):
                width = box.x
            else:
                width = box[0]
            width = int(width * 1.1 + 5)
            self.fieldsGrid.SetColMinimalWidth(i, width)
            self.fieldsGrid.SetColSize(i, width)

        self.Layout()

    def set_file_picker_wildcard(self, extra_data_wildcard):
        if extra_data_wildcard is None:
            self.extraDataFilePicker.Disable()
            return

        # wxFilePickerCtrl doesn't support changing wildcard at runtime
        # so we have to replace it
        picker_parent = self.extraDataFilePicker.GetParent()
        new_picker = wx.FilePickerCtrl(
            picker_parent, wx.ID_ANY, wx.EmptyString,
            u"Select a file",
            extra_data_wildcard,
            wx.DefaultPosition, wx.DefaultSize,
            (wx.FLP_DEFAULT_STYLE | wx.FLP_FILE_MUST_EXIST | wx.FLP_OPEN |
             wx.FLP_SMALL | wx.FLP_USE_TEXTCTRL | wx.BORDER_SIMPLE))
        self.GetSizer().Replace(self.extraDataFilePicker, new_picker,
                                recursive=True)
        self.extraDataFilePicker.Destroy()
        self.extraDataFilePicker = new_picker
        self.Layout()

    def _swapRows(self, a, b):
        for i in range(self.FIELDS_GRID_COLUMNS):
            va = self.fieldsGrid.GetCellValue(a, i)
            vb = self.fieldsGrid.GetCellValue(b, i)
            self.fieldsGrid.SetCellValue(a, i, vb)
            self.fieldsGrid.SetCellValue(b, i, va)

    # Handlers for FieldsPanelBase events.
    def OnGridCellClicked(self, event):
        self.fieldsGrid.ClearSelection()
        self.fieldsGrid.SelectRow(event.Row)
        if event.Col < 2:
            # toggle checkbox
            val = self.fieldsGrid.GetCellValue(event.Row, event.Col)
            val = "" if val else "1"
            self.fieldsGrid.SetCellValue(event.Row, event.Col, val)
            # group shouldn't be enabled without show
            if event.Col == 0 and val == "":
                self.fieldsGrid.SetCellValue(event.Row, 1, val)
            if event.Col == 1 and val == "1":
                self.fieldsGrid.SetCellValue(event.Row, 0, val)

    def OnFieldsUp(self, event):
        selection = self.fieldsGrid.SelectedRows
        if len(selection) == 1 and selection[0] > 0:
            self._swapRows(selection[0], selection[0] - 1)
            self.fieldsGrid.ClearSelection()
            self.fieldsGrid.SelectRow(selection[0] - 1)

    def OnFieldsDown(self, event):
        selection = self.fieldsGrid.SelectedRows
        size = self.fieldsGrid.NumberRows
        if len(selection) == 1 and selection[0] < size - 1:
            self._swapRows(selection[0], selection[0] + 1)
            self.fieldsGrid.ClearSelection()
            self.fieldsGrid.SelectRow(selection[0] + 1)

    def _setFieldsList(self, fields):
        if self.fieldsGrid.NumberRows:
            self.fieldsGrid.DeleteRows(0, self.fieldsGrid.NumberRows)
        self.fieldsGrid.AppendRows(len(fields))
        row = 0
        for f in fields:
            self.fieldsGrid.SetCellValue(row, 0, "1")
            self.fieldsGrid.SetCellValue(row, 1, "1")
            self.fieldsGrid.SetCellRenderer(
                row, 0, wx.grid.GridCellBoolRenderer())
            self.fieldsGrid.SetCellRenderer(
                row, 1, wx.grid.GridCellBoolRenderer())
            self.fieldsGrid.SetCellValue(row, 2, f)
            self.fieldsGrid.SetCellAlignment(
                row, 2, wx.ALIGN_LEFT, wx.ALIGN_TOP)
            self.fieldsGrid.SetReadOnly(row, 2)
            row += 1

    def OnExtraDataFileChanged(self, event):
        extra_data_file = self.extraDataFilePicker.Path
        if not os.path.isfile(extra_data_file):
            return

        self.extra_field_data = None
        try:
            self.extra_field_data = self.extra_data_func(
                extra_data_file, self.normalizeCaseCheckbox.Value)
        except Exception as e:
            pop_error(
                "Failed to parse file %s\n\n%s" % (extra_data_file, e))
            self.extraDataFilePicker.Path = ''

        if self.extra_field_data is not None:
            field_list = list(self.extra_field_data[0])
            self._setFieldsList(["Value", "Footprint"] + field_list)
            field_list.append(self.NONE_STRING)
            self.boardVariantFieldBox.SetItems(field_list)
            self.boardVariantFieldBox.SetStringSelection(self.NONE_STRING)
            self.boardVariantWhitelist.Clear()
            self.boardVariantBlacklist.Clear()
            self.dnpFieldBox.SetItems(field_list)
            self.dnpFieldBox.SetStringSelection(self.NONE_STRING)

    def OnBoardVariantFieldChange(self, event):
        selection = self.boardVariantFieldBox.Value
        if not selection or selection == self.NONE_STRING \
                or self.extra_field_data is None:
            self.boardVariantWhitelist.Clear()
            self.boardVariantBlacklist.Clear()
            return
        variant_set = set()
        for _, field_dict in self.extra_field_data[1].items():
            if selection in field_dict:
                variant_set.add(field_dict[selection])
        self.boardVariantWhitelist.SetItems(list(variant_set))
        self.boardVariantBlacklist.SetItems(list(variant_set))

    def OnSize(self, event):
        self.Layout()
        g = self.fieldsGrid
        g.SetColSize(
            2, g.GetClientSize().x - g.GetColSize(0) - g.GetColSize(1) - 30)

    def GetShowFields(self):
        result = []
        for row in range(self.fieldsGrid.NumberRows):
            if self.fieldsGrid.GetCellValue(row, 0) == "1":
                result.append(self.fieldsGrid.GetCellValue(row, 2))
        return result

    def GetGroupFields(self):
        result = []
        for row in range(self.fieldsGrid.NumberRows):
            if self.fieldsGrid.GetCellValue(row, 1) == "1":
                result.append(self.fieldsGrid.GetCellValue(row, 2))
        return result

    def SetCheckedFields(self, show, group):
        group = [s for s in group if s in show]
        current = []
        for row in range(self.fieldsGrid.NumberRows):
            current.append(self.fieldsGrid.GetCellValue(row, 2))
        new = [s for s in current if s not in show]
        self._setFieldsList(show + new)
        for row in range(self.fieldsGrid.NumberRows):
            field = self.fieldsGrid.GetCellValue(row, 2)
            self.fieldsGrid.SetCellValue(row, 0, "1" if field in show else "")
            self.fieldsGrid.SetCellValue(row, 1, "1" if field in group else "")
