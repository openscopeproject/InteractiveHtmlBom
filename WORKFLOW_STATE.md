# Workflow State

## Request
Add support for deep-linking to PCB nets via URL query parameters. When a URL parameter like `net=VCC` is present, the viewer should automatically locate the referenced net, select/highlight all associated PCB elements, zoom and center the view so the highlighted net is clearly visible, while preserving existing behavior when no parameter is provided.

## Clarified Scope
- Add support for URL query parameter `net=<netname>` to deep-link to PCB nets
- Automatically locate referenced net and highlight associated elements  
- Automatically zoom and center the view to show the highlighted net
- Reuse existing net selection, highlighting, filtering, and zooming functionality
- Preserve all existing behavior when no parameter is provided

## Open Questions
1. Should I support both `net` and `ref/component` parameters simultaneously? (Answered: Yes, both are supported)
2. Does the existing `netClicked(net)` function provide the desired zoom/center behavior? (Answered: Yes, it uses existing highlight handlers)

## Constraints
- Minimal, additive implementation
- Avoid refactoring unrelated code  
- Reuse existing functionality wherever possible
- Changes should be non-invasive

## Plan
Modify the `window.onload` function in ibom.js to parse URL query parameters for a `net` parameter. When found, call the existing `netClicked(net)` function which will:
1. Locate the referenced net
2. Select/highlight all associated PCB elements using existing highlighting mechanism  
3. Zoom and center view to show highlighted net (already implemented in netClicked)

## Files To Change
- C:\Users\dani0\Documents\Programok\InteractiveHtmlBom\InteractiveHtmlBom\web\ibom.js - Added net parameter parsing and handling in window.onload function

## Implementation Notes
- Added 4 lines of code to parse net parameter and call existing netClicked function
- Leverages existing `netsToHandler` map that's already populated during BOM table population  
- Reuses existing `netClicked()` function which handles highlighting and zooming behavior
- Maintains backward compatibility with existing ref/component parameter support

## Current Status
Implementation complete. The feature supports deep-linking to nets via URL query parameters like `viewer.html?net=VCC`.

## Next Agent
linter

## Lint Results
-

## Commit Message Draft
-