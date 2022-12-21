axlCmdRegister( "ibom" `ibom )

procedure( addMetadata( ibomVersion @optional ( rev "" ) ( company "" ) )
    let( ( metadata )    

        when( rev == ""
            rev = axlUIPrompt( "Enter Revision:" )            
        )

        when( company == ""
            company =  axlUIPrompt( "Enter company name:" )                    
        )
        
        ibomVersion = strcat( "\"" ibomVersion "\"" )
        rev = strcat( "\"" rev "\"" )
        company = strcat( "\"" company "\"" )

        dsnName = strcat( "\"" upperCase( axlCurrentDesign() ) "\"" )
        
        currentTime = timeToTm( stringToTime( getCurrentTime() ) )
        day = sprintf( nil "%d" currentTime->tm_mday )
        month = sprintf( nil "%d" currentTime->tm_mon + 1 ) 
        year = sprintf( nil "%d" currentTime->tm_year - 100 )
        currentDate = strcat( "\"" day "." month "." year "\"" )

        metadata = strcat(
            "\"ibom_version\": "
            ibomVersion
            ", \"metadata\": { \"title\": "
            dsnName
            ", \"revision\": "
            rev
            ", \"company\": "
            company
            ", \"date\": "
            currentDate 
            " }"
        )
    )
)

procedure( writeConfig( outFile )
    let( ( outPort config result )       

        outPort = outfile( outFile )

        if( outPort != nil then        
            config = strcat( 
                "var config = { " 
                "\"dark_mode\": " 
                "false"
                ", \"show_pads\": " 
                "true"
                ", \"show_fabrication\": " 
                "true"
                ", \"show_silkscreen\": "
                "false"
                ", \"highlight_pin1\": "
                "true"
                ", \"redraw_on_drag\": "
                "true"
                ", \"board_rotation\": "
                sprintf( nil "%f" 0.0 )                 
                ", \"checkboxes\": "
                "\"\""
                ", \"bom_view\": "
                "\"left-right\""
                ", \"layer_view\": "
                "\"FB\""                
                ", \"fields\": "
                "[\"Value\", \"Footprint\"]"   
                "}"             
            )

            fprintf( outPort config )
            close( outPort )

            result = t
        else
            ; error    
            error( "Can not write to file ..." )        
            result = nil
        )
        result
    )
)

; ### segment

; ```js
; {
;   "type": "segment",
;   "start": [x, y],
;   "end": [x, y],
;   "width": width,
; }
; ```

procedure( addLine( segment @optional ( width 0.1 ) )
    let( ( extents xStart yStart xEnd yEnd element )    
        extents = segment->startEnd

        xStart = caar( extents )
        yStart = -cadar( extents ) ; multiply by -1, s. ibom y convention
        
        xEnd = caadr( extents )        
        yEnd = -cadadr( extents ) ; multiply by -1, s. ibom y convention

        element = strcat( 
            "{ \"type\": \"segment\", \"start\": [" 
            sprintf( nil "%f" xStart ) 
            ", " 
            sprintf( nil "%f" yStart ) 
            "], \"end\": [" 
            sprintf( nil "%f" xEnd ) 
            ", " 
            sprintf( nil "%f" yEnd ) 
            "], \"width\": " 
            sprintf( nil "%f" width ) 
            " }" 
        )
    )
)

; ### circle

; ```js
; {
;   "type": "circle",
;   "start": [x, y],
;   "radius": radius,
;   // Optional boolean, defaults to 0
;   "filled": 0,
;   // Line width (only has effect for non-filled shapes)
;   "width": width,
; }
; ```

procedure( addCircle( segment @optional ( width 0.1 ) )
    let( ( xy xStart yStart radius element )
        xy = segment->xy
        xStart = car( xy )
        yStart = -cadr( xy ) 
        radius = segment->radius       

        element = strcat( 
            "{ \"type\": \"circle\", \"start\": [" 
            sprintf( nil "%f" xStart ) 
            ", " 
            sprintf( nil "%f" yStart ) 
            "], \"radius\": " 
            sprintf( nil "%f" radius ) 
            ", \"width\": " 
            sprintf( nil "%f" width ) 
            " }" 
        )
    )
)

; ### arc

; ```js
; {
;   "type": "arc",
;   "width": width,
;   // SVG path of the arc given as 'd' attribute of svg spec.
;   // If this parameter is specified everything below it is ignored.
;   "svgpath": svgpath,
;   "start": [x, y], // arc center
;   "radius": radius,
;   "startangle": angle1,
;   "endangle": angle2,
; }
; ```

procedure( addArc( segment @optional ( width 0.1 ) )
    let( ( xy xCenter yCenter radius extents xStart yStart xEnd yEnd cw angle1 angle2 startAngle endAngle element )
        xy = segment->xy
        xCenter = car( xy )
        yCenter = -cadr( xy )
        
        radius = segment->radius

        extents = segment->startEnd        

        xStart = caar( extents )
        yStart = -cadar( extents ) ; multiply by -1, s. ibom y convention
        
        xEnd = caadr( extents )        
        yEnd = -cadadr( extents ) ; multiply by -1, s. ibom y convention

        cw = segment->isClockwise
        
        ;width = 0.1 ;segment->width
        
        angle1 =  axlRadToDeg( atan2( ( yStart - yCenter ), ( xStart - xCenter ) ) )   

        ; convert to positive angle
        when( negativep( angle1 )
            angle1 = angle1 + 360
        )
        
        angle2 = axlRadToDeg( atan2( ( yEnd - yCenter ), ( xEnd - xCenter ) ) )

        ; convert to positive angle
        when( negativep( angle2 )
            angle2 = angle2 + 360    
        )
        
        ; map the correct angles
        if( ( angle2 - angle1 ) > 0 then
            if( cw then
                startAngle = angle1
                endAngle = angle2        
            else
                startAngle = angle2
                endAngle = angle1
            )

            ; if arc is a circle, but not marked as a circle ...
            when( startAngle == endAngle
                endAngle = endAngle + 360.0
            )
        else
            if( cw then
                startAngle = angle1
                endAngle = angle2        
            else
                startAngle = angle2
                endAngle = angle1
            )
            
            ; if arc is a circle, but not marked as a circle ...
            when( startAngle == endAngle
                startAngle = startAngle + 360.0
            )
        )

        element = strcat( 
            "{ \"type\": \"arc\", \"width\": " 
            sprintf( nil "%f" width ) 
            ", \"start\": [" 
            sprintf( nil "%f" xCenter ) 
            ", " 
            sprintf( nil "%f" yCenter ) 
            "], \"radius\": " 
            sprintf( nil "%f" radius ) 
            ", \"startangle\": " 
            sprintf( nil "%f" startAngle ) 
            ", \"endangle\": " 
            sprintf( nil "%f" endAngle ) 
            " }" 
        )
    )
)

procedure( addText( object @optional ( textType t ) )
    let( ( xy x y angle attr alignment justify textBlock height width thickness text element )
        xy = object->xy
        x = xCoord( xy )
        y = -yCoord( xy )

        ; get rotation
        angle = object->rotation

        ; check, if text is mirrored
        if( object->isMirrored then
            attr = "\"mirrored\""
        else
            attr = ""
        )

        ; get text alignment
        alignment = object->justify

        case( alignment
            (
                "LEFT"
                justify = "[-1, 1]"
            )
            (
                "RIGHT"
                justify = "[1, 1]"
            )
            (
                "CENTER"
                justify = "[0, 1]"
            )
            (
                t    
                justify = "[0, 1]"
            )            
        )

        case( textType
            (
                "refdes"
                type = ", \"ref\": 1"
            )
            (
                "value"
                type = ", \"val\": 1"
            )
            (
                t
                type = ""
            )
        )
        
        ; get text parameters
        textBlock = axlGetParam( strcat( "paramTextBlock:" object->textBlock ) )
        height = textBlock->height
        width = textBlock->width
        thickness = textBlock->photoWidth

        ; remove characters, that are not in font data
        pattern = pcreCompile("[\\\\\"\\'\\%]")
        text = pcreReplace( pattern object->text " " 0 )
 
        element = strcat(
            "{ \"pos\": ["
            sprintf( nil "%f" x )
            ", "
            sprintf( nil "%f" y )
            "], \"text\": \""
            text
            "\", \"height\":  "
            sprintf( nil "%f" height )
            ", \"width\": "
            sprintf( nil "%f" width )
            ", \"justify\": "
            justify
            ", \"thickness\": "
            sprintf( nil "%f" thickness )
            ", \"attr\": ["
            attr
            "], \"angle\": "
            sprintf( nil "%f" angle )
            type
            "}"
        ) 
    )
)

procedure( parseSegment( segment )
    let( ( element )
        case( segment->objType
            (
                "line"
                element = addLine( segment )        
            )
            (
                "arc"
                if( segment->isCirle then
                    element = addCircle( segment )
                else
                    element = addArc( segment )
                )
            )
            (
                t
                warn( "Unknown segment ...\n")
            )        
        )    
        element
    )    
)

procedure( addBoardGeometry( @optional ( expand list( '( 0.0 0.0) '( 0.0 0.0 ) ) ) )
    let( ( ( edges 'unbound ) dsn outline segments extents xStart yStart xEnd yEnd bBox element boardGeometry )

        dsn = axlDBGetDesign()
        outline = dsn->designOutline
        segments = outline->segments
        
        extents =  axlDBGetExtents( segments nil )

        xStart = caar( extents ) - caar( expand )
        yStart = -cadar( extents ) + cadar( expand ) ;multiply by -1, s. ibom y convention
        
        xEnd = caadr( extents ) + caadr( expand )        
        yEnd = -cadadr( extents ) - cadadr( expand ) ; multiply by -1, s. ibom y convention

        bBox = strcat( 
            "\"edges_bbox\": { \"minx\": " 
            sprintf(nil "%f" xStart ) 
            ", \"miny\": " 
            sprintf( nil "%f" yStart ) 
            ", \"maxx\": " 
            sprintf(nil "%f" xEnd ) 
            ", \"maxy\": " 
            sprintf( nil "%f" yEnd ) 
            "}" 
        )

        foreach( segment segments
            ; parse segment
            element = parseSegment( segment )  
    
            if( boundp( 'edges ) then
                tconc( edges element )
            else
                edges = tconc( nil element )
            )      
        )

        ; add cutout to edges list
        cutout = car( axlDBGetShapes( "BOARD GEOMETRY/CUTOUT" ) )
        segments = cutout->segments

        foreach( segment segments
            ; parse segment
            element = parseSegment( segment )  
    
            if( boundp( 'edges ) then
                tconc( edges element )
            else
                edges = tconc( nil element )
            )      
        )
    
        boardGeometry = strcat( bBox ", \"edges\": [" buildString( car( edges ) ", " ) "]" )   
    )
)

; rotate a vector around 0:0
procedure( rotateVector( point angle )
    let( ( angleRad x y xy )  
        angleRad = axlDegToRad( angle )
        x = car( point ) * cos( angleRad ) - cadr( point ) * sin( angleRad )
        y = car( point ) * sin( angleRad ) + cadr( point ) * cos( angleRad )
        ; return xy
        xy = list( x y )
    )
)

; rotation is the rotation of the symbol, it gets negated in the function
procedure( getBboxSize( segments xOffset yOffset rotation ) 
    let( (  ( xDim 'unbound )
            ( yDim 'unbound )
            points radius xy x y xMin xMax yMin yMax xSize ySize )
        
        foreach( segment segments     
            radius = segment->radius

            if( radius then
                points = segment->bBox
            else
                points = segment->startEnd            
            )
            
            foreach( point points            
                ; transform each point of the segment
                x = car( point ) - xOffset
                y = cadr( point ) * -1 - yOffset
                
                ; because of the negative y-axis it needs to be turned with rotation to make it undone
                xy = rotateVector( list( x y ) rotation )
                
                if( boundp( 'xDim ) then
                    tconc( xDim car( xy ) )
                else
                    xDim = tconc( nil car( xy ) )
                ) 
            
                if( boundp( 'yDim ) then
                    tconc( yDim cadr( xy ) )
                else
                    yDim = tconc( nil cadr( xy ) )
                )
            )
        )

        xDim = car( xDim )
        yDim = car( yDim )

        ; calculate min and max values for the x-dimension
        xMin = car( sort( copy( xDim ) 'lessp ) ) 
        xMax = car( sort( copy( xDim ) 'greaterp ) ) 

        ; calculate min and max values for the y-dimension
        yMin = car( sort( copy( yDim ) 'lessp ) )
        yMax = car( sort( copy( yDim ) 'greaterp ) )   

        xSize = xMax - xMin
        ySize = yMax - yMin

        dxCenter = xMin + xSize / 2
        ; yMax is the lowest point ... since y-axis is inverted
        dyCenter = yMax - ySize / 2

        sizeCenter = list( list( xSize ySize ) list( dxCenter dyCenter ) )
    )
)

procedure( addArcPoints( xOffset yOffset startAngle endAngle radius clockWise nbPoints )
    let( ( ( points 'unbound ) dPhi angle point )

        if( clockWise then       
            ; dPhi must be negative     
            when( startAngle < endAngle
                startAngle = startAngle + 360.0
            )
            dPhi = ( endAngle - startAngle ) / ( nbPoints - 1 ) 
        else
            ; dPhi must be positive
            when( endAngle < startAngle 
                endAngle = endAngle + 360.0
            )
            dPhi = ( endAngle - startAngle ) / ( nbPoints - 1 )   
        )              

        for( i 0 ( nbPoints - 1 )
            angle = axlDegToRad( startAngle + i * dPhi )
            point = strcat(                
                "["
                sprintf( nil "%f" ( xOffset + radius * cos( angle ) ) ) 
                ", "
                
                sprintf( nil "%f" ( yOffset - radius * sin( angle ) ) )
                "]"
            )

            if( boundp( 'points ) then
                tconc( points point )
            else
                points = tconc( nil point )
            ) 
        )
        points = car( points )
    )
)

procedure( addPoly( figure xOffset yOffset rotation )
    let( (  ( nbArcPoints 20 ) ( points 'unbound ) segments xy x y arcCenter xArcCenter yArcCenter loopIteration prevSegment prevEndpoint dx dy radius startAngle endAngle clockWise arcPointspoint )
    
        segments = axlPathGetPathSegs( car( figure ) )
        
        foreach( segment segments          

            xy = segment->_endPoint
            x = car( xy ) - xOffset
            y = cadr( xy ) * - 1 - yOffset

            xy = rotateVector( list( x y ) rotation ) 
            x = car( xy )
            y = cadr( xy )
          
            if( segment->_arcCenter then               

                arcCenter = segment->_arcCenter
                xArcCenter = car( arcCenter ) - xOffset
                yArcCenter = cadr( arcCenter ) * -1 - yOffset

                ; perform vector rotation
                arcCenter = rotateVector( list( xArcCenter yArcCenter ) rotation )
                xArcCenter = car( arcCenter )
                yArcCenter = cadr( arcCenter )

                loopIteration = lindex( segments segment )

                if( loopIteration == 1 then
                    prevSegment = nthelem( length( segments ) segments )                    
                else 
                    prevSegment = nthelem( sub1( loopIteration ) segments )  
                )

                prevEndpoint = prevSegment->_endPoint

                xPrevEndpoint = car( prevEndpoint ) - xOffset
                yPrevEndpoint = cadr( prevEndpoint ) * -1 - yOffset
                
                ; because the y-axis is inverted, the vector needs to be rotated in direction of the rotation to make rotation undone
                prevEndpoint = rotateVector( list( xPrevEndpoint yPrevEndpoint ) rotation )
                
                dx = car( prevEndpoint ) - xArcCenter
                ; because y-axis is inverted
                dy = ( cadr( prevEndpoint ) - yArcCenter ) * - 1 
                
                radius = sqrt( expt( dx 2 ) + expt( dy 2 ) )

                startAngle = axlRadToDeg( atan2( dy dx ) )
                ;print( startAngle)

                when( negativep( startAngle )
                    startAngle = startAngle + 360    
                )

                dx = car( xy ) - xArcCenter
                ; because y-axis is inverted
                dy = ( cadr( xy ) - yArcCenter ) * - 1
                
                endAngle = axlRadToDeg( atan2( dy dx ) )

                when( negativep( endAngle )
                    endAngle = endAngle + 360    
                )
                
                clockWise = segment->_arcClockwise            
                
                ; make arc points, set to 20 points
                arcPoints = addArcPoints( xArcCenter yArcCenter startAngle endAngle radius clockWise nbArcPoints )   
                
                if( boundp( 'points ) then
                    foreach( entry arcPoints
                        tconc( points entry )
                    )          
                else                
                    points = tconc( nil car( arcPoints ))
                    foreach( entry cdr( arcPoints )
                        tconc( points entry )
                    ) 
                )
            else                

                point = strcat(
                    "["
                    sprintf( nil "%f" x )
                    ", "
                    sprintf( nil "%f" y )
                    "]"
                )

                if( boundp( 'points ) then
                    tconc( points point )
                else
                    points = tconc( nil point )
                ) 
            ) 
            
        )        
        ;points = strcat( "\"polygons\": [[" buildString( car( points ) ", ") " ]]" )           
        points = buildString( car( points ) ", ")
    ) 
)

procedure( addPad( pin ) 
    let( (  ( padLayers 'unbound ) 
            ( drill 'unbound ) 
            ( pads 'unbound ) 
            xy xPos yPos pos angle pinOnes pinNumber 
            type padstack startEnd layers pad 
            drillShape drillSize bBox xSize ySize size poly shape )   

        ; get position
        xy = pin->xy
        xPos = car( xy )
        yPos = -cadr( xy )
        
        pos = strcat( 
            "[ " 
            sprintf( nil "%f" xPos ) 
            ", " 
            sprintf( nil "%f" yPos ) 
            "]" 
        )            
            
        ; get pin angle
        angle = sprintf( nil "%f" pin->rotation )

        ; default smd, overwritten later, if needed
        type = "\"smd\""
                
        ; mark pin 1
        pinOnes = list( "1" "A" "A1" )
        pinNumber = pin->number

        if( member( pinNumber pinOnes ) then
            pinNumber = "\"1\""
        else
            pinNumber = "\"\""
        )
       
        ; get padstack
        padstack = axlLoadPadstack( pin->name ) 
        startEnd = unique( padstack->startEnd )
        
        when( member( "ETCH/TOP" startEnd )             
            padLayers = tconc( nil "ETCH/TOP" )
        )

        when( member( "ETCH/BOTTOM" startEnd ) 
            if( boundp( 'padLayers ) then
                tconc( padLayers "ETCH/BOTTOM" )
            else
                padLayers = tconc( nil "ETCH/BOTTOM" )
            )        
        )

        ; check, if etch is defined
        if( boundp( 'padLayers ) then
            padLayers = car( padLayers )
        else
            ; let pad be defined on top, but size is set to zero later ( mechanical hole )
            padLayers = list( "ETCH/TOP" )          
        )       
        
        ; draw independent pad each layer, only append drilling to first pad
        foreach( padLayer padLayers 
            ; if pin is through all, define holes
            if( pin->isThrough && ( lindex( padLayers padLayer ) == 1 ) then
                type = "\"th\""

                if( padstack->usage == "Slot" then
                    drillShape = "oblong"
                    drillSize = strcat( 
                        "[ "
                        sprintf( nil "%f" padstack->drillSizeWidth )
                        ", "
                        sprintf( nil "%f" padstack->drillSizeHeight )
                        "]"
                    )                  
                else
                    drillShape = "circle"
                    drillSize = strcat( 
                        "[ "
                        sprintf( nil "%f" padstack->drillDiameter )
                        ", "
                        sprintf( nil "%f" 0.0 )
                        "]"
                    )             
                ) 

                drill = strcat(
                    "\"drillshape\": \""
                    drillShape
                    "\", \"drillsize\": "
                    drillSize
                    ", \"offset\": ["
                    sprintf( nil "%f" car( padstack->drillOffset ) )
                    ", "
                    sprintf( nil "%f" cadr( padstack->drillOffset ) )
                    "]"
                )            
            else
                type = "\"smd\""                
            )

            if( pin->isMirrored == nil then
                if( padLayer == "ETCH/TOP" then
                    layers = "[\"F\"]"
                    pad = axlDBGetPad( pin, "ETCH/TOP", "REGULAR" ) 
                else
                    layers = "[\"B\"]"
                    pad = axlDBGetPad( pin, "ETCH/BOTTOM", "REGULAR" )  
                )
            else
                if( padLayer == "ETCH/TOP" then
                    layers = "[\"B\"]"
                    pad = axlDBGetPad( pin, "ETCH/BOTTOM", "REGULAR" ) 
                else
                    layers = "[\"F\"]"
                    pad = axlDBGetPad( pin, "ETCH/TOP", "REGULAR" )  
                )                
            )

            ; get pad size
            bBox = pad->bBox               
            xSize = caadr( bBox ) - caar( bBox )
            ySize = cadadr( bBox ) - cadar( bBox )
            
            size = strcat(
                "[ "
                sprintf( nil "%f" xSize )
                ", "
                sprintf( nil "%f" ySize )
                "]"
            )

            case( pad->figureName
                (
                    "CIRCLE"
                    shape = "\"circle\""
                )
                (   
                    "OCTAGON"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                )                          
                ( 
                    "SQUARE"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    ) 
                ) 
                ( 
                    "RECTANGLE"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )             
                ) 
                ( 
                    "OBLONG_X"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                )
                (
                    "OBLONG_Y"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                )
                (
                    "SHAPE"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                ) 
                (
                    "FLASH" 
                    warn( "Flash pad is not supported ..." )              
    
                ) 
                ( 
                    "DONUT"
                    warn( "Donut pad is not supported ..." )  
                ) 
                ( 
                    "ROUNDED_RECTANGLE"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                )
                (
                    "CHAMFERED_RECTANGLE"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos pin->rotation )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                )
                (
                    "N_SIDED_POLY"
                    shape = "\"custom\""
    
                    when( pad->figure                     
                        poly = addPoly( pad->figure xPos yPos )
                        shape = strcat( 
                            shape
                            ", \"polygons\": [[" 
                            poly    
                            " ]]"                
                        )
                    )
                ) 
                (
                    "NULL"
                    ; pin is mechanical
                    shape = "\"circle\""
    
                    ; set size to zero
                    size = strcat(
                        "[ "
                        sprintf( nil "%f" 0.0 )
                        ", "
                        sprintf( nil "%f" 0.0 )
                        "]"
                    )
                )
                (
                    t
                    error( "Unknown pad shape ..." )
                )            
            )    
               
            ;build pad
            pad = strcat(
                "{ \"layers\": "
                layers
                ", \"pos\": "
                pos
                ", \"size\": "
                size
                ", \"angle\": "
                angle
                ", \"pin1\":"
                pinNumber
                ", \"shape\": "
                shape
                ", \"type\": "
                type
            )
    
            ; if present, add the drill information
            if( boundp( 'drill ) then
                ;build pad
                pad = strcat( pad ", " drill "}" )
            else
                pad = strcat( pad "}" )
            )

            ; if present, add the drill information
            if( boundp( 'pads ) then
                tconc( pads pad )
            else
                pads = tconc( nil pad )
            )

            ; unbind drill for next iteration
            drill = 'unbound
        )
        ; build pads string                
        pads = buildString( car( pads ) "," )       
    )
)

procedure( addFootprint( symbol )
    let( (  ( sizeCenterTop 'unbound )
            ( sizeCenterBottom 'unbound )
            ( sizeTop list( 0.0 0.0 ) )
            ( centerTop list( 0.0 0.0 ) )
            ( sizeBottom list( 0.0 0.0 ) )
            ( centerBottom list( 0.0 0.0 ) )
            ( size 'unbound ) 
            ( pads 'unbound ) 
            ( sizeCenter 'unbound ) 
            ( bBox list( '(0.0 0.0) '(0.0 0.0) ) )
            xy x y xPos yPos angle bBox xSize ySize footprint ) 
        ; get reference designator
        refdes = symbol->refdes

        ; get symbol layer
        if( symbol->layer == "TOP" then
            layer = "\"layer\": \"F\""
        else
            layer = "\"layer\": \"B\""
        )
        
        ; get symbol origin and rotation angle
        xy = symbol->xy
        angle = symbol->rotation

        ; get children of symbol
        children = symbol->children        

        ; loop through children
        foreach( child children          
            when( child->layer == "PACKAGE GEOMETRY/PLACE_BOUND_TOP" && child->objType == "shape"               
                segments = child->segments
                sizeCenterTop = getBboxSize( segments xCoord( xy ) -yCoord( xy ) angle )
                sizeTop = car( sizeCenter )  
                centerTop = cadr( sizeCenter )                              
            )            

            when( child->layer == "PACKAGE GEOMETRY/PLACE_BOUND_BOTTOM" && child->objType == "shape"
                segments = child->segments
                sizeCenterBottom = getBboxSize( segments xCoord( xy ) -yCoord( xy ) angle )
                sizeBottom = car( sizeCenter )  
                centerBottom = cadr( sizeCenter )
            )
        )

        ; if boundary is defined at both layer, combine both
        if( boundp( 'sizeCenterTop ) && boundp( 'sizeCenterBottom ) then
            ; check if there is a difference
            dxCenter = xCoord( centerBottom ) - xCoord( centerTop )
            dyCenter = yCoord( centerBottom ) - yCoord( centerTop )

            dxLeft = ( xCoord( centerBottom ) - xCoord( sizeBottom ) / 2 ) - ( xCoord( centerTop ) - xCoord( sizeTop ) / 2 ) 
            dxRight = ( xCoord( centerBottom ) + xCoord( sizeBottom ) / 2 ) - ( xCoord( centerTop ) + xCoord( sizeTop ) / 2 ) 
            dyBottom = ( yCoord( centerBottom ) - yCoord( sizeBottom ) / 2 ) - ( yCoord( centerTop ) - yCoord( sizeTop ) / 2 ) 
            dyTop = ( yCoord( centerBottom ) + yCoord( sizeBottom ) / 2 ) - ( yCoord( centerTop ) + yCoord( sizeTop ) / 2 ) 

            ; initial values
            xSize = xCoord( sizeTop )
            ySize = yCoord( sizeTop )

            xCenter = xCoord( centerTop )
            yCenter = yCoord( centerTop )
          
            unless( dxLeft > 0.0
                xSize = xSize + dxLeft
                xCenter = xCenter - dxLeft / 2              
            )

            unless( dxRight > 0.0
                xSize = xSize + dxRight
                xCenter = xCenter + dxRight / 2              
            )

            ; negative implies increasing y-size
            unless( dyBottom > 0.0
                ySize = ySize + dyBottom
                yCenter = yCenter + dyBottom / 2              
            )

            unless( dyTop > 0.0
                ySize = ySize + dyTop
                yCenter = yCenter - dyTop / 2              
            )    

            size = list( xSize ySize )
            center = list( xCenter yCenter )
            sizeCenter = list( size center )           
        else
            when( boundp( 'sizeCenterTop )
                size = sizeTop
                center = centerTop
                sizeCenter = list( size center )
            )

            when( boundp( 'sizeCenterBottom ) 
                size = sizeBottom
                center = centerBottom
                sizeCenter = list( size center )
            )        
        )
              
        if( boundp( 'sizeCenter ) then
            xSize = xCoord( size )
            ySize = yCoord( size )

            center = rotateVector( center -angle )
        
            xCenter = xCoord( center )
            yCenter = yCoord( center )
        else
            ; get extents of symbol, if boundary is not defined
            bBox = axlDBGetExtents( symbol nil )
            xSize = caadr( bBox ) - caar( bBox )
            ySize = cadadr( bBox ) - cadar( bBox )

            xCenter = 0.0
            yCenter = 0.0
        )
           
        ; center bBox around 0:0
        bBoxCenter = rotateVector( list( -xSize/2 -ySize/2 ) -angle )   

        ; shift x/y position ( center offset and rotated vector )
        xPos = xCoord( xy ) + xCoord( bBoxCenter ) + xCenter
        yPos = -yCoord( xy ) + yCoord( bBoxCenter ) + yCenter
        
        xRelPos = 0.0
        yRelPos = 0.0       
 
        general = strcat( 
            "\"ref\": \""
            refdes
            "\", \"bbox\": { \"pos\": ["
            sprintf( nil "%f" xPos )            
            ", "            
            sprintf( nil "%f" yPos )
            "], \"angle\": "
            sprintf( nil "%f" angle )
            ", \"relpos\": ["
            sprintf( nil "%f" xRelPos )
            ", "
            sprintf( nil "%f" yRelPos )            
            "], \"size\": ["
            sprintf( nil "%f" xSize )
            ", "
            sprintf( nil "%f" ySize )
            "]}"
        )

        ; get pins
        pins = symbol->pins

        ; add each pin
        foreach( pin pins
            pad = addPad( pin )

            if( boundp( 'pads ) then
                tconc( pads pad )
            else
                pads = tconc( nil pad )
            )                                         
        )       

        ; PAD DEFINITION        
        if( boundp( 'pads ) then
            pads = strcat( "\"pads\": [" buildString( car( pads ) ", " ) "]" ) 
        else        
            pads = "\"pads\": []"  
        )       
        
        ; DRAWINGS
        drawings = "\"drawings\": []"

        ; MERGE FOOTPRINT
        footprint = strcat( "{ " buildString( list( general pads drawings layer) ", " ) "}")
    )        
)

procedure( addSymbols()
    let( (  ( silkscreenTop 'unbound ) 
            ( silkscreenBottom 'unbound ) 
            ( fabricationTop 'unbound ) 
            ( fabricationBottom 'unbound ) 
            ( symbolsTop 'unbound ) 
            ( symbolsBottom 'unbound ) 
            ( symbolsBoth 'unbound ) 
            ( symbolsSkipped 'unbound ) 
            ( fields 'unbound ) 
            ( footprints 'unbound ) 
            symbols footprint id sym value package field children segments element fabrication drawings bom syms ) 

        ; get design
        dsn = axlDBGetDesign()

        ; get symbols
        symbols = dsn->symbols   
    
        ; loop through symbols
        foreach( symbol symbols
            ; fill bom
            ; if, symbol has a refdes
            ; make bom
            when( symbol->refdes
                ; create footprints
                footprint = addFootprint( symbol )
                ; append to field list            
                if( boundp( 'footprints ) then
                    tconc( footprints footprint )
                else
                    footprints = tconc( nil footprint )
                ) 
                
                ; footprint id
                id = sub1( length( car( footprints ) ) )
                ; create string, double bracing is for components of equal value    
                ; refdes, id ( corresponds to location in footprint list )        
                sym = strcat( "[[\"" symbol->refdes "\", " sprintf( nil "%d" id )  "]]" )

                value = cadr( assoc( 'VALUE, axlDBGetProperties( symbol->component->compdef ) ) )
                package = symbol->component->package
                field = strcat( 
                    "\"" 
                    sprintf( nil "%d" id ) 
                    "\": [\"" 
                    value 
                    "\", \"" 
                    package 
                    "\"]" 
                )

                ; append to field list            
                if( boundp( 'fields ) then
                    tconc( fields field )
                else
                    fields = tconc( nil field )
                ) 

                if( symbol->layer == "TOP" then             
                    if( boundp( 'symbolsTop ) then
                        tconc( symbolsTop sym )
                    else
                        symbolsTop = tconc( nil sym )

                    ) 
                    if( boundp( 'symbolsBoth ) then
                        tconc( symbolsBoth sym )
                    else
                        symbolsBoth = tconc( nil sym )

                    ) 
                ; if on BOTTOM
                else
                    if( boundp( 'symbolsBottom ) then
                        tconc( symbolsBottom sym )
                    else
                        symbolsBottom = tconc( nil sym )
                    )   
                    if( boundp( 'symbolsBoth ) then
                        tconc( symbolsBoth sym )
                    else
                        symbolsBoth = tconc( nil sym )

                    )           
                )
            )

            children = symbol->children

            ; loop through children of symbols
            foreach( child children
                case( child->layer 
                    (
                        "PACKAGE GEOMETRY/SILKSCREEN_TOP"  
                        if( ( child->objType == "path" ) || ( child->objType == "shape" ) then                      
                            segments = child->segments

                            ; loop though segments of each child
                            foreach( segment segments
                                element = parseSegment( segment )                   
                                if( boundp( 'silkscreenTop ) then
                                    tconc( silkscreenTop element )
                                else
                                    silkscreenTop = tconc( nil element )
                                )                  
                            )
                        else
                            when( child->objType == "text"
                                element = addText( child )
                                if( boundp( 'silkscreenTop ) then
                                    tconc( silkscreenTop element )
                                else
                                    silkscreenTop = tconc( nil element )
                                )                                 
                            )                        
                        ) 
                    )
                    (
                        "PACKAGE GEOMETRY/SILKSCREEN_BOTTOM"
                        if( ( child->objType == "path" ) || ( child->objType == "shape" ) then
                            segments = child->segments

                            ; loop though segments of each child
                            foreach( segment segments
                                element = parseSegment( segment )                   
                                if( boundp( 'silkscreenBottom ) then
                                    tconc( silkscreenBottom element )
                                else
                                    silkscreenBottom = tconc( nil element )
                                )                  
                            )
                        else
                            when( child->objType == "text"
                                element = addText( child )  
                                if( boundp( 'silkscreenBottom ) then
                                    tconc( silkscreenBottom element )
                                else
                                    silkscreenBottom = tconc( nil element )
                                )                                 
                            )                        
                        ) 
                    )
                    (
                        "REF DES/SILKSCREEN_TOP"
                        when( child->objType == "text"   
                            element = addText( child "refdes" )                   
                            if( boundp( 'silkscreennTop ) then
                                tconc( silkscreenTop element )
                            else
                                silkscreenTop = tconc( nil element )
                            )                 
                        )
                    )      
                    (
                        "REF DES/SILKSCREEN_BOTTOM"
                        when( child->objType == "text"   
                            element = addText( child "refdes" )                   
                            if( boundp( 'silkscreenBottom ) then
                                tconc( silkscreenBottom element )
                            else
                                silkscreenBottom = tconc( nil element )
                            )                 
                        )
                    )  
                    (
                        "COMPONENT VALUE/SILKSCREEN_TOP"
                        when( child->objType == "text"   
                            element = addText( child "value" )                   
                            if( boundp( 'silkscreenTop ) then
                                tconc( silkscreenTop element )
                            else
                                silkscreenTop = tconc( nil element )
                            )                 
                        )
                    )      
                    (
                        "COMPONENT VALUE/SILKSCREEN_BOTTOM"
                        when( child->objType == "text"   
                            element = addText( child "value" )                   
                            if( boundp( 'silkscreenBottom ) then
                                tconc( silkscreenBottom element )
                            else
                                silkscreenBottom = tconc( nil element )
                            )                 
                        )
                    )   
                    (
                        "PACKAGE GEOMETRY/ASSEMBLY_TOP"
                        if( ( child->objType == "path" ) || ( child->objType == "shape" ) then
                            segments = child->segments

                            ; loop though segments of each child
                            foreach( segment segments
                                element = parseSegment( segment )                   
                                if( boundp( 'fabricationTop ) then
                                    tconc( fabricationTop element )
                                else
                                    fabricationTop = tconc( nil element )
                                )                  
                            )    
                        else
                            when( child->objType == "text"
                                element = addText( child )  
                                if( boundp( 'fabricationTop ) then
                                    tconc( fabricationTop element )
                                else
                                    fabricationTop = tconc( nil element )
                                )                                 
                            )                        
                        )                                            
                    )
                    (
                        "PACKAGE GEOMETRY/ASSEMBLY_BOTTOM"                        
                        if( ( child->objType == "path" ) || ( child->objType == "shape" ) then
                            segments = child->segments

                            ; loop though segments of each child
                            foreach( segment segments
                                element = parseSegment( segment )                   
                                if( boundp( 'fabricationBottom ) then
                                    tconc( fabricationBottom element )
                                else
                                    fabricationBottom = tconc( nil element )
                                )                  
                            )
                        else
                            when( child->objType == "text"
                                element = addText( child ) 
                                if( boundp( 'fabricationBottom ) then
                                    tconc( fabricationBottom element )
                                else
                                    fabricationBottom = tconc( nil element )
                                )                                 
                            )                        
                        ) 
                    )        
                    (
                        "REF DES/ASSEMBLY_TOP"
                        when( child->objType == "text"   
                            element = addText( child "refdes" )                   
                            if( boundp( 'fabricationTop ) then
                                tconc( fabricationTop element )
                            else
                                fabricationTop = tconc( nil element )
                            )                 
                        )
                    )      
                    (
                        "REF DES/ASSEMBLY_BOTTOM"
                        when( child->objType == "text"   
                            element = addText( child "refdes" )                   
                            if( boundp( 'fabricationBottom ) then
                                tconc( fabricationBottom element )
                            else
                                fabricationBottom = tconc( nil element )
                            )                 
                        )
                    )    
                    (
                        "COMPONENT VALUE/ASSEMBLY_TOP"
                        when( child->objType == "text"   
                            element = addText( child "value" )  
                            if( boundp( 'fabricationTop ) then
                                tconc( fabricationTop element )
                            else
                                fabricationTop = tconc( nil element )
                            )                 
                        )
                    )      
                    (
                        "COMPONENT VALUE/ASSEMBLY_BOTTOM"
                        when( child->objType == "text"   
                            element = addText( child "value" )              
                            if( boundp( 'fabricationBottom ) then
                                tconc( fabricationBottom element )
                            else
                                fabricationBottom = tconc( nil element )
                            )                 
                        )
                    )   
                    ; OTHER LAYERS, WHICH HAVE TO BE CONSIDERED, CAN BE ADDED HERE
                    (
                        t
                        ; ignored
                    )
                )
            )        
        ) 

        ; TOP SILKSCREEN
        if( boundp( 'silkscreenTop ) then
            silkscreenTop = strcat( "\"F\": [" buildString( car( silkscreenTop ) ", " ) "]" )    
        else
            silkscreenTop = "\"F\": []"                    
        )

        ; BOTTOM SILKSCREEN
        if( boundp( 'silkscreenBottom )  then
            silkscreenBottom = strcat( "\"B\": [" buildString( car( silkscreenBottom ) ", " ) "]" ) 
        else
            silkscreenBottom = "\"B\": []"  
        )

        ; silkscren data in JSON format
        silkscreen = strcat( "\"silkscreen\": { " buildString( list( silkscreenTop silkscreenBottom ) ", " ) "}" )

        ; TOP ASSEMBLY
        if( boundp( 'fabricationTop ) then
            fabricationTop = strcat( "\"F\": [" buildString( car( fabricationTop ) ", " ) "]" )    
        else
            fabricationTop = "\"F\": []"                    
        )

        ; BOTTOM ASSEMBLY
        if( boundp( 'fabricationBottom )  then
            fabricationBottom = strcat( "\"B\": [" buildString( car( fabricationBottom ) ", " ) "]" ) 
        else
            fabricationBottom = "\"B\": []"  
        )
        
        ; fabrication data in JSON format
        fabrication = strcat( "\"fabrication\": { " buildString( list( fabricationTop fabricationBottom ) ", " ) "}" )
        
        ; combine silkscreen and fabrication layer in drawings
        drawings = strcat( "\"drawings\": {" buildString( list( silkscreen fabrication ) ", " ) "}" )

        ; FOOTPRINTS
        if( boundp( 'footprints ) then
            footprints = strcat( "\"footprints\": [" buildString( car( footprints ) ", " ) "]" )
        else
            footprints = "\"footprints\": []" 
        )

        ; SYMBOLS TOP LAYER
        if( boundp( 'symbolsTop ) then
            symbolsTop = strcat( "\"F\": [" buildString( car( symbolsTop ) ", " ) "]" )
        else
            symbolsTop = "\"F\": []"  
        )

        ; SYMBOLS BOTTOM LAYER
        if( boundp( 'symbolsBottom ) then
            symbolsBottom = strcat( "\"B\": [" buildString( car( symbolsBottom ) ", " ) "]" )
        else
            symbolsBottom = "\"B\": []"      
        )   

        ; SYMBOLS BOTH LAYERS
        if( boundp( 'symbolsBoth ) then
            symbolsBoth = strcat( "\"both\": [" buildString( car( symbolsBoth ) ", " ) "]" )
        else
            symbolsBoth = "\"both\": []"      
        ) 

        ; SYMBOLS SKIPPED
        if( boundp( 'symbolsSkipped ) then
            symbolsSkipped = strcat( "\"skipped\": [" buildString( car( symbolsSkipped ) ", " ) "]" )
        else
            symbolsSkipped = "\"skipped\": []"      
        ) 

        ; FIELDS
        if( boundp( 'fields ) then
            fields = strcat( "\"fields\": {" buildString( car( fields ) ", " ) "}" )
        else
            fields = "\"fields\": {}"
        ) 

        ; bom data in JSON format
        bom = strcat( "\"bom\": {" buildString( list( symbolsBoth symbolsTop symbolsBottom symbolsSkipped fields ) ", " ) "}" )

        syms = buildString( list(drawings footprints bom) ", " )
    )
)

procedure( addFontData( file )
    let( ( ( fontData "" ) inPort ) 
        if( isFile( file ) then
            inPort = infile( file )

            if( inPort then
                while( gets( line inPort )
                    fontData = strcat( fontData line )
                )            
            else
                warn( "No font data added ..." )
            )  
            close( inPort ) 
        else
            ; error    
            error( "Can not read from file ..." )                
        )
        fontData
    )                
)

procedure( writePcbData( templateFilePath outFile )
    let( ( outPort pcbData result )       

        outPort = outfile( outFile )
        fontDataFile = buildString( list( templateFilePath "font-data" "font_data" ) "/" )

        if( outPort != nil then        
            if( isFile( fontDataFile ) then
                pcbData = strcat( 
                    "var pcbdata = JSON.parse('{ " 
                    buildString( list(
                        addMetadata( "v2.4.1-2-gbbb5" )
                        addBoardGeometry( list( '( 10.0 10.0 ) '( 10.0 10.0 ) ) )
                        addSymbols()
                        addFontData( fontDataFile )                 
                        )             
                    ", " 
                    ) 
                    "}')" 
                )

                fprintf( outPort pcbData )
                close( outPort )

                result = t
            else
                ; error    
                error( "Font data is missing ... " )        
                result = nil
            ) 
        else
            ; error    
            error( "Can not write to file ... " )        
            result = nil
        )        
    )
)

procedure( importData( file outPort )
    ; inport, prc, line need to be local only
    let( ( inPort prc line )
        prc = pcreCompile( "%" ) 

        if( isFile( file ) then
            inPort = infile( file )

            while( gets( line inPort )
                ; prc is defined by ibom()
                line = pcreReplace( prc line "%%" 0 )                
                fprintf( outPort line )        
            )
            close( inPort )
        else
            warn( "%s not found ... skipped ..." file )
        )
    )
)

procedure( ibom() 
    let( (  workingDir projectName ibomDir templateDir userDir ibom htmlTemplate prc match sectionTable result inPort outPort line
            css cssPath 
            userCss userCssPath 
            splitJs splitJsPath 
            lzString lzStringPath
            pepJs pepJsPath
            configJs configJsPath
            utilJs utilJsPath
            renderJs renderJsPath
            tableUtilJs tableUtilJsPath
            ibomJs ibomJsPath
            userJs userJsPath
            userHeader userHeaderPath
            userFooter userFooterPath
            pcbData pcbDataPath        
        )        

        ; get working directory and project name
        workingDir = getWorkingDir()
        projectName = axlCurrentDesign()               
        ibomDir = buildString( list( workingDir "ibom" ) "/" )
        
        ; get ibom path
        ; path to ibom template files, defined in site.env otherwise templateDir must be set to the ibom/web path
        templateDir = axlGetVariableList("ibom")        
        ; path to user files
        userDir = buildString( list( templateDir "user-files" ) "/" )

        if( isDir( templateDir ) then
            ; create directory in project, if it is not existing
            unless( isDir( ibomDir )
                createDir( ibomDir );
            );	
            
            ibom = buildString( list( ibomDir strcat( projectName ".html" ) ) "/" )
            htmlTemplate = buildString( list( templateDir "ibom.html" ) "/" )   
            
            ; replace % by %%, since the fprintf routine expects a value
            prc = pcreCompile( "%" )    

            ; create matching expressions
            match = nil

            css = pcreCompile("///CSS///")
            cssPath = buildString( list( templateDir "ibom.css" ) "/" )

            userCss = pcreCompile("///USERCSS///")
            userCssPath = buildString( list( userDir "user.css" ) "/" )

            splitJs = pcreCompile("///SPLITJS///")
            splitJsPath = buildString( list( templateDir "split.js" ) "/" )

            lzString = pcreCompile("///LZ-STRING///")
            lzStringPath = buildString( list( templateDir "lz-string.js" ) "/" )

            pepJs = pcreCompile("///POINTER_EVENTS_POLYFILL///")
            pepJsPath = buildString( list( templateDir "pep.js" ) "/" )

            configJs = pcreCompile("///CONFIG///")
            configJsPath = buildString( list( workingDir "ibom" "config.tmp" ) "/" ) 

            utilJs = pcreCompile("///UTILJS///")
            utilJsPath = buildString( list( templateDir "util.js" ) "/" )

            renderJs = pcreCompile("///RENDERJS///")
            renderJsPath = buildString( list( templateDir "render.js" ) "/" )

            tableUtilJs = pcreCompile("///TABLEUTILJS///")
            tableUtilJsPath = buildString( list( templateDir "table-util.js" ) "/" )

            ibomJs = pcreCompile("///IBOMJS///")
            ibomJsPath = buildString( list( templateDir "ibom.js" ) "/" )

            userJs = pcreCompile("///USERJS///")
            userJsPath = buildString( list( userDir "user.js" ) "/" )

            userHeader = pcreCompile("///USERHEADER///")
            userHeaderPath = buildString( list( userDir "userheader.html" ) "/" )

            userFooter = pcreCompile("///USERFOOTER///")
            userFooterPath = buildString( list( userDir "userfooter.html" ) "/" )

            pcbData = pcreCompile("///PCBDATA///")
            pcbDataPath = buildString( list( workingDir "ibom" "pcbdata.tmp" ) "/" ) 

            ; build list
            sectionTable = list(
                list( css cssPath )
                list( userCss userCssPath )
                list( splitJs splitJsPath )
                list( lzString lzStringPath )
                list( pepJs pepJsPath )
                list( configJs configJsPath )
                list( utilJs utilJsPath )
                list( renderJs renderJsPath )
                list( tableUtilJs tableUtilJsPath )
                list( ibomJs ibomJsPath )
                list( userJs userJsPath )
                list( userHeader userHeaderPath )
                list( userFooter userFooterPath )
                list( pcbData pcbDataPath )
            )

            ; write config, optional ... can be commented, then only the data at the path is loaded
            result = writeConfig( configJsPath )

            when( result 
                ; write PcbData to file
                result = writePcbData( templateDir pcbDataPath )            
            )

            when( result 
                ; write to file
                inPort = infile( htmlTemplate )
                outPort = outfile( ibom ) 
                                
                if( inPort && outPort then
                    while( gets(line inPort)
                        line = pcreReplace(prc line "%%" 0)
                        
                        ; import file contents
                        foreach( section sectionTable
                            when( pcreMatchp( car( section ) line )
                                match = t
                                importData( cadr( section ) outPort )            
                            )            
                        )
                            
                        ; print content from htmlTemplate
                        unless( match == t
                            fprintf( outPort line )
                        )
                        match = nil    
                    )

                    ; close ports        
                    close( inPort )
                    close( outPort )
                else
                    ; error    
                    error( "Can not open file or write to file ..." )                                  
                )
            )

            when( isFile( configJsPath )      
                warn( "Deleting temporary configuraton file ..." )                   
                deleteFile( configJsPath )   
            )

            when( isFile( pcbDataPath )
                warn( "Deleting temporary pcbdata file ..." )
                deleteFile( pcbDataPath )       
            )
        else
            error( "Template path is not existing ..." )
        )
    )
)