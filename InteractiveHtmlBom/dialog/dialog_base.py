# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Aug  8 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.dataview

###########################################################################
## Class settings_dialog
###########################################################################

class settings_dialog ( wx.Dialog ):
    
    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Interactive Html Bom", pos = wx.DefaultPosition, size = wx.Size( 600,750 ), style = wx.CAPTION|wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP )
        
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        
        vSizer = wx.BoxSizer( wx.VERTICAL )
        
        bSizer38 = wx.BoxSizer( wx.HORIZONTAL )
        
        leftSizer = wx.BoxSizer( wx.VERTICAL )
        
        htmlSettings = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Html defaults" ), wx.VERTICAL )
        
        self.m_darkMode = wx.CheckBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Dark mode", wx.DefaultPosition, wx.DefaultSize, 0 )
        htmlSettings.Add( self.m_darkMode, 0, wx.ALL, 5 )
        
        self.m_showSilkscreen = wx.CheckBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Show silkscreen", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_showSilkscreen.SetValue(True) 
        htmlSettings.Add( self.m_showSilkscreen, 0, wx.ALL, 5 )
        
        self.m_highlightPin1 = wx.CheckBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Highlight first pin", wx.DefaultPosition, wx.DefaultSize, 0 )
        htmlSettings.Add( self.m_highlightPin1, 0, wx.ALL, 5 )
        
        self.m_continuousRedraw = wx.CheckBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Continuous redraw on drag", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_continuousRedraw.SetValue(True) 
        htmlSettings.Add( self.m_continuousRedraw, 0, wx.ALL, 5 )
        
        bSizer18 = wx.BoxSizer( wx.VERTICAL )
        
        bSizer19 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_boardRotationLabel = wx.StaticText( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Board rotation", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_boardRotationLabel.Wrap( -1 )
        
        bSizer19.Add( self.m_boardRotationLabel, 0, wx.ALL, 5 )
        
        
        bSizer19.Add( ( 0, 0), 1, wx.EXPAND, 5 )
        
        self.m_rotationDegree = wx.StaticText( htmlSettings.GetStaticBox(), wx.ID_ANY, u"0", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_rotationDegree.Wrap( -1 )
        
        bSizer19.Add( self.m_rotationDegree, 0, wx.ALL, 5 )
        
        
        bSizer19.Add( ( 8, 0), 0, 0, 5 )
        
        
        bSizer18.Add( bSizer19, 1, wx.EXPAND, 5 )
        
        self.m_rotationSlider = wx.Slider( htmlSettings.GetStaticBox(), wx.ID_ANY, 0, -36, 36, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
        bSizer18.Add( self.m_rotationSlider, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        htmlSettings.Add( bSizer18, 1, wx.EXPAND, 5 )
        
        m_bomDefaultViewChoices = [ u"BOM only", u"BOM left, drawings right", u"BOM top, drawings bottom" ]
        self.m_bomDefaultView = wx.RadioBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"BOM View", wx.DefaultPosition, wx.DefaultSize, m_bomDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.m_bomDefaultView.SetSelection( 1 )
        htmlSettings.Add( self.m_bomDefaultView, 0, wx.ALL|wx.EXPAND, 5 )
        
        m_layerDefaultViewChoices = [ u"Front only", u"Front and Back", u"Back only" ]
        self.m_layerDefaultView = wx.RadioBox( htmlSettings.GetStaticBox(), wx.ID_ANY, u"Layer View", wx.DefaultPosition, wx.DefaultSize, m_layerDefaultViewChoices, 1, wx.RA_SPECIFY_COLS )
        self.m_layerDefaultView.SetSelection( 1 )
        htmlSettings.Add( self.m_layerDefaultView, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        leftSizer.Add( htmlSettings, 0, wx.ALL|wx.EXPAND, 5 )
        
        blacklistSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component blacklist" ), wx.VERTICAL )
        
        self.m_checkBox4 = wx.CheckBox( blacklistSizer.GetStaticBox(), wx.ID_ANY, u"Blacklist virtual components", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_checkBox4.SetValue(True) 
        blacklistSizer.Add( self.m_checkBox4, 0, wx.ALL, 5 )
        
        bSizer412 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer612 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_sortOrderCtrl12 = wx.dataview.DataViewListCtrl( blacklistSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,100 ), 0 )
        self.m_dataViewListColumn82 = self.m_sortOrderCtrl12.AppendTextColumn( u"Reference", wx.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_LEFT, 0 ) 
        bSizer612.Add( self.m_sortOrderCtrl12, 1, wx.ALL|wx.EXPAND, 5 )
        
        
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
        
        
        leftSizer.Add( blacklistSizer, 1, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer38.Add( leftSizer, 1, wx.EXPAND, 5 )
        
        rightSizer = wx.BoxSizer( wx.VERTICAL )
        
        bomCheckboxesSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"BOM checkboxes" ), wx.VERTICAL )
        
        bSizer411 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer611 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_sortOrderCtrl11 = wx.dataview.DataViewListCtrl( bomCheckboxesSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,150 ), 0 )
        self.m_dataViewListColumn81 = self.m_sortOrderCtrl11.AppendTextColumn( u"Name", wx.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_LEFT, 0 ) 
        bSizer611.Add( self.m_sortOrderCtrl11, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer411.Add( bSizer611, 1, wx.EXPAND, 5 )
        
        bSizer511 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_button111 = wx.Button( bomCheckboxesSizer.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer511.Add( self.m_button111, 0, wx.ALL, 5 )
        
        self.m_button211 = wx.Button( bomCheckboxesSizer.GetStaticBox(), wx.ID_ANY, u"Dn", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer511.Add( self.m_button211, 0, wx.ALL, 5 )
        
        self.m_button311 = wx.Button( bomCheckboxesSizer.GetStaticBox(), wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer511.Add( self.m_button311, 0, wx.ALL, 5 )
        
        self.m_button411 = wx.Button( bomCheckboxesSizer.GetStaticBox(), wx.ID_ANY, u"-", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer511.Add( self.m_button411, 0, wx.ALL, 5 )
        
        
        bSizer411.Add( bSizer511, 0, wx.ALIGN_RIGHT, 5 )
        
        
        bomCheckboxesSizer.Add( bSizer411, 1, wx.EXPAND, 5 )
        
        
        rightSizer.Add( bomCheckboxesSizer, 0, wx.ALL|wx.EXPAND, 5 )
        
        sortingSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Component sort order" ), wx.VERTICAL )
        
        bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer6 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_sortOrderCtrl = wx.dataview.DataViewListCtrl( sortingSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,150 ), 0 )
        self.m_componentPrefix = self.m_sortOrderCtrl.AppendTextColumn( u"Prefix", wx.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, 0 )
        self.m_componentPrefix.GetRenderer().EnableEllipsize( wx.ELLIPSIZE_END );
        bSizer6.Add( self.m_sortOrderCtrl, 1, wx.ALL|wx.EXPAND, 5 )
        
        
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
        
        
        rightSizer.Add( sortingSizer, 1, wx.ALL|wx.EXPAND, 5 )
        
        extrafieldsSizer = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Extra fields from netlist" ), wx.VERTICAL )
        
        bSizer41 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer61 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_sortOrderCtrl1 = wx.dataview.DataViewListCtrl( extrafieldsSizer.GetStaticBox(), wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,100 ), 0 )
        self.m_componentPrefix1 = self.m_sortOrderCtrl1.AppendToggleColumn( wx.EmptyString, wx.DATAVIEW_CELL_EDITABLE, -1, wx.ALIGN_LEFT, 0 )
        self.m_componentPrefix1.GetRenderer().EnableEllipsize( wx.ELLIPSIZE_END );
        self.m_dataViewListColumn8 = self.m_sortOrderCtrl1.AppendTextColumn( u"Field", wx.DATAVIEW_CELL_ACTIVATABLE, -1, wx.ALIGN_LEFT, 0 ) 
        bSizer61.Add( self.m_sortOrderCtrl1, 0, wx.EXPAND|wx.ALL, 5 )
        
        
        bSizer41.Add( bSizer61, 1, wx.EXPAND, 5 )
        
        bSizer51 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_button11 = wx.Button( extrafieldsSizer.GetStaticBox(), wx.ID_ANY, u"Up", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer51.Add( self.m_button11, 0, wx.ALL, 5 )
        
        self.m_button21 = wx.Button( extrafieldsSizer.GetStaticBox(), wx.ID_ANY, u"Dn", wx.DefaultPosition, wx.Size( 30,30 ), 0 )
        bSizer51.Add( self.m_button21, 0, wx.ALL, 5 )
        
        
        bSizer41.Add( bSizer51, 0, wx.ALIGN_RIGHT, 5 )
        
        
        extrafieldsSizer.Add( bSizer41, 1, wx.EXPAND, 5 )
        
        
        rightSizer.Add( extrafieldsSizer, 0, wx.ALL|wx.EXPAND, 5 )
        
        sbSizer7 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Netlist file" ), wx.VERTICAL )
        
        self.m_filePicker1 = wx.FilePickerCtrl( sbSizer7.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE|wx.FLP_SMALL )
        sbSizer7.Add( self.m_filePicker1, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )
        
        
        rightSizer.Add( sbSizer7, 0, wx.ALL|wx.EXPAND, 5 )
        
        sbSizer6 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"Bom destination directory" ), wx.VERTICAL )
        
        self.m_bomDirPicker = wx.DirPickerCtrl( sbSizer6.GetStaticBox(), wx.ID_ANY, wx.EmptyString, u"Select bom folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE|wx.DIRP_SMALL )
        sbSizer6.Add( self.m_bomDirPicker, 0, wx.EXPAND|wx.BOTTOM|wx.RIGHT|wx.LEFT, 5 )
        
        
        rightSizer.Add( sbSizer6, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer38.Add( rightSizer, 1, wx.EXPAND, 5 )
        
        
        vSizer.Add( bSizer38, 1, wx.EXPAND, 5 )
        
        bSizer39 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.m_button41 = wx.Button( self, wx.ID_ANY, u"Save current settings", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer39.Add( self.m_button41, 0, wx.ALL, 5 )
        
        
        bSizer39.Add( ( 100, 0), 1, wx.EXPAND, 5 )
        
        self.m_openBrowser = wx.CheckBox( self, wx.ID_ANY, u"Open browser", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_openBrowser.SetValue(True) 
        bSizer39.Add( self.m_openBrowser, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
        
        self.m_button42 = wx.Button( self, wx.ID_ANY, u"Generate BOM", wx.DefaultPosition, wx.DefaultSize, 0 )
        
        self.m_button42.SetDefault()
        bSizer39.Add( self.m_button42, 0, wx.ALL, 5 )
        
        self.m_button43 = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer39.Add( self.m_button43, 0, wx.ALL, 5 )
        
        
        vSizer.Add( bSizer39, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
        
        
        self.SetSizer( vSizer )
        self.Layout()
        
        self.Centre( wx.BOTH )
    
    def __del__( self ):
        pass
    

