# Photo UX and Upload Reliability Proposal

Status: Draft for implementation agents  
Date: 2026-06-03

## 1) Feature Description

Improve media reliability and viewing UX across the wedding app by fixing image orientation at upload time and upgrading preview behavior (sequential navigation, scroll lock, zoom, consistent dialog placement, and direct home navigation from the hamburger menu).

This proposal applies to:

- Uploaded media gallery preview in the menu page
- Table page media preview/lightbox
- List views where images appear (tables list, drawer list, gallery grid)

## 2) Confirmed Product Decisions

- Scope of preview improvements: both preview flows in the app
- Orientation fix scope: only new uploads
- Preview navigation: swipe + on-screen arrows
- Preview sequence content: all media (images and videos)
- Background scroll lock: robust standard lock; minor edge-device exceptions acceptable
- Zoom behavior: pinch-to-zoom + double-tap toggle
- Dialog placement target: consistent centered dialogs
- Hamburger home target: main menu/tables page
- Proposal path/name: default under docs

## 3) Functional Requirements

FR-1 Orientation Normalization on New Uploads  
All newly uploaded images must be stored in canonical orientation (EXIF orientation applied and then normalized/removed) so list and preview rendering appears correct without client-side rotation hacks.

FR-2 Correct Orientation in Lists  
Images displayed in list contexts must appear with correct orientation, including:

- Menu table cards
- Drawer table thumbnails
- Upload gallery grid thumbnails

FR-3 Unified Preview Sequence  
When opening preview, users can move to previous/next media without closing. Sequence includes images and videos.

FR-4 Gesture + Controls Navigation  
Preview supports swipe navigation and visible on-screen left/right controls.

FR-5 Background Scroll Lock During Preview  
While preview is open, page/background scroll must be disabled and restored after close.

FR-6 Improved Zoom for Images  
In preview image slides:

- Pinch gesture adjusts zoom
- Double-tap toggles zoom levels
- Pan is possible when zoomed
- Zoom state resets when changing slide

FR-7 Consistent Dialog Positioning  
Upload dialog appears centered in all breakpoints (no bottom-sheet variant).

FR-8 Home Entry in Hamburger Menu  
Drawer includes a clear entry to navigate to main menu/tables page.

FR-9 Mixed Media Preview Behavior  
Video slides remain playable with controls; image-only zoom gestures must not break video interaction.

## 4) Non-Functional Requirements

NFR-1 Mobile-first usability  
Touch interactions remain responsive on common mobile devices.

NFR-2 Predictable interaction model  
Gestures and controls behave consistently between table preview and gallery preview.

NFR-3 Performance  
No visible lag when opening preview and navigating between nearby items; avoid unnecessary full-page reflows.

NFR-4 Accessibility baseline  
Preview controls and dialogs remain keyboard reachable; escape/close behavior preserved.

NFR-5 Backward compatibility  
No migration required for existing uploads; only new uploads are normalized.

NFR-6 Failure containment  
If orientation metadata cannot be parsed, upload must still succeed with current fallback behavior.

## 5) Implementation Task List

### T1. Upload orientation normalization pipeline

Goal: Normalize orientation for newly uploaded images in API upload flow.

Actions:

- Apply EXIF transpose before resize/compression in image processing step
- Re-encode with normalized metadata (remove orientation ambiguity)
- Keep current size/compression logic

Done when:

- Newly uploaded portrait/landscape photos display correctly in list and preview views without CSS rotation fixes

Dependencies:

- None

### T2. Build unified preview data model (mixed media)

Goal: Provide one ordered media array (images + videos) to preview component(s).

Actions:

- Define preview item shape for image/video types
- Ensure both menu gallery and table page map items consistently

Done when:

- Preview opens at clicked item and can move through all media in order

Dependencies:

- T1 recommended but not required

### T3. Add swipe + arrow navigation in preview

Goal: Consistent previous/next navigation in both directions.

Actions:

- Keep swipe thresholds tuned for mobile
- Add visible previous/next buttons with clear hit areas
- Preserve close on backdrop/close-button behavior

Done when:

- User can traverse sequence without closing preview

Dependencies:

- T2

### T4. Enforce preview scroll lock lifecycle

Goal: Prevent accidental background scrolling while preview is open.

Actions:

- Lock document scroll on open, restore exact prior scroll on close
- Ensure nested open/close transitions do not leave page locked

Done when:

- No background movement on normal devices while preview is visible

Dependencies:

- T2

### T5. Implement pinch + double-tap zoom for image slides

Goal: Reliable, intuitive zoom controls.

Actions:

- Add double-tap toggle between base and zoomed level
- Maintain pinch scaling and bounded zoom range
- Enable pan only when zoom > 1
- Reset zoom/pan on slide change

Done when:

- Image zoom feels stable and does not interfere with media navigation

Dependencies:

- T2, T3

### T6. Mixed media interaction safeguards

Goal: Avoid gesture conflicts on video slides.

Actions:

- Disable image zoom handlers on video items
- Keep video controls usable while preserving preview navigation controls

Done when:

- Video playback controls are usable and navigation remains available

Dependencies:

- T2, T3, T5

### T7. Center dialog consistently

Goal: Remove bottom-sheet variance and keep upload dialog centered.

Actions:

- Replace breakpoint-conditional bottom alignment with always-centered layout
- Verify spacing on small screens and safe-area fit

Done when:

- Upload dialog appears centered on mobile and desktop

Dependencies:

- None

### T8. Add Home item in hamburger menu

Goal: Add direct path back to menu/tables page.

Actions:

- Insert Home entry near top of drawer navigation
- Route target: main menu/tables page

Done when:

- From any page, user can open drawer and return to tables in one tap

Dependencies:

- None

### T9. QA checklist and regression pass

Goal: Validate all behaviors end-to-end.

Actions:

- Orientation test set: portrait, landscape, rotated EXIF samples
- Preview flow test: images, videos, mixed sequence
- Scroll-lock test during preview open/close cycles
- Dialog position test at multiple breakpoints
- Drawer home navigation test

Done when:

- All FR and NFR above are validated in manual QA

Dependencies:

- T1 through T8

## 6) Execution Order Recommendation

1. T1
2. T2
3. T3 + T4
4. T5 + T6
5. T7 + T8
6. T9

## 7) Risks and Notes

- Existing uploads are intentionally not retrofixed; orientation inconsistencies may remain in old data.
- Mixed-media preview has higher gesture-conflict risk; interaction boundaries between swipe, zoom, and video controls must be explicit.
- Minor platform-specific scroll-lock edge cases are acceptable per current decision.
