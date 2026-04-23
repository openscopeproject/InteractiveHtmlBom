# AR Functionality Setup Guide

The InteractiveHtmlBom plugin's AR functionality uses MindAR for image tracking and requires users to provide .mind files for their PCB.

## System Requirements

### Browser and Network Requirements

- **Localhost Access Required**: AR functionality must be accessed via localhost (e.g., `http://localhost:8080/bom.html` or `http://127.0.0.1:8080/bom.html`) or HTTPS. The `file://` protocol cannot access camera.
- **Internet Connection Required**: AR functionality requires downloading external JavaScript libraries (A-Frame and MindAR) from CDN. Ensure stable internet connection during first load.
- **Modern Browser**: Supports WebRTC and camera access (Chrome 67+, Firefox 63+, Safari 11+, Edge 79+)
- **Camera Permission**: Browser must have permission to access device camera for AR tracking

### Hardware Requirements

- **Device Camera**: Built-in or external camera capable of capturing video
- **Adequate Lighting**: Good lighting conditions for optimal AR tracking performance
- **Stable Surface**: Recommended to place PCB on stable, non-reflective surface during AR use

## What are .mind files

.mind files are image tracking target files used by MindAR, containing feature point information for AR tracking. You need to create separate .mind files for the front and back sides of your PCB.

## Creating .mind files

### Step 1: Capture PCB Images from KiCad 3D Viewer

**IMPORTANT: You must use KiCad 3D Viewer, following these steps:**

1. **Open KiCad 3D Viewer**:
   - In PCB Editor, click `View` → `3D Viewer`

2. **Set Orthographic Projection Mode**:
   - In 3D Viewer, click `View` → `Projection` → `Orthographic`
   - **CRITICAL: Must disable perspective mode, use orthographic projection**

3. **Capture Front Image**:
   - Click `View` → `Preset Views` → `Top`
   - Use mouse wheel to zoom, ensure PCB fills the entire view
   - **IMPORTANT: Image edges must be tight against PCB, no extra white space**
   - Take screenshot and save as `pcb_front.png`

4. **Capture Back Image**:
   - Click `View` → `Preset Views` → `Bottom`
   - Use mouse wheel to zoom, ensure PCB fills the entire view
   - **IMPORTANT: Image edges must be tight against PCB, no extra white space**
   - Take screenshot and save as `pcb_back.png`

### Step 2: Use MindAR Online Tool

1. Visit [MindAR Image Target Creator](https://hiukim.github.io/mind-ar-js-doc/tools/compile)
2. Upload `pcb_front.png`
3. Click "Compile" to generate .mind file
4. Download the generated .mind file, rename to `pcb_front.mind`
5. Repeat steps 2-4, upload `pcb_back.png` to create `pcb_back.mind`

### Method 2: Using MindAR CLI Tool

If you have Node.js environment, you can use command line tools:

```bash
# Install MindAR CLI
npm install -g @hiukim/mind-ar-js-cli

# Create .mind file for PCB front
mind-ar-js-cli compile --input pcb_front.png --output pcb_front.mind

# Create .mind file for PCB back
mind-ar-js-cli compile --input pcb_back.png --output pcb_back.mind
```

## Configure AR in Plugin

1. Open PCB file in KiCad
2. Run InteractiveHtmlBom plugin
3. In settings dialog:
   - Check "Enable AR functionality"
   - Select "Front PCB Mind File": choose your front .mind file
   - Select "Back PCB Mind File": choose your back .mind file
4. Generate BOM

## AR Functionality Features

### Real-time PCB Overlay

- **Live Camera Feed**: View your physical PCB through device camera
- **Digital Overlay**: Interactive BOM components overlaid on physical PCB in real-time
- **Component Highlighting**: Click on physical components to highlight in BOM table and vice versa
- **Layer Switching**: Toggle between front and back PCB views while maintaining AR tracking

### AR Controls and Interface

- **AR Status Indicator**: Shows current AR tracking status (Searching, Tracking, Lost)
- **Opacity Control**: Adjust transparency of digital overlay (0-100%) for better visibility
- **Manual Lock Feature**: Lock AR position to prevent tracking drift during extended use
- **Layer Toggle**: Switch between front (F) and back (B) PCB layers in AR view

### Manual Lock Functionality

The manual lock feature helps maintain stable AR positioning:

1. **Auto-tracking Mode** (Default): AR system continuously tracks PCB position
   - Adapts to PCB movement and camera angle changes
   - May occasionally experience tracking drift or jitter

2. **Manual Lock Mode**: Freeze AR overlay at current position
   - Click the lock button (🔓) in AR interface to enable lock mode
   - AR overlay becomes fixed relative to camera view
   - Useful for detailed component inspection without tracking interference
   - Click lock button again (🔒) to return to auto-tracking mode

**When to Use Manual Lock:**
- During detailed component examination
- When experiencing tracking instability
- For precise component identification tasks
- When PCB is in optimal tracking position

## Network and Security Considerations

### Internet Connectivity Requirements

AR functionality requires internet access for:

- **External Libraries**: Downloads A-Frame (WebXR framework) and MindAR libraries from CDN
- **First Load**: Initial library download (~2-3MB total)
- **Offline Use**: After first successful load, libraries are cached for offline use
- **CDN Dependencies**:
  - A-Frame: `https://aframe.io/releases/1.5.0/aframe.min.js`
  - MindAR: `https://cdn.jsdelivr.net/npm/mind-ar@1.2.5/dist/mindar-image-aframe.prod.js`

### Localhost and Protocol Requirements

- **Required**: Must use localhost server (http://localhost or http://127.0.0.1) or HTTPS
- **File Protocol**: Direct file:// access **NOT SUPPORTED** - cannot access camera
- **Remote Hosting**: Requires HTTPS for camera access
- **Security Context**: Camera access requires secure context (HTTPS or localhost only)

### Privacy and Security

- **Local Processing**: All AR processing happens locally in browser
- **No Data Upload**: PCB images and .mind files remain on your device
- **Camera Access**: Only used for AR tracking, no recording or transmission
- **Network Traffic**: Only for downloading required JavaScript libraries

## PCB Image Requirements

**Must use KiCad 3D Viewer screenshots, not physical photos!**

For optimal AR tracking performance, your PCB images must meet:

- **Use KiCad 3D Viewer**: Must be screenshots from 3D Viewer, not physical photos
- **Orthographic Projection**: Must disable perspective mode, use orthographic projection
- **Standard Views**: Use Top view (front) and Bottom view (back)
- **Tight Cropping**: Image edges must be tight against PCB, no extra white space
- **High Resolution**: Recommend at least 1200x800 pixels
- **Clear Features**: Include components, silkscreen, traces and other identifiable features

## Troubleshooting

### Issue 1: Unstable AR Tracking

- Check if .mind files are correctly generated
- Ensure PCB image quality is good
- Try using under different lighting conditions

### Issue 2: Cannot Start AR Mode

- **Check Internet Connection**: Ensure stable internet for downloading AR libraries
- **Verify Localhost Access**: Use localhost or HTTPS, file:// protocol NOT supported
- **Browser Compatibility**: Ensure browser supports WebRTC (camera access)
- **Camera Permissions**: Grant camera access when prompted by browser
- **Check .mind Files**: Verify .mind files are correctly selected and valid
- **Console Errors**: Check browser console (F12) for error messages
- **HTTPS/Security**: Ensure secure context for camera access

### Issue 3: .mind File Generation Failed

- Ensure using KiCad 3D Viewer screenshots, not physical photos
- Ensure perspective mode is disabled, using orthographic projection
- Ensure image edges are tight against PCB, no extra white space
- Ensure input image format is correct (PNG/JPG)
- Image should contain sufficient feature points
- Try adjusting image contrast and clarity

### Issue 4: Common Problems with 3D Viewer Screenshots

- **Perspective mode not disabled**: Must use orthographic projection, not perspective
- **Incorrect view**: Must use Top and Bottom views, not angled views
- **Improper zoom**: PCB should fill entire view, edges tight against image boundaries
- **Low resolution**: Recommend maximizing 3D Viewer window for high-resolution screenshots

### Issue 5: Network and Connectivity Problems

**AR Libraries Not Loading:**
- Check internet connection stability
- Verify CDN accessibility (aframe.io and cdn.jsdelivr.net)
- Try refreshing page to retry library download
- Check browser console for network errors

**Camera Access Denied:**
- Ensure using localhost (127.0.0.1) or HTTPS protocol
- Grant camera permissions when browser prompts
- Check browser settings for camera access permissions
- Try different browser if issues persist

**Performance Issues:**
- Close unnecessary browser tabs to free memory
- Ensure adequate lighting for camera
- Use wired internet connection for stability
- Clear browser cache if experiencing loading issues

### Issue 6: AR Tracking and Lock Problems

**Tracking Instability:**
- Use manual lock feature during detailed inspection
- Ensure adequate lighting and contrast
- Place PCB on non-reflective, stable surface
- Avoid rapid camera movements

**Manual Lock Not Working:**
- Ensure AR tracking is active before locking
- Click lock button when PCB is in optimal position
- Unlock and re-lock if position drifts
- Check that lock button is visible in AR interface

## Getting Help

If you still encounter problems:

1. **Check System Requirements**: Verify browser compatibility and internet connection
2. **Test Basic Functionality**: Ensure camera access and localhost setup work correctly
3. **Review Console Logs**: Check browser console (F12) for error messages
4. **Verify KiCad Version**: Recommend KiCad 7.0+ for best compatibility
5. **Check Plugin Logs**: Review plugin log output for configuration issues
6. **Submit GitHub Issue**: Report problems on project GitHub page with:
   - Operating system and version
   - Browser type and version
   - KiCad version
   - Network setup (localhost/file protocol)
   - Console error messages
   - Steps to reproduce the issue

## Quick Start Checklist

Before using AR functionality, ensure:

- [ ] Internet connection available for library download
- [ ] Using localhost (127.0.0.1) or HTTPS protocol access (NOT file://)
- [ ] Browser supports camera access (Chrome/Firefox/Safari/Edge)
- [ ] Camera permissions granted
- [ ] .mind files created from KiCad 3D Viewer screenshots
- [ ] AR functionality enabled in plugin settings
- [ ] Both front and back .mind files selected
- [ ] Good lighting conditions for AR tracking
