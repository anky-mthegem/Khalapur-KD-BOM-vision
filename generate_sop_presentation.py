"""
Comprehensive SOP & Application User Manual Presentation Generator.
Generates an executive-ready 16:9 widescreen PowerPoint deck with embedded screenshots,
Standard Operating Procedures (SOP), and plant quality guidelines.
"""
import pathlib
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_sop_deck(output_path: pathlib.Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette: Industrial Office Ribbon Theme
    NAVY = RGBColor(43, 87, 154)         # #2B579A - MS Word Blue
    NAVY_DARK = RGBColor(30, 62, 109)    # #1E3E6D
    NAVY_LIGHT = RGBColor(237, 243, 252) # Soft blue tint
    GREEN = RGBColor(16, 124, 16)        # #107C10 - Quality Pass
    GREEN_LIGHT = RGBColor(223, 246, 221)
    RED = RGBColor(209, 52, 56)          # #D13438 - Discrepancy
    RED_LIGHT = RGBColor(253, 231, 233)
    AMBER = RGBColor(200, 130, 0)        # #C88200 - Warning
    AMBER_LIGHT = RGBColor(255, 244, 206)
    CYAN = RGBColor(0, 164, 228)         # #00A4E4 - Tripwire
    SLATE = RGBColor(96, 94, 92)         # #605E5C
    DARK = RGBColor(32, 31, 30)          # #201F1E
    WHITE = RGBColor(255, 255, 255)
    BG_GRAY = RGBColor(243, 242, 241)    # #F3F2F1
    BORDER_GRAY = RGBColor(210, 208, 206)# #D2D0CE

    screenshots_dir = pathlib.Path("docs/screenshots")

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_GRAY
        bg.line.fill.background()

    def add_header(slide, title_text, sop_step="SOP-KD-BOM-001 | KHALAPUR PLANT LINE 1"):
        h_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
        h_bar.fill.solid()
        h_bar.fill.fore_color.rgb = NAVY
        h_bar.line.fill.background()

        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.0), Inches(0.3))
        cat_tf = cat_box.text_frame
        p_cat = cat_tf.paragraphs[0]
        p_cat.text = sop_step.upper()
        p_cat.font.name = "Segoe UI"
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = RGBColor(190, 215, 245)

        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(10.0), Inches(0.6))
        t_tf = t_box.text_frame
        p_t = t_tf.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(21)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.2), Inches(0.35), Inches(1.3), Inches(0.4))
        badge.fill.solid()
        badge.fill.fore_color.rgb = GREEN
        badge.line.fill.background()
        b_tf = badge.text_frame
        b_p = b_tf.paragraphs[0]
        b_p.text = "v2.6.0-OBB"
        b_p.font.name = "Segoe UI"
        b_p.font.size = Pt(11)
        b_p.font.bold = True
        b_p.font.color.rgb = WHITE
        b_p.alignment = PP_ALIGN.CENTER

    def add_footer(slide):
        f_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4))
        f_bar.fill.solid()
        f_bar.fill.fore_color.rgb = NAVY_DARK
        f_bar.line.fill.background()

        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(6.5), Inches(0.35))
        tf = t_box.text_frame
        p = tf.paragraphs[0]
        p.text = "Standard Operating Procedure (SOP-KD-BOM-001)  •  Plant Line 1 (Khalapur)"
        p.font.name = "Segoe UI"
        p.font.size = Pt(9)
        p.font.color.rgb = RGBColor(200, 215, 240)

        r_box = slide.shapes.add_textbox(Inches(8.5), Inches(7.12), Inches(4.0), Inches(0.35))
        rtf = r_box.text_frame
        rp = rtf.paragraphs[0]
        rp.text = "Made with ❤️ by Aman"
        rp.font.name = "Segoe UI"
        rp.font.size = Pt(9)
        rp.font.bold = True
        rp.font.color.rgb = RGBColor(255, 200, 200)
        rp.alignment = PP_ALIGN.RIGHT

    def add_framed_screenshot(slide, img_path: pathlib.Path, left: Inches, top: Inches, width: Inches, caption: str = ""):
        if not img_path.exists():
            return
        im = Image.open(str(img_path))
        w, h = im.size
        aspect = h / w
        height = Inches(width.inches * aspect)

        pad = Inches(0.08)
        cap_h = Inches(0.4) if caption else Inches(0)
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left - pad, top - pad, width + pad * 2, height + pad * 2 + cap_h)
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = BORDER_GRAY
        card.line.width = Pt(1.5)

        slide.shapes.add_picture(str(img_path), left, top, width=width, height=height)

        if caption:
            cbox = slide.shapes.add_textbox(left, top + height + Inches(0.05), width, Inches(0.35))
            ctf = cbox.text_frame
            ctf.word_wrap = True
            cp = ctf.paragraphs[0]
            cp.text = caption
            cp.font.name = "Segoe UI"
            cp.font.size = Pt(9)
            cp.font.bold = True
            cp.font.color.rgb = NAVY
            cp.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 1: Title Slide (SOP Cover)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY_DARK
    bg1.line.fill.background()

    top_strip = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.15))
    top_strip.fill.solid()
    top_strip.fill.fore_color.rgb = GREEN
    top_strip.line.fill.background()

    main_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.1), Inches(10.933), Inches(5.1))
    main_card.fill.solid()
    main_card.fill.fore_color.rgb = WHITE
    main_card.line.color.rgb = BORDER_GRAY
    main_card.line.width = Pt(1.5)

    doc_pill = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.7), Inches(1.4), Inches(3.2), Inches(0.4))
    doc_pill.fill.solid()
    doc_pill.fill.fore_color.rgb = NAVY_LIGHT
    doc_pill.line.color.rgb = NAVY
    doc_pill.line.width = Pt(1)
    dp_tf = doc_pill.text_frame
    dp = dp_tf.paragraphs[0]
    dp.text = "OFFICIAL PLANT STANDARD OPERATING PROCEDURE"
    dp.font.name = "Segoe UI"
    dp.font.size = Pt(8.5)
    dp.font.bold = True
    dp.font.color.rgb = NAVY

    tbox = slide1.shapes.add_textbox(Inches(1.7), Inches(1.9), Inches(9.8), Inches(2.2))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    tp1 = ttf.paragraphs[0]
    tp1.text = "CONVEYOR BELT BOM VISION INSPECTOR"
    tp1.font.name = "Segoe UI"
    tp1.font.size = Pt(32)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY

    tp2 = ttf.add_paragraph()
    tp2.text = "Standard Operating Procedure (SOP-KD-BOM-001) & Technical Operation Manual"
    tp2.font.name = "Segoe UI"
    tp2.font.size = Pt(15)
    tp2.font.color.rgb = SLATE
    tp2.space_before = Pt(8)

    pills = [
        ("FACILITY", "Plant Line 1 (Khalapur)", NAVY_LIGHT, NAVY),
        ("QC GATE CRITERIA", "100% Zero-Defect Match", GREEN_LIGHT, GREEN),
        ("AI ARCHITECTURE", "YOLO26-OBB + ByteTrack", RGBColor(245, 240, 255), RGBColor(80, 40, 180)),
        ("DOCUMENT STATUS", "Released & Active", AMBER_LIGHT, AMBER)
    ]
    for i, (p_title, p_sub, p_bg, p_fg) in enumerate(pills):
        px = Inches(1.7 + i * 2.45)
        pill = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, Inches(4.3), Inches(2.35), Inches(1.1))
        pill.fill.solid()
        pill.fill.fore_color.rgb = p_bg
        pill.line.color.rgb = p_fg
        pill.line.width = Pt(1)
        ptf = pill.text_frame
        ptf.word_wrap = True
        pp1 = ptf.paragraphs[0]
        pp1.text = p_title
        pp1.font.name = "Segoe UI"
        pp1.font.size = Pt(9)
        pp1.font.bold = True
        pp1.font.color.rgb = p_fg
        pp2 = ptf.add_paragraph()
        pp2.text = p_sub
        pp2.font.name = "Segoe UI"
        pp2.font.size = Pt(11)
        pp2.font.bold = True
        pp2.font.color.rgb = DARK

    cred_box = slide1.shapes.add_textbox(Inches(1.2), Inches(6.45), Inches(10.933), Inches(0.5))
    ctf = cred_box.text_frame
    cp = ctf.paragraphs[0]
    cp.text = "Engineering Design & Implementation  •  Made with ❤️ by Aman  •  Khalapur Plant Line 1"
    cp.font.name = "Segoe UI"
    cp.font.size = Pt(11)
    cp.font.color.rgb = RGBColor(200, 220, 245)
    cp.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 2: Section 1 - Purpose & Quality Gate Philosophy
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_bg(slide2)
    add_header(slide2, "1. Purpose & Mandatory 100% Match Quality Gate", "SOP-KD-BOM-001 | SECTION 1")
    add_footer(slide2)

    c1 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    c1.fill.solid()
    c1.fill.fore_color.rgb = WHITE
    c1.line.color.rgb = BORDER_GRAY
    c1.line.width = Pt(1)

    t1 = slide2.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.0), Inches(0.5))
    t1_tf = t1.text_frame
    p1 = t1_tf.paragraphs[0]
    p1.text = "Operational Purpose & Scope"
    p1.font.name = "Segoe UI"
    p1.font.size = Pt(16)
    p1.font.bold = True
    p1.font.color.rgb = NAVY

    b1 = slide2.shapes.add_textbox(Inches(1.1), Inches(2.35), Inches(5.0), Inches(4.1))
    b1_tf = b1.text_frame
    b1_tf.word_wrap = True
    scope_points = [
        "Governs inspection, hardware verification, and audit logging for Knock-Down (KD) furniture packing kits on Packaging Line 1.",
        "Verifies that all hardware items (screws, dowels, shelf pins, eccentric cams, studs) match the exact bill of materials before carton sealing.",
        "Eliminates human counting error caused by high line speed (0.2 - 0.4 m/s), eye fatigue, and visual fastener similarities.",
        "Permanently eliminates missing hardware customer complaints across pan-India distribution channels."
    ]
    for idx, pt in enumerate(scope_points):
        p = b1_tf.paragraphs[0] if idx == 0 else b1_tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(10)

    c2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    c2.fill.solid()
    c2.fill.fore_color.rgb = WHITE
    c2.line.color.rgb = GREEN
    c2.line.width = Pt(1.5)

    callout_tag = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(1.75), Inches(5.133), Inches(0.55))
    callout_tag.fill.solid()
    callout_tag.fill.fore_color.rgb = GREEN_LIGHT
    callout_tag.line.color.rgb = GREEN
    callout_tag.line.width = Pt(1)
    ct_tf = callout_tag.text_frame
    cp = ct_tf.paragraphs[0]
    cp.text = "MANDATORY 100% MATCH QC GATE RULE"
    cp.font.name = "Segoe UI"
    cp.font.size = Pt(12)
    cp.font.bold = True
    cp.font.color.rgb = GREEN
    cp.alignment = PP_ALIGN.CENTER

    b2 = slide2.shapes.add_textbox(Inches(7.1), Inches(2.45), Inches(5.133), Inches(4.0))
    b2_tf = b2.text_frame
    b2_tf.word_wrap = True
    gate_points = [
        "Under ZERO circumstances may a kit box be taped, strapped, or dispatched if any hardware item has a count mismatch (Counted != Target).",
        "PASS State (#107C10): Every vision-inspected item matches target quantity exactly. Enables 'Complete Batch' button and triggers Zebra QC print.",
        "BLOCKED State (#D13438): If any item is missing (under-count) or extra (over-count), the screen triggers high-contrast red alerts and lists exact missing drawings.",
        "Audit Trail: Every batch verification writes an annotated high-resolution JPEG snapshot to disk with drawing tags and timestamp for traceability."
    ]
    for idx, pt in enumerate(gate_points):
        p = b2_tf.paragraphs[0] if idx == 0 else b2_tf.add_paragraph()
        p.text = f"✔  {pt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 3: SOP Step 1 - Zero-Touch System Startup
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_bg(slide3)
    add_header(slide3, "SOP Step 1: Zero-Touch Startup & Hardware Check", "SOP-KD-BOM-001 | STEP 1: INITIALIZATION")
    add_footer(slide3)

    steps_startup = [
        ("1. Launch Inspection Station", NAVY, [
            "Windows 11: Double-click start_windows.bat on desktop.",
            "Automatic checks: Detects Python 3.10/3.11, validates .venv, verifies dependencies.",
            "Initializes YOLO26-OBB base weights in backend/models/weights/.",
            "Compiles React frontend build and starts FastAPI server on port 8000.",
            "Automatically opens default browser to http://localhost:8000 after 2 seconds."
        ]),
        ("2. Verify Hardware Status Pills", GREEN, [
            "Inspect top Title Bar hardware status indicators:",
            "Camera Pill: Must display 'USB Camera 0 (Connected)' in green.",
            "Model Pill: Must display 'yolo26s-obb.pt (Active)'.",
            "FPS Counter: Verify bottom status bar reads ~30.0 FPS with ~14ms latency.",
            "If camera shows 'Warning No Signal', click 'Camera Source' in toolbar to select USB port."
        ]),
        ("3. Pre-Loaded Default Recipe", RGBColor(80, 40, 180), [
            "System automatically loads plant baseline recipe on startup:",
            "Master Item Code: 31162814SD05076",
            "Description: HRD PKT FOR MAIN BODY 900W/1200W 560D KREATION X3",
            "Total Target Fasteners: 68 pieces across 15 vision items.",
            "Virtual tripwire initializes with calibrated coordinates [0.55, 0.05, 0.55, 0.95]."
        ])
    ]

    for i, (stitle, scolor, spoints) in enumerate(steps_startup):
        sx = Inches(0.8 + i * 4.0)
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(1.5), Inches(3.75), Inches(5.2))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = scolor
        card.line.width = Pt(1.5)

        tbox = slide3.shapes.add_textbox(sx + Inches(0.2), Inches(1.75), Inches(3.35), Inches(0.6))
        ttf = tbox.text_frame
        p = ttf.paragraphs[0]
        p.text = stitle
        p.font.name = "Segoe UI"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = scolor

        bbox = slide3.shapes.add_textbox(sx + Inches(0.2), Inches(2.45), Inches(3.35), Inches(4.0))
        btf = bbox.text_frame
        btf.word_wrap = True
        for pt_idx, pt in enumerate(spoints):
            p = btf.paragraphs[0] if pt_idx == 0 else btf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.color.rgb = DARK
            p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 4: SOP Step 2 - Recipe Selection & Barcode Scan (WITH SCREENSHOT)
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_bg(slide4)
    add_header(slide4, "SOP Step 2: Recipe Loading & Barcode Scanning", "SOP-KD-BOM-001 | STEP 2: RECIPE TRIGGER")
    add_footer(slide4)

    # Left Column: SOP Text
    c_left = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.2), Inches(5.2))
    c_left.fill.solid()
    c_left.fill.fore_color.rgb = WHITE
    c_left.line.color.rgb = BORDER_GRAY
    c_left.line.width = Pt(1)

    t_box = slide4.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(4.8), Inches(0.5))
    tf = t_box.text_frame
    p = tf.paragraphs[0]
    p.text = "Operator Recipe Selection Flow"
    p.font.name = "Segoe UI"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = NAVY

    b_box = slide4.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.3))
    btf = b_box.text_frame
    btf.word_wrap = True
    steps_r = [
        "1. Scan Carton Barcode: Use handheld Zebra scanner to scan the Master Item Code printed on the packing work order (e.g. 31162814SD05076).",
        "2. Manual Input: Alternatively, type the Master Code into the Ribbon 'Recipe Trigger' field and press 'Load'.",
        "3. Active Recipe Verification: Confirm that the Top Title Bar updates with the active Master Code and official kit name in bold yellow.",
        "4. BOM Grid Population: The right Excel-style grid loads all drawing numbers, descriptions, and target quantities (e.g. 68 pcs total).",
        "5. Auto-Reset Counters: Loading a recipe automatically resets counted quantities to 0 and clears tripwire memory for the new batch."
    ]
    for idx, pt in enumerate(steps_r):
        p = btf.paragraphs[0] if idx == 0 else btf.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)

    # Right Column: Framed Screenshot of Home / Inspection Tab
    img_home = screenshots_dir / "01_home_inspection.jpg"
    add_framed_screenshot(slide4, img_home, Inches(6.3), Inches(1.5), Inches(6.2), "Fig 1: Home / Inspection View showing Ribbon Bar, Live Viewport & BOM Grid")

    # =========================================================================
    # SLIDE 5: SOP Step 3 - Conveyor Feeding & Real-Time Counting (WITH SCREENSHOT)
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_bg(slide5)
    add_header(slide5, "SOP Step 3: Conveyor Feeding & Tripwire Counting", "SOP-KD-BOM-001 | STEP 3: CONVEYOR COUNTING")
    add_footer(slide5)

    c_left5 = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.2), Inches(5.2))
    c_left5.fill.solid()
    c_left5.fill.fore_color.rgb = WHITE
    c_left5.line.color.rgb = BORDER_GRAY
    c_left5.line.width = Pt(1)

    t_box5 = slide5.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(4.8), Inches(0.5))
    tf5 = t_box5.text_frame
    p5 = tf5.paragraphs[0]
    p5.text = "Live Fastener Inspection Protocol"
    p5.font.name = "Segoe UI"
    p5.font.size = Pt(16)
    p5.font.bold = True
    p5.font.color.rgb = CYAN

    b_box5 = slide5.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.3))
    btf5 = b_box5.text_frame
    btf5.word_wrap = True
    feed_points = [
        "1. Conveyor Feeding: Operator spreads packet fasteners onto the belt upstream of the camera lens. Maintain single-layer spread.",
        "2. YOLO26-OBB Detection: System detects rotated bounding boxes (OBB) from 0-360° with green polygons and Drawing No labels.",
        "3. Motion Tracking: ByteTrack assigns a persistent track_id and renders a yellow motion velocity trail.",
        "4. Virtual Tripwire Crossing: When the object centroid crosses the cyan tripwire line in the LEFT_TO_RIGHT direction, count increments.",
        "5. Debounce Protection: Track ID is remembered once crossed—fastener will NOT double-count if conveyor pauses or vibrates.",
        "6. Live Row Status: Grid row highlights change in real time: WAIT (gray) -> PROG (amber) -> MATCH (green) -> OVER (red)."
    ]
    for idx, pt in enumerate(feed_points):
        p = btf5.paragraphs[0] if idx == 0 else btf5.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(7)

    # Right Column: Framed Screenshot of Live Audit Snapshot
    img_snap = screenshots_dir / "05_audit_snapshot.jpg"
    add_framed_screenshot(slide5, img_snap, Inches(6.3), Inches(1.5), Inches(6.2), "Fig 2: Real-time Inspection with OBB Detections, Drawing Numbers & Virtual Tripwire")

    # =========================================================================
    # SLIDE 6: SOP Step 4 - 100% Match QC Gate & Zebra Printing
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_bg(slide6)
    add_header(slide6, "SOP Step 4: 100% Match QC Gate & Zebra QC Printing", "SOP-KD-BOM-001 | STEP 4: QC VERIFICATION")
    add_footer(slide6)

    # Pass Card
    pass_c = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    pass_c.fill.solid()
    pass_c.fill.fore_color.rgb = WHITE
    pass_c.line.color.rgb = GREEN
    pass_c.line.width = Pt(1.5)

    p_tag = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.1), Inches(1.75), Inches(5.0), Inches(0.55))
    p_tag.fill.solid()
    p_tag.fill.fore_color.rgb = GREEN_LIGHT
    p_tag.line.color.rgb = GREEN
    p_tag.line.width = Pt(1)
    ptf_t = p_tag.text_frame
    pp = ptf_t.paragraphs[0]
    pp.text = "PASS SCENARIO (100% MATCH)"
    pp.font.name = "Segoe UI"
    pp.font.size = Pt(12)
    pp.font.bold = True
    pp.font.color.rgb = GREEN
    pp.alignment = PP_ALIGN.CENTER

    p_body = slide6.shapes.add_textbox(Inches(1.1), Inches(2.45), Inches(5.0), Inches(4.0))
    pbtf = p_body.text_frame
    pbtf.word_wrap = True
    pass_steps = [
        "1. Press 'Complete Batch' button in Ribbon Toolbar once all hardware has crossed the tripwire.",
        "2. Verification Check: All 15 vision-inspected items have Counted == Target (e.g. 68 / 68 pcs).",
        "3. High-Contrast PASS Banner: Viewport displays large green PASS overlay (#107C10).",
        "4. QC Alert Modal: Opens summary showing green checkmarks on all drawing numbers.",
        "5. Automated Zebra Print: System sends ESC/POS print payload to Zebra ZD421 QC label printer.",
        "6. Carton Sealing: Operator attaches verified QC label to kit carton and seals for dispatch."
    ]
    for idx, pt in enumerate(pass_steps):
        p = pbtf.paragraphs[0] if idx == 0 else pbtf.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)

    # Blocked Card
    block_c = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    block_c.fill.solid()
    block_c.fill.fore_color.rgb = WHITE
    block_c.line.color.rgb = RED
    block_c.line.width = Pt(1.5)

    b_tag = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.1), Inches(1.75), Inches(5.133), Inches(0.55))
    b_tag.fill.solid()
    b_tag.fill.fore_color.rgb = RED_LIGHT
    b_tag.line.color.rgb = RED
    b_tag.line.width = Pt(1)
    btf_t = b_tag.text_frame
    bp = btf_t.paragraphs[0]
    bp.text = "BLOCKED SCENARIO (DISCREPANCY)"
    bp.font.name = "Segoe UI"
    bp.font.size = Pt(12)
    bp.font.bold = True
    bp.font.color.rgb = RED
    bp.alignment = PP_ALIGN.CENTER

    b_body = slide6.shapes.add_textbox(Inches(7.1), Inches(2.45), Inches(5.133), Inches(4.0))
    bbtf = b_body.text_frame
    bbtf.word_wrap = True
    block_steps = [
        "1. Discrepancy Detected: If Counted < Target (missing items) or Counted > Target (overcount).",
        "2. Red BLOCKED Banner: Viewport flashes high-contrast red alert banner (#D13438).",
        "3. Missing Items Discrepancy Modal: Pop-up lists exact item description, drawing number, target quantity, and missing shortfall (e.g. -2 pcs).",
        "4. Interlock Action: Label printer is locked—zero labels can be printed until resolved.",
        "5. Corrective Action: Operator inspects packet, adds the missing fasteners, passes them across the tripwire, and re-clicks 'Complete Batch'.",
        "6. Incident Logged: Discrepancy details recorded in Audit Session database for shift analysis."
    ]
    for idx, pt in enumerate(block_steps):
        p = bbtf.paragraphs[0] if idx == 0 else bbtf.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)

    # =========================================================================
    # SLIDE 7: SOP Step 5 - Managing Manufacturing BOM Recipes (WITH SCREENSHOT)
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_bg(slide7)
    add_header(slide7, "SOP Step 5: Managing Plant BOM Recipes", "SOP-KD-BOM-001 | STEP 5: RECIPE REGISTRY")
    add_footer(slide7)

    c_left7 = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.2), Inches(5.2))
    c_left7.fill.solid()
    c_left7.fill.fore_color.rgb = WHITE
    c_left7.line.color.rgb = BORDER_GRAY
    c_left7.line.width = Pt(1)

    t_box7 = slide7.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(4.8), Inches(0.5))
    tf7 = t_box7.text_frame
    p7 = tf7.paragraphs[0]
    p7.text = "Plant Recipe Registry Controls"
    p7.font.name = "Segoe UI"
    p7.font.size = Pt(16)
    p7.font.bold = True
    p7.font.color.rgb = NAVY

    b_box7 = slide7.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.3))
    btf7 = b_box7.text_frame
    btf7.word_wrap = True
    recipe_mgmt_steps = [
        "1. Access Recipe Registry: Click 'BOM Recipes' in Ribbon Toolbar to view all configured manufacturing kits.",
        "2. Review Kit Metadata: Inspect Master Item Code, Kit Description, Total Lines, and Vision Inspected item count.",
        "3. Active Recipe Indicator: The currently active kit displays a bold green 'ACTIVE NOW' pill.",
        "4. Switch Active Kit: To change production line to a different kit, click 'Activate Recipe' on any stored recipe.",
        "5. Download Standard Template: Click 'Download Standard Template (.xlsx)' button to get the official plant Excel formatting template.",
        "6. Global Parts Catalog Tab: Switch sub-tab to inspect registered Drawing Numbers and their YOLO class mapping."
    ]
    for idx, pt in enumerate(recipe_mgmt_steps):
        p = btf7.paragraphs[0] if idx == 0 else btf7.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)

    img_rec = screenshots_dir / "02_bom_recipes.jpg"
    add_framed_screenshot(slide7, img_rec, Inches(6.3), Inches(1.5), Inches(6.2), "Fig 3: Plant Recipe Registry showing Master Codes, Item Counts & ACTIVE NOW status")

    # =========================================================================
    # SLIDE 8: SOP Step 6 - Excel BOM Import & Drawing Validation (WITH SCREENSHOT)
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_bg(slide8)
    add_header(slide8, "SOP Step 6: Importing Excel BOMs & Validation", "SOP-KD-BOM-001 | STEP 6: EXCEL IMPORT")
    add_footer(slide8)

    c_left8 = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.2), Inches(5.2))
    c_left8.fill.solid()
    c_left8.fill.fore_color.rgb = WHITE
    c_left8.line.color.rgb = BORDER_GRAY
    c_left8.line.width = Pt(1)

    t_box8 = slide8.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(4.8), Inches(0.5))
    tf8 = t_box8.text_frame
    p8 = tf8.paragraphs[0]
    p8.text = "Excel Import & Drawing Validation"
    p8.font.name = "Segoe UI"
    p8.font.size = Pt(16)
    p8.font.bold = True
    p8.font.color.rgb = GREEN

    b_box8 = slide8.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.3))
    btf8 = b_box8.text_frame
    btf8.word_wrap = True
    import_steps = [
        "1. Click 'Import Excel BOM' in Ribbon Toolbar to open the upload modal.",
        "2. Upload Plant Sheet: Drag & drop any official Excel BOM (.xlsx, .xls) or plant CSV file.",
        "3. Auto-Exclusion: System automatically unchecks packaging cartons, polybags, and stickers.",
        "4. Missing Drawing Warning: If any item lacks a drawing number, an amber warning banner appears.",
        "5. In-Modal Correction: Operators can type the drawing number directly in the grid without modifying Excel.",
        "6. Item Deletion: Click the red Trash icon to remove unwanted non-hardware lines.",
        "7. Commit to System: Click 'Commit Recipe' to register new drawing numbers in parts catalog."
    ]
    for idx, pt in enumerate(import_steps):
        p = btf8.paragraphs[0] if idx == 0 else btf8.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(7)

    img_modal = screenshots_dir / "04_excel_upload_modal.png"
    add_framed_screenshot(slide8, img_modal, Inches(6.3), Inches(1.5), Inches(6.2), "Fig 4: Excel BOM Upload Modal with Missing Drawing Warnings & In-Place Editing")

    # =========================================================================
    # SLIDE 9: SOP Step 7 - Dataset & Auto-Labeling Studio (WITH SCREENSHOT)
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_bg(slide9)
    add_header(slide9, "SOP Step 7: Dataset Creation & Auto-Labeling Studio", "SOP-KD-BOM-001 | STEP 7: AUTO-LABELING")
    add_footer(slide9)

    c_left9 = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.2), Inches(5.2))
    c_left9.fill.solid()
    c_left9.fill.fore_color.rgb = WHITE
    c_left9.line.color.rgb = BORDER_GRAY
    c_left9.line.width = Pt(1)

    t_box9 = slide9.shapes.add_textbox(Inches(1.0), Inches(1.7), Inches(4.8), Inches(0.5))
    tf9 = t_box9.text_frame
    p9 = tf9.paragraphs[0]
    p9.text = "Fastener Annotation Workflow"
    p9.font.name = "Segoe UI"
    p9.font.size = Pt(16)
    p9.font.bold = True
    p9.font.color.rgb = RGBColor(120, 50, 180)

    b_box9 = slide9.shapes.add_textbox(Inches(1.0), Inches(2.25), Inches(4.8), Inches(4.3))
    btf9 = b_box9.text_frame
    btf9.word_wrap = True
    label_steps = [
        "1. Access Studio: Click 'Dataset & Labeling' tab when new hardware parts are introduced.",
        "2. Image Acquisition: Click 'Capture Frame' to grab image from conveyor or 'Browse Component Images' to upload component photos.",
        "3. OpenCV Auto-Box: Click 'Auto Box' button to automatically detect fastener contours and propose rotated bounding boxes.",
        "4. Manual BBox [R]: Press 'R' to draw custom precision rotated bounding boxes.",
        "5. Label Selection: Click drawing number chip in the top 'BOM Labels' bar or press 1-9.",
        "6. Save to Dataset [Ctrl+Enter]: Saves normalized YOLO-OBB text files and increments sample counts in database."
    ]
    for idx, pt in enumerate(label_steps):
        p = btf9.paragraphs[0] if idx == 0 else btf9.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(7)

    img_lbl = screenshots_dir / "03_labeling_studio.jpg"
    add_framed_screenshot(slide9, img_lbl, Inches(6.3), Inches(1.5), Inches(6.2), "Fig 5: Dataset & Labeling Studio with OpenCV Auto-Box and Drawing Number Chips")

    # =========================================================================
    # SLIDE 10: SOP Step 8 - YOLO26 Training & Zero-Downtime Hot-Swap
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_bg(slide10)
    add_header(slide10, "SOP Step 8: YOLO Model Training & Model Hot-Swap", "SOP-KD-BOM-001 | STEP 8: MODEL TRAINING")
    add_footer(slide10)

    train_cards = [
        ("1. Configure Training Job", NAVY, [
            "Navigate to 'Model Training' ribbon tab.",
            "Base Weights: Select 'yolo26s-obb.pt' as pretrained backbone.",
            "Epochs: Standard 50 epochs (or 100 for complex multi-screw kits).",
            "Image Resolution: 1280x720 (native camera resolution).",
            "Device: 'auto' (detects NVIDIA CUDA GPU or falls back to multi-core CPU).",
            "Click 'Start YOLO26 Training'."
        ]),
        ("2. Real-Time Metric Monitoring", RGBColor(80, 40, 180), [
            "Training runs in background thread—conveyor inspection remains active.",
            "Progress Bar: Live epoch progress (e.g. Epoch 24/50).",
            "Convergence Graph: Real-time loss curve display.",
            "mAP50 Accuracy: Must achieve >92% mAP50 for plant deployment approval.",
            "Auto-Save: Checkpoints saved to backend/models/weights/."
        ]),
        ("3. Zero-Downtime Model Hot-Swap", GREEN, [
            "Open 'Available Models' table in Model Training tab.",
            "Locate newly trained model weights file (e.g. train_20261118_120000.pt).",
            "Click 'Activate Model' button.",
            "System reloads Ultralytics ByteTrack weights dynamically in memory.",
            "ZERO line shutdown required—live conveyor stream adopts new weights instantly."
        ])
    ]

    for i, (ttitle, tcolor, tpoints) in enumerate(train_cards):
        tx = Inches(0.8 + i * 4.0)
        tcard = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, tx, Inches(1.5), Inches(3.75), Inches(5.2))
        tcard.fill.solid()
        tcard.fill.fore_color.rgb = WHITE
        tcard.line.color.rgb = tcolor
        tcard.line.width = Pt(1.5)

        ttbox = slide10.shapes.add_textbox(tx + Inches(0.2), Inches(1.75), Inches(3.35), Inches(0.6))
        tttf = ttbox.text_frame
        p = tttf.paragraphs[0]
        p.text = ttitle
        p.font.name = "Segoe UI"
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = tcolor

        tbbox = slide10.shapes.add_textbox(tx + Inches(0.2), Inches(2.45), Inches(3.35), Inches(4.0))
        tb_tf = tbbox.text_frame
        tb_tf.word_wrap = True
        for pt_idx, pt in enumerate(tpoints):
            p = tb_tf.paragraphs[0] if pt_idx == 0 else tb_tf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.color.rgb = DARK
            p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 11: Troubleshooting & Shift Handover Checklist
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_bg(slide11)
    add_header(slide11, "Troubleshooting Matrix & Shift Handover SOP", "SOP-KD-BOM-001 | SECTION 9 & 10")
    add_footer(slide11)

    t_card = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    t_card.fill.solid()
    t_card.fill.fore_color.rgb = WHITE
    t_card.line.color.rgb = RED
    t_card.line.width = Pt(1)

    tt = slide11.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.0), Inches(0.5))
    ttf_s = tt.text_frame
    tp = ttf_s.paragraphs[0]
    tp.text = "Troubleshooting & Error Recovery"
    tp.font.name = "Segoe UI"
    tp.font.size = Pt(15)
    tp.font.bold = True
    tp.font.color.rgb = RED

    tb = slide11.shapes.add_textbox(Inches(1.1), Inches(2.35), Inches(5.0), Inches(4.1))
    tbtf = tb.text_frame
    tbtf.word_wrap = True
    trouble_points = [
        "Camera Offline (No Signal): Check USB3 cable connection. Click 'Camera Source' in toolbar and select USB Camera 0. Restart start_windows.bat if port is locked.",
        "Missing Counts on Tripwire: Ensure parts cross the cyan line completely. Click 'Tripwire Adjust' in toolbar to position the line across full conveyor width.",
        "Double-Counting Hardware: Fasteners are bouncing or vibrating backwards. Ensure conveyor speed is within 0.2 - 0.4 m/s and belt is tensioned.",
        "Excel BOM Fails to Upload: Verify file contains sheet named 'BOM Details' or standard column headers: 'Sr No', 'Item Name', 'Drawing No', 'Qty'."
    ]
    for idx, pt in enumerate(trouble_points):
        p = tbtf.paragraphs[0] if idx == 0 else tbtf.add_paragraph()
        p.text = f"⚠  {pt}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)

    h_card = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    h_card.fill.solid()
    h_card.fill.fore_color.rgb = WHITE
    h_card.line.color.rgb = GREEN
    h_card.line.width = Pt(1)

    ht = slide11.shapes.add_textbox(Inches(7.1), Inches(1.75), Inches(5.1), Inches(0.5))
    htf = ht.text_frame
    hp = htf.paragraphs[0]
    hp.text = "Daily Shift Handover Checklist"
    hp.font.name = "Segoe UI"
    hp.font.size = Pt(15)
    hp.font.bold = True
    hp.font.color.rgb = GREEN

    hb = slide11.shapes.add_textbox(Inches(7.1), Inches(2.35), Inches(5.1), Inches(4.1))
    hbtf = hb.text_frame
    hbtf.word_wrap = True
    checklist = [
        "[ ] Camera Lens Inspection: Wipe overhead lens with microfiber cloth to remove industrial dust.",
        "[ ] Conveyor Belt Surface: Ensure matte belt is clean and free of metal shavings or grease.",
        "[ ] Golden Sample Run: Scan Master Kit 31162814SD05076 and run 1 verified test packet (Must yield 100% PASS).",
        "[ ] Zebra Label Printer: Verify thermal paper roll has >50 labels remaining and printhead is clean.",
        "[ ] Audit Log Review: Verify past shift's batch pass yield (Target: >95%).",
        "[ ] Sign Shift Log: Outgoing and incoming operators sign daily QC log sheet."
    ]
    for idx, pt in enumerate(checklist):
        p = hbtf.paragraphs[0] if idx == 0 else hbtf.add_paragraph()
        p.text = pt
        p.font.name = "Segoe UI"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK
        p.space_after = Pt(9)

    prs.save(str(output_path))
    print(f"SOP Presentation generated successfully with screenshots: {output_path}")

if __name__ == "__main__":
    out_file = pathlib.Path("Industrial_BOM_Vision_Inspector_Overview.pptx")
    build_sop_deck(out_file)
