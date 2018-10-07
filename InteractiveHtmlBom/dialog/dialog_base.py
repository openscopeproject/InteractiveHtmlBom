# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Aug  8 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class SettingsDialogBase
###########################################################################

class SettingsDialogBase ( wx.Dialog ):
    
    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"InteractiveHtmlBom", pos = wx.DefaultPosition, size = wx.Size( 463,497 ), style = wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP )
        
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        
        bSizer20 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_notebook1 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.NB_TOP )
        self.m_notebook1.SetForegroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )
        self.m_notebook1.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
        
        
        bSizer20.Add( self.m_notebook1, 1, wx.EXPAND |wx.ALL, 5 )
        
        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_button41 = wx.Button( self, wx.ID_ANY, u"Save current settings", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer39.Add( self.m_button41, 0, wx.ALL, 5 )
        
        
        bSizer39.Add( ( 50, 0), 0, wx.EXPAND, 5 )
        
        self.m_button42 = wx.Button( self, wx.ID_ANY, u"Generate BOM", wx.DefaultPosition, wx.DefaultSize, 0 )
        
        self.m_button42.SetDefault()
        bSizer39.Add( self.m_button42, 0, wx.ALL, 5 )
        
        self.m_button43 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer39.Add( self.m_button43, 0, wx.ALL, 5 )
        
        
        bSizer20.Add( bSizer39, 0, wx.ALIGN_CENTER, 5 )
        
        
        self.SetSizer( bSizer20 )
        self.Layout()
        
        self.Centre( wx.BOTH )
        
        # Connect Events
        self.m_button41.Bind( wx.EVT_BUTTON, self.OnSaveSettings )
        self.m_button42.Bind( wx.EVT_BUTTON, self.OnGenerateBom )
        self.m_button43.Bind( wx.EVT_BUTTON, self.OnExit )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def OnSaveSettings( self, event ):
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
        
        self.m_darkMode = wx.CheckBox( self, wx.ID_ANY, u"Dark mode", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.m_darkMode, 0, wx.ALL, 5 )
        
        self.m_showSilkscreen = wx.CheckBox( self, wx.ID_ANY, u"Show silkscreen", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_showSilkscreen.SetValue(True) 
        b_sizer.Add( self.m_showSilkscreen, 0, wx.ALL, 5 )
        
        self.m_highlightPin1 = wx.CheckBox( self, wx.ID_ANY, u"Highlight first pin", wx.DefaultPosition, wx.DefaultSize, 0 )
        b_sizer.Add( self.m_highlightPin1, 0, wx.ALL, 5 )
        
        self.m_continuousRedraw = wx.CheckBox( self, wx.ID_ANY, u"Continuous redraw on drag", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_continuousRedraw.SetValue(True) 
        b_sizer.Add( self.m_continuousRedraw, 0, wx.ALL, 5 )
        
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
        
        sbSizer31 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Checkboxes" ), wx.HORIZONTAL )
        
        self.m_textCtrl1 = wx.TextCtrl( sbSizer31.GetStaticBox(), wx.ID_ANY, u"Sourced,Placed", wx.DefaultPosition, wx.DefaultSize, 0 )
        sbSizer31.Add( self.m_textCtrl1, 1, wx.ALL, 5 )
        
        
        b_sizer.Add( sbSizer31, 0, wx.ALL|wx.EXPAND, 5 )
        
        m_bomDefaultViewChoices = [ u"BOM only", u"BOM left, drawings right", u"BOM top, drawings bottom" ]
        self.m_bomDefaultView = wx.RadioBox( self, wx.ID_ANY, u"BOM View", wx.DefaultPosition, wx.DefaultSize, m_bomDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.m_bomDefaultView.SetSelection( 1 )
        b_sizer.Add( self.m_bomDefaultView, 0, wx.ALL|wx.EXPAND, 5 )
        
        m_layerDefaultViewChoices = [ u"Front only", u"Front and Back", u"Back only" ]
        self.m_layerDefaultView = wx.RadioBox( self, wx.ID_ANY, u"Layer View", wx.DefaultPosition, wx.DefaultSize, m_layerDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.m_layerDefaultView.SetSelection( 1 )
        b_sizer.Add( self.m_layerDefaultView, 0, wx.ALL|wx.EXPAND, 5 )
        
        self.m_openBrowser = wx.CheckBox( self, wx.ID_ANY, u"Open browser", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_openBrowser.SetValue(True) 
        b_sizer.Add( self.m_openBrowser, 0, wx.ALL, 5 )
        
        
        self.SetSizer( b_sizer )
        self.Layout()
        b_sizer.Fit( self )
        
        # Connect Events
        self.boardRotationSlider.Bind( wx.EVT_SLIDER, self.OnBoardRotationSlider )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def OnBoardRotationSlider( self, event ):
        event.Skip()
    

###########################################################################
## Class GeneralSettingsPanelBase
###########################################################################

class GeneralSettingsPanelBase ( wx.Panel ):
    
    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )
        
        bSizer32 = wx.BoxSizer( wx.VERTICAL )
        
        sbSizer6 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Bom destination directory" ), wx.VERTICAL )
        
        self.m_bomDirPicker = wx.DirPickerCtrl( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select bom folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_SMALL )
        sbSizer6.Add( self.m_bomDirPicker, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )
        
        
        bSizer32.Add( sbSizer6, 0, wx.ALL|wx.EXPAND, 5 )
        
        sortingSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component sort order" ), wx.VERTICAL )
        
        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer6 = wx.BoxSizer( wx.VERTICAL )
        
        m_listBox2Choices = []
        self.m_listBox2 = wx.ListBox( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox2Choices, wx.LB_SINGLE )
        bSizer6.Add( self.m_listBox2, 1, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer4.Add( bSizer6, 1, wx.EXPAND, 5 )
        
        bSizer5 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_button1 = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button1, 0, wx.ALL, 5 )
        
        self.m_button2 = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"Dn", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button2, 0, wx.ALL, 5 )
        
        self.m_button3 = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button3, 0, wx.ALL, 5 )
        
        self.m_button4 = wx.Button( sortingSizer.GetStaticBox(), wx.ID_ANY, u"-", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button4, 0, wx.ALL, 5 )
        
        
        bSizer4.Add( bSizer5, 0, wx.ALIGN_RIGHT, 5 )
        
        
        sortingSizer.Add( bSizer4, 1, wx.EXPAND, 5 )
        
        
        bSizer32.Add( sortingSizer, 1, wx.ALL|wx.EXPAND, 5 )
        
        blacklistSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component blacklist" ), wx.VERTICAL )
        
        bSizer412 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer612 = wx.BoxSizer( wx.VERTICAL )
        
        m_listBox1Choices = []
        self.m_listBox1 = wx.ListBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox1Choices, wx.LB_SINGLE|wx.LB_SORT )
        bSizer612.Add( self.m_listBox1, 1, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer412.Add( bSizer612, 1, wx.EXPAND, 5 )
        
        bSizer512 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_button112 = wx.Button( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer512.Add( self.m_button112, 0, wx.ALL, 5 )
        
        self.m_button212 = wx.Button( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"-", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer512.Add( self.m_button212, 0, wx.ALL, 5 )
        
        
        bSizer412.Add( bSizer512, 0, wx.ALIGN_RIGHT, 5 )
        
        
        blacklistSizer.Add( bSizer412, 1, wx.EXPAND, 5 )
        
        self.m_staticText1 = wx.StaticText( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Globs are supported, e.g. MH*", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )
        
        blacklistSizer.Add( self.m_staticText1, 0, wx.ALL, 5 )
        
        self.m_checkBox4 = wx.CheckBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Blacklist virtual components", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox4.SetValue(True) 
        blacklistSizer.Add( self.m_checkBox4, 0, wx.ALL, 5 )
        
        
        bSizer32.Add( blacklistSizer, 1, wx.ALL|wx.EXPAND|wx.TOP, 5 )
        
        
        self.SetSizer( bSizer32 )
        self.Layout()
        bSizer32.Fit( self )
        
        # Connect Events
        self.m_button1.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderUp )
        self.m_button2.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderDown )
        self.m_button3.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderAdd )
        self.m_button4.Bind( wx.EVT_BUTTON, self.OnComponentSortOrderRemove )
        self.m_button112.Bind( wx.EVT_BUTTON, self.OnComponentBlacklistAdd )
        self.m_button212.Bind( wx.EVT_BUTTON, self.OnComponentBlacklistRemove )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
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
## Class ExtraFieldsPanelBase
###########################################################################

class ExtraFieldsPanelBase ( wx.Panel ):
    
    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )
        
        bSizer42 = wx.BoxSizer( wx.VERTICAL )
        
        sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Netlist or xml file" ), wx.VERTICAL )
        
        self.m_filePicker1 = wx.FilePickerCtrl( sbSizer7.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE|wx.FLP_FILE_MUST_EXIST|wx.FLP_OPEN|wx.FLP_SMALL )
        sbSizer7.Add( self.m_filePicker1, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )
        
        
        bSizer42.Add( sbSizer7, 0, wx.ALL|wx.EXPAND, 5 )
        
        extraFieldsSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Extra fields" ), wx.VERTICAL )
        
        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer6 = wx.BoxSizer( wx.VERTICAL )
        
        m_checkList1Choices = [u"a", u"b"]
        self.m_checkList1 = wx.CheckListBox( extraFieldsSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_checkList1Choices, wx.LB_MULTIPLE )
        bSizer6.Add( self.m_checkList1, 1, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer4.Add( bSizer6, 1, wx.EXPAND, 5 )
        
        bSizer5 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_button1 = wx.Button( extraFieldsSizer.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button1, 0, wx.ALL, 5 )
        
        self.m_button2 = wx.Button( extraFieldsSizer.GetStaticBox(), wx.ID_ANY, u"Dn", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer5.Add( self.m_button2, 0, wx.ALL, 5 )
        
        
        bSizer4.Add( bSizer5, 0, wx.ALIGN_RIGHT, 5 )
        
        
        extraFieldsSizer.Add( bSizer4, 1, wx.EXPAND, 5 )
        
        
        bSizer42.Add( extraFieldsSizer, 1, wx.ALL|wx.EXPAND, 5 )
        
        sbSizer32 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Board variant" ), wx.VERTICAL )
        
        m_comboBox1Choices = [ u"-None-" ]
        self.m_comboBox1 = wx.ComboBox( sbSizer32.GetStaticBox(), wx.ID_ANY, u"-None-", wx.DefaultPosition, wx.DefaultSize, m_comboBox1Choices, 0 )
        sbSizer32.Add( self.m_comboBox1, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer42.Add( sbSizer32, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        self.SetSizer( bSizer42 )
        self.Layout()
        bSizer42.Fit( self )
        
        # Connect Events
        self.m_button1.Bind( wx.EVT_BUTTON, self.OnExtraFieldsUp )
        self.m_button2.Bind( wx.EVT_BUTTON, self.OnExtraFieldsDown )
    
    def __del__( self ):
        pass
    
    
    # Virtual event handlers, overide them in your derived class
    def OnExtraFieldsUp( self, event ):
        event.Skip()
    
    def OnExtraFieldsDown( self, event ):
        event.Skip()
    

