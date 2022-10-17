# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b3)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.grid

###########################################################################
## Class SettingsDialogBase
###########################################################################

class SettingsDialogBase ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"InteractiveHtmlBom", pos = wx.DefaultPosition, size = wx.Size( 463,497 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP|wx.BORDER_DEFAULT )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )


        self.Centre( wx.BOTH )

    def __del__( self ):
        pass


###########################################################################
## Class SettingsDialogPanel
###########################################################################

class SettingsDialogPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 400,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer20 = wx.BoxSizer( wx.VERTICAL )

        self.notebook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_TOP|wx.BORDER_DEFAULT )

        bSizer20.Add( self.notebook, 1, wx.EXPAND |wx.ALL, 5 )

        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )

        self.saveSettingsBtn = wx.Button( self, wx.ID_ANY, u"Save current settings...", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )
        bSizer39.Add( self.saveSettingsBtn, 0, wx.ALL, 5 )


        bSizer39.Add( ( 50, 0), 1, wx.EXPAND, 5 )

        self.generateBomBtn = wx.Button( self, wx.ID_ANY, u"Generate BOM", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )

        self.generateBomBtn.SetDefault()
        bSizer39.Add( self.generateBomBtn, 0, wx.ALL, 5 )

        self.cancelBtn = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0|wx.BORDER_DEFAULT )
        bSizer39.Add( self.cancelBtn, 0, wx.ALL, 5 )


        bSizer20.Add( bSizer39, 0, wx.EXPAND, 5 )


        self.SetSizer( bSizer20 )
        self.Layout()

        # Connect Events
        self.saveSettingsBtn.Bind( wx.EVT_BUTTON, self.OnSave )
        self.generateBomBtn.Bind( wx.EVT_BUTTON, self.OnGenerateBom )
        self.cancelBtn.Bind( wx.EVT_BUTTON, self.OnExit )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnSave( self, event ):
        event.Skip()

    def OnGenerateBom( self, event ):
        event.Skip()

    def OnExit( self, event ):
        event.Skip()


###########################################################################
## Class HtmlSettingsPanelBase
###########################################################################

class HtmlSettingsPanelBase ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        b_sizer = wx.BoxSizer( wx.VERTICAL )

        self.darkModeCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Dark mode", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.darkModeCheckbox, 0, wx.ALL, 5 )

        self.showPadsCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Show footprint pads", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.showPadsCheckbox.SetValue(True)
        b_sizer.Add( self.showPadsCheckbox, 0, wx.ALL, 5 )

        self.showFabricationCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Show fabrication layer", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.showFabricationCheckbox, 0, wx.ALL, 5 )

        self.showSilkscreenCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Show silkscreen", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.showSilkscreenCheckbox.SetValue(True)
        b_sizer.Add( self.showSilkscreenCheckbox, 0, wx.ALL, 5 )

        self.highlightPin1Checkbox = wx.CheckBox( self, wx.ID_ANY, u"Highlight first pin", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.highlightPin1Checkbox, 0, wx.ALL, 5 )

        self.continuousRedrawCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Continuous redraw on drag", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.continuousRedrawCheckbox.SetValue(True)
        b_sizer.Add( self.continuousRedrawCheckbox, 0, wx.ALL, 5 )

        bSizer18 = wx.BoxSizer( wx.VERTICAL )

        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )

        self.m_boardRotationLabel = wx.StaticText( self, wx.ID_ANY, u"Board rotation", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_boardRotationLabel.Wrap( -1 )

        bSizer19.Add( self.m_boardRotationLabel, 0, wx.ALL, 5 )


        bSizer19.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.rotationDegreeLabel = wx.StaticText( self, wx.ID_ANY, u"0", wx.DefaultPosition, wx.Size( 30,-1 ), wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE )
        self.rotationDegreeLabel.Wrap( -1 )

        bSizer19.Add( self.rotationDegreeLabel, 0, wx.ALL, 5 )


        bSizer19.Add( ( 8, 0), 0, 0, 5 )


        bSizer18.Add( bSizer19, 1, wx.EXPAND, 5 )

        self.boardRotationSlider = wx.Slider( self, wx.ID_ANY, 0, -36, 36, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        bSizer18.Add( self.boardRotationSlider, 0, wx.ALL|wx.EXPAND, 5 )


        b_sizer.Add( bSizer18, 0, wx.EXPAND, 5 )

        self.offsetBackRotationCheckbox = wx.CheckBox( self, wx.ID_ANY, u"Offset back rotation", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.offsetBackRotationCheckbox, 0, wx.ALL, 5 )

        sbSizer31 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Checkboxes" ), wx.HORIZONTAL )

        self.bomCheckboxesCtrl = wx.TextCtrl( sbSizer31.GetStaticBox(), wx.ID_ANY, u"Sourced,Placed", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer31.Add( self.bomCheckboxesCtrl, 1, wx.ALL, 5 )


        b_sizer.Add( sbSizer31, 0, wx.ALL|wx.EXPAND, 5 )

        bomDefaultViewChoices = [ u"BOM only", u"BOM left, drawings right", u"BOM top, drawings bottom" ]
        self.bomDefaultView = wx.RadioBox( self, wx.ID_ANY, u"BOM View", wx.DefaultPosition, wx.DefaultSize, bomDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.bomDefaultView.SetSelection( 1 )
        b_sizer.Add( self.bomDefaultView, 0, wx.ALL|wx.EXPAND, 5 )

        layerDefaultViewChoices = [ u"Front only", u"Front and Back", u"Back only" ]
        self.layerDefaultView = wx.RadioBox( self, wx.ID_ANY, u"Layer View", wx.DefaultPosition, wx.DefaultSize, layerDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.layerDefaultView.SetSelection( 1 )
        b_sizer.Add( self.layerDefaultView, 0, wx.ALL|wx.EXPAND, 5 )

        sbSizer10 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Miscellaneous" ), wx.VERTICAL )

        self.compressionCheckbox = wx.CheckBox( sbSizer10.GetStaticBox(), wx.ID_ANY, u"Enable compression", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.compressionCheckbox.SetValue(True)
        sbSizer10.Add( self.compressionCheckbox, 0, wx.ALL, 5 )

        self.openBrowserCheckbox = wx.CheckBox( sbSizer10.GetStaticBox(), wx.ID_ANY, u"Open browser", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.openBrowserCheckbox.SetValue(True)
        sbSizer10.Add( self.openBrowserCheckbox, 0, wx.ALL, 5 )


        b_sizer.Add( sbSizer10, 1, wx.EXPAND, 5 )


        self.SetSizer( b_sizer )
        self.Layout()
        b_sizer.Fit( self )

        # Connect Events
        self.boardRotationSlider.Bind( wx.EVT_SLIDER, self.OnBoardRotationSlider )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnBoardRotationSlider( self, event ):
        event.Skip()


###########################################################################
## Class GeneralSettingsPanelBase
###########################################################################

class GeneralSettingsPanelBase ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer32 = wx.BoxSizer( wx.VERTICAL )

        sbSizer6 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Bom destination" ), wx.VERTICAL )

        fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
        fgSizer1.AddGrowableCol( 1 )
        fgSizer1.SetFlexibleDirection( wx.BOTH )
        fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.m_staticText8 = wx.StaticText( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Directory", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText8.Wrap( -1 )

        fgSizer1.Add( self.m_staticText8, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        self.bomDirPicker = wx.DirPickerCtrl( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select bom folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_SMALL|wx.DIRP_USE_TEXTCTRL|wx.BORDER_SIMPLE )
        fgSizer1.Add( self.bomDirPicker, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5 )

        self.m_staticText9 = wx.StaticText( sbSizer6.GetStaticBox(), wx.ID_ANY, u"Name format", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText9.Wrap( -1 )

        fgSizer1.Add( self.m_staticText9, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

        bSizer20 = wx.BoxSizer( wx.HORIZONTAL )

        self.fileNameFormatTextControl = wx.TextCtrl( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer20.Add( self.fileNameFormatTextControl, 1, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.LEFT|wx.TOP, 5 )

        self.m_btnNameHint = wx.Button( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnNameHint.SetMinSize( wx.Size( 30,30 ) )

        bSizer20.Add( self.m_btnNameHint, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


        fgSizer1.Add( bSizer20, 1, wx.EXPAND, 5 )


        sbSizer6.Add( fgSizer1, 1, wx.EXPAND, 5 )


        bSizer32.Add( sbSizer6, 0, wx.ALL|wx.EXPAND, 5 )

        sbSizer9 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Additional pcb data" ), wx.HORIZONTAL )

        self.includeTracksCheckbox = wx.CheckBox( sbSizer9.GetStaticBox(), wx.ID_ANY, u"Include tracks/zones", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer9.Add( self.includeTracksCheckbox, 1, wx.ALL, 5 )

        self.includeNetsCheckbox = wx.CheckBox( sbSizer9.GetStaticBox(), wx.ID_ANY, u"Include nets", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer9.Add( self.includeNetsCheckbox, 1, wx.ALL, 5 )


        bSizer32.Add( sbSizer9, 0, wx.ALL|wx.EXPAND, 5 )

        sortingSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component sort order" ), wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer6 = wx.BoxSizer( wx.VERTICAL )

        componentSortOrderBoxChoices = []
        self.componentSortOrderBox = wx.ListBox( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, componentSortOrderBoxChoices, wx.LB_SINGLE|wx.BORDER_SIMPLE )
        bSizer6.Add( self.componentSortOrderBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer4.Add( bSizer6, 1, wx.EXPAND, 5 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnSortUp = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnSortUp.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnSortUp, 0, wx.ALL, 5 )

        self.m_btnSortDown = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnSortDown.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnSortDown, 0, wx.ALL, 5 )

        self.m_btnSortAdd = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnSortAdd.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnSortAdd, 0, wx.ALL, 5 )

        self.m_btnSortRemove = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnSortRemove.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnSortRemove, 0, wx.ALL, 5 )


        bSizer4.Add( bSizer5, 0, 0, 5 )


        sortingSizer.Add( bSizer4, 1, wx.EXPAND, 5 )


        bSizer32.Add( sortingSizer, 1, wx.ALL|wx.EXPAND, 5 )

        blacklistSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component blacklist" ), wx.VERTICAL )

        bSizer412 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer612 = wx.BoxSizer( wx.VERTICAL )

        blacklistBoxChoices = []
        self.blacklistBox = wx.ListBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, blacklistBoxChoices, wx.LB_SINGLE|wx.LB_SORT|wx.BORDER_SIMPLE )
        bSizer612.Add( self.blacklistBox, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer412.Add( bSizer612, 1, wx.EXPAND, 5 )

        bSizer512 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnBlacklistAdd = wx.Button( blacklistSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnBlacklistAdd.SetMinSize( wx.Size( 30,30 ) )

        bSizer512.Add( self.m_btnBlacklistAdd, 0, wx.ALL, 5 )

        self.m_btnBlacklistRemove = wx.Button( blacklistSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnBlacklistRemove.SetMinSize( wx.Size( 30,30 ) )

        bSizer512.Add( self.m_btnBlacklistRemove, 0, wx.ALL, 5 )


        bSizer412.Add( bSizer512, 0, 0, 5 )


        blacklistSizer.Add( bSizer412, 1, wx.EXPAND, 5 )

        self.m_staticText1 = wx.StaticText( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Globs are supported, e.g. MH*", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )

        blacklistSizer.Add( self.m_staticText1, 0, wx.ALL, 5 )

        self.blacklistVirtualCheckbox = wx.CheckBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Blacklist virtual components", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.blacklistVirtualCheckbox.SetValue(True)
        blacklistSizer.Add( self.blacklistVirtualCheckbox, 0, wx.ALL, 5 )

        self.blacklistEmptyValCheckbox = wx.CheckBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Blacklist components with empty value", wx.DefaultPosition, wx.DefaultSize, 0 )
        blacklistSizer.Add( self.blacklistEmptyValCheckbox, 0, wx.ALL, 5 )


        bSizer32.Add( blacklistSizer, 1, wx.ALL|wx.EXPAND|wx.TOP, 5 )


        self.SetSizer( bSizer32 )
        self.Layout()
        bSizer32.Fit( self )

        # Connect Events
        self.Bind( wx.EVT_SIZE, self.OnSize )
        self.m_btnNameHint.Bind( wx.EVT_BUTTON, self.OnNameFormatHintClick )
        self.m_btnSortUp.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderUp )
        self.m_btnSortDown.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderDown )
        self.m_btnSortAdd.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderAdd )
        self.m_btnSortRemove.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderRemove )
        self.m_btnBlacklistAdd.Bind( wx.EVT_BUTTON, self.OnComponentBlacklistAdd )
        self.m_btnBlacklistRemove.Bind( wx.EVT_BUTTON, self.OnComponentBlacklistRemove )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnSize( self, event ):
        event.Skip()

    def OnNameFormatHintClick( self, event ):
        event.Skip()

    def OnComponentSortOrderUp( self, event ):
        event.Skip()

    def OnComponentSortOrderDown( self, event ):
        event.Skip()

    def OnComponentSortOrderAdd( self, event ):
        event.Skip()

    def OnComponentSortOrderRemove( self, event ):
        event.Skip()

    def OnComponentBlacklistAdd( self, event ):
        event.Skip()

    def OnComponentBlacklistRemove( self, event ):
        event.Skip()


###########################################################################
## Class FieldsPanelBase
###########################################################################

class FieldsPanelBase ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        bSizer42 = wx.BoxSizer( wx.VERTICAL )

        sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Extra data file" ), wx.VERTICAL )

        self.extraDataFilePicker = wx.FilePickerCtrl( sbSizer7.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select a file", u"Netlist and xml files (*.net; *.xml)|*.net;*.xml", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE|wx.FLP_FILE_MUST_EXIST|wx.FLP_OPEN|wx.FLP_SMALL|wx.FLP_USE_TEXTCTRL|wx.BORDER_SIMPLE )
        sbSizer7.Add( self.extraDataFilePicker, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )


        bSizer42.Add( sbSizer7, 0, wx.ALL|wx.EXPAND, 5 )

        fieldsSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Fields" ), wx.VERTICAL )

        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

        self.fieldsGrid = wx.grid.Grid( fieldsSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        # Grid
        self.fieldsGrid.CreateGrid( 2, 3 )
        self.fieldsGrid.EnableEditing( True )
        self.fieldsGrid.EnableGridLines( True )
        self.fieldsGrid.EnableDragGridSize( False )
        self.fieldsGrid.SetMargins( 0, 0 )

        # Columns
        self.fieldsGrid.AutoSizeColumns()
        self.fieldsGrid.EnableDragColMove( False )
        self.fieldsGrid.EnableDragColSize( True )
        self.fieldsGrid.SetColLabelValue( 0, u"Show" )
        self.fieldsGrid.SetColLabelValue( 1, u"Group" )
        self.fieldsGrid.SetColLabelValue( 2, u"Name" )
        self.fieldsGrid.SetColLabelSize( 30 )
        self.fieldsGrid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Rows
        self.fieldsGrid.EnableDragRowSize( False )
        self.fieldsGrid.SetRowLabelSize( 0 )
        self.fieldsGrid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Label Appearance

        # Cell Defaults
        self.fieldsGrid.SetDefaultCellAlignment( wx.ALIGN_CENTER, wx.ALIGN_TOP )
        bSizer4.Add( self.fieldsGrid, 1, wx.ALL|wx.EXPAND, 5 )

        bSizer5 = wx.BoxSizer( wx.VERTICAL )

        self.m_btnUp = wx.Button( fieldsSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnUp.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnUp, 0, wx.ALL, 5 )

        self.m_btnDown = wx.Button( fieldsSizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.BU_EXACTFIT )
        self.m_btnDown.SetMinSize( wx.Size( 30,30 ) )

        bSizer5.Add( self.m_btnDown, 0, wx.ALL, 5 )


        bSizer4.Add( bSizer5, 0, 0, 5 )


        fieldsSizer.Add( bSizer4, 1, wx.EXPAND, 5 )

        self.normalizeCaseCheckbox = wx.CheckBox( fieldsSizer.GetStaticBox(), wx.ID_ANY, u"Normalize field name case", wx.DefaultPosition, wx.DefaultSize, 0 )
        fieldsSizer.Add( self.normalizeCaseCheckbox, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer42.Add( fieldsSizer, 2, wx.ALL|wx.EXPAND, 5 )

        sbSizer32 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Board variant" ), wx.VERTICAL )

        self.m_staticText5 = wx.StaticText( sbSizer32.GetStaticBox(), wx.ID_ANY, u"Board variant field name", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText5.Wrap( -1 )

        sbSizer32.Add( self.m_staticText5, 0, wx.ALL, 5 )

        boardVariantFieldBoxChoices = []
        self.boardVariantFieldBox = wx.ComboBox( sbSizer32.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, boardVariantFieldBoxChoices, wx.CB_READONLY|wx.CB_SORT|wx.BORDER_SIMPLE )
        sbSizer32.Add( self.boardVariantFieldBox, 0, wx.ALL|wx.EXPAND, 5 )

        bSizer17 = wx.BoxSizer( wx.HORIZONTAL )

        bSizer18 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText6 = wx.StaticText( sbSizer32.GetStaticBox(), wx.ID_ANY, u"Whitelist", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText6.Wrap( -1 )

        bSizer18.Add( self.m_staticText6, 0, wx.ALL, 5 )

        boardVariantWhitelistChoices = []
        self.boardVariantWhitelist = wx.CheckListBox( sbSizer32.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, boardVariantWhitelistChoices, 0|wx.BORDER_SIMPLE )
        bSizer18.Add( self.boardVariantWhitelist, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer17.Add( bSizer18, 1, wx.EXPAND, 5 )

        bSizer19 = wx.BoxSizer( wx.VERTICAL )

        self.m_staticText7 = wx.StaticText( sbSizer32.GetStaticBox(), wx.ID_ANY, u"Blacklist", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText7.Wrap( -1 )

        bSizer19.Add( self.m_staticText7, 0, wx.ALL, 5 )

        boardVariantBlacklistChoices = []
        self.boardVariantBlacklist = wx.CheckListBox( sbSizer32.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, boardVariantBlacklistChoices, 0|wx.BORDER_SIMPLE )
        bSizer19.Add( self.boardVariantBlacklist, 1, wx.ALL|wx.EXPAND, 5 )


        bSizer17.Add( bSizer19, 1, wx.EXPAND, 5 )


        sbSizer32.Add( bSizer17, 1, wx.EXPAND, 5 )


        bSizer42.Add( sbSizer32, 3, wx.ALL|wx.EXPAND, 5 )

        sbSizer8 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"DNP field name" ), wx.VERTICAL )

        self.m_staticText4 = wx.StaticText( sbSizer8.GetStaticBox(), wx.ID_ANY, u"Components with this field not empty will be ignored", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( -1 )

        sbSizer8.Add( self.m_staticText4, 0, wx.ALL, 5 )

        dnpFieldBoxChoices = []
        self.dnpFieldBox = wx.ComboBox( sbSizer8.GetStaticBox(), wx.ID_ANY, u"-None-", wx.DefaultPosition, wx.DefaultSize, dnpFieldBoxChoices, wx.CB_READONLY|wx.CB_SORT|wx.BORDER_NONE )
        sbSizer8.Add( self.dnpFieldBox, 0, wx.ALL|wx.EXPAND, 5 )


        bSizer42.Add( sbSizer8, 0, wx.ALL|wx.EXPAND, 5 )


        self.SetSizer( bSizer42 )
        self.Layout()
        bSizer42.Fit( self )

        # Connect Events
        self.Bind( wx.EVT_SIZE, self.OnSize )
        self.extraDataFilePicker.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnExtraDataFileChanged )
        self.fieldsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.OnGridCellClicked )
        self.m_btnUp.Bind( wx.EVT_BUTTON, self.OnFieldsUp )
        self.m_btnDown.Bind( wx.EVT_BUTTON, self.OnFieldsDown )
        self.normalizeCaseCheckbox.Bind( wx.EVT_CHECKBOX, self.OnNetlistFileChanged )
        self.boardVariantFieldBox.Bind( wx.EVT_COMBOBOX, self.OnBoardVariantFieldChange )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnSize( self, event ):
        event.Skip()

    def OnExtraDataFileChanged( self, event ):
        event.Skip()

    def OnGridCellClicked( self, event ):
        event.Skip()

    def OnFieldsUp( self, event ):
        event.Skip()

    def OnFieldsDown( self, event ):
        event.Skip()

    def OnNetlistFileChanged( self, event ):
        event.Skip()

    def OnBoardVariantFieldChange( self, event ):
        event.Skip()
