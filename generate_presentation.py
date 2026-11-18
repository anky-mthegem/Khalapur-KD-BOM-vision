"""
Professional Presentation Generator for Industrial Conveyor Belt BOM Vision Inspector.
Generates an executive-ready 16:9 widescreen .pptx presentation.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path: Path):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette: Industrial Office Ribbon Theme
    NAVY = RGBColor(43, 87, 154)       # #2B579A - MS Word Blue
    NAVY_DARK = RGBColor(30, 62, 109)  # #1E3E6D
    NAVY_LIGHT = RGBColor(237, 243, 252) # Soft blue tint
    GREEN = RGBColor(16, 124, 16)      # #107C10 - Quality Pass
    GREEN_LIGHT = RGBColor(223, 246, 221)
    RED = RGBColor(209, 52, 56)        # #D13438 - Discrepancy
    RED_LIGHT = RGBColor(253, 231, 233)
    CYAN = RGBColor(0, 164, 228)       # #00A4E4 - Tripwire
    SLATE = RGBColor(96, 94, 92)       # #605E5C
    DARK = RGBColor(32, 31, 30)        # #201F1E
    WHITE = RGBColor(255, 255, 255)
    BG_GRAY = RGBColor(243, 242, 241)  # #F3F2F1
    BORDER_GRAY = RGBColor(210, 208, 206) # #D2D0CE

    def add_header(slide, title_text, category_text="KHALAPUR PLANT LINE 1 | INDUSTRIAL VISION INSPECTION"):
        # Header background bar
        h_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
        h_bar.fill.solid()
        h_bar.fill.fore_color.rgb = NAVY
        h_bar.line.fill.background()

        # Category / Breadcrumb
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.7), Inches(0.3))
        cat_tf = cat_box.text_frame
        cat_tf.word_wrap = True
        p_cat = cat_tf.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.name = "Segoe UI"
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = RGBColor(180, 205, 240)

        # Slide Title
        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.38), Inches(10.0), Inches(0.6))
        t_tf = t_box.text_frame
        t_tf.word_wrap = True
        p_t = t_tf.paragraphs[0]
        p_t.text = title_text
        p_t.font.name = "Segoe UI"
        p_t.font.size = Pt(22)
        p_t.font.bold = True
        p_t.font.color.rgb = WHITE

        # System Badge
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.1), Inches(0.35), Inches(1.4), Inches(0.4))
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
        # Bottom status bar
        f_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.1), Inches(13.333), Inches(0.4))
        f_bar.fill.solid()
        f_bar.fill.fore_color.rgb = NAVY_DARK
        f_bar.line.fill.background()

        t_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.12), Inches(6.0), Inches(0.35))
        tf = t_box.text_frame
        p = tf.paragraphs[0]
        p.text = "KD BOM Vision Inspector  |  Plant Line 1 (Khalapur)  |  Confidential"
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

    def set_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_GRAY
        bg.line.fill.background()

    # =========================================================================
    # SLIDE 1: Title Slide (Executive Industrial Theme)
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY_DARK
    bg1.line.fill.background()

    # Subtle top accent bar
    top_acc = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.15))
    top_acc.fill.solid()
    top_acc.fill.fore_color.rgb = GREEN
    top_acc.line.fill.background()

    # Main Card
    main_c = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(10.933), Inches(4.8))
    main_c.fill.solid()
    main_c.fill.fore_color.rgb = WHITE
    main_c.line.color.rgb = BORDER_GRAY
    main_c.line.width = Pt(1.5)

    # Title inside card
    tbox = slide1.shapes.add_textbox(Inches(1.8), Inches(1.6), Inches(9.8), Inches(1.8))
    ttf = tbox.text_frame
    ttf.word_wrap = True
    tp1 = ttf.paragraphs[0]
    tp1.text = "INDUSTRIAL CONVEYOR BELT\nBOM VISION INSPECTOR"
    tp1.font.name = "Segoe UI"
    tp1.font.size = Pt(36)
    tp1.font.bold = True
    tp1.font.color.rgb = NAVY

    tp2 = ttf.add_paragraph()
    tp2.text = "Autonomous AI Verification, 100% Match QC Gate & YOLO26-OBB Tracking System"
    tp2.font.name = "Segoe UI"
    tp2.font.size = Pt(16)
    tp2.font.color.rgb = SLATE
    tp2.space_before = Pt(12)

    # 3 Summary Stat Pills
    pill_data = [
        ("PLANT LINE 1", "Khalapur Facility", NAVY_LIGHT, NAVY),
        ("PRECISION TARGET", "100% Zero-Defect Match", GREEN_LIGHT, GREEN),
        ("AI ENGINE", "YOLO26-OBB + ByteTrack", RGBColor(240, 240, 255), RGBColor(80, 40, 180)),
    ]
    for i, (title, sub, bgcolor, fgcolor) in enumerate(pill_data):
        px = Inches(1.8 + i * 3.3)
        pill = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, Inches(3.9), Inches(3.1), Inches(1.0))
        pill.fill.solid()
        pill.fill.fore_color.rgb = bgcolor
        pill.line.color.rgb = fgcolor
        pill.line.width = Pt(1)
        ptf = pill.text_frame
        ptf.word_wrap = True
        pp1 = ptf.paragraphs[0]
        pp1.text = title
        pp1.font.name = "Segoe UI"
        pp1.font.size = Pt(11)
        pp1.font.bold = True
        pp1.font.color.rgb = fgcolor
        pp2 = ptf.add_paragraph()
        pp2.text = sub
        pp2.font.name = "Segoe UI"
        pp2.font.size = Pt(13)
        pp2.font.bold = True
        pp2.font.color.rgb = DARK

    # Author Credit in bottom footer of title slide
    fbox = slide1.shapes.add_textbox(Inches(1.2), Inches(6.3), Inches(10.933), Inches(0.6))
    ftf = fbox.text_frame
    fp = ftf.paragraphs[0]
    fp.text = "System Architecture & Engineering  •  Made with ❤️ by Aman  •  Plant Line 1 Khalapur"
    fp.font.name = "Segoe UI"
    fp.font.size = Pt(12)
    fp.font.color.rgb = RGBColor(200, 220, 245)
    fp.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 2: The Manufacturing Problem & Business Value
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_bg(slide2)
    add_header(slide2, "Manufacturing Challenge & Quality Mandate")
    add_footer(slide2)

    col_data = [
        ("The Packaging Problem", RED_LIGHT, RED, [
            "Knock-Down (KD) furniture kits require up to 68 individual fasteners (screws, nuts, brackets, studs).",
            "Manual human counting on fast-moving conveyors suffers from eye fatigue, distraction, and tally slips.",
            "Missing hardware packet errors are only discovered after shipping to customers across India."
        ]),
        ("Why Traditional Vision Fails", RGBColor(255, 248, 230), RGBColor(180, 110, 0), [
            "Axis-aligned bounding boxes (YOLO boxes) overlap heavily when fasteners tumble or cluster on the belt.",
            "Hardware appearance varies across vendor batches, anti-rust coatings, and lighting flickers.",
            "Rigid industrial sensors cannot adapt to dynamic plant BOM recipe changes or multiple kit variants."
        ]),
        ("The Autonomous AI Solution", GREEN_LIGHT, GREEN, [
            "Oriented Bounding Boxes (OBB): Rotated 4-point polygons accurately isolate angled screws at 0-360°.",
            "Virtual Tripwire with ByteTrack: Real-time 2D geometric vector intersection tracks crossing parts.",
            "100% Match QC Gate: Prevents box sealing unless exact recipe counts match engineering drawing specs."
        ])
    ]

    for i, (col_title, bgcol, fgcol, points) in enumerate(col_data):
        cx = Inches(0.8 + i * 4.0)
        cshape = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(1.5), Inches(3.75), Inches(5.2))
        cshape.fill.solid()
        cshape.fill.fore_color.rgb = WHITE
        cshape.line.color.rgb = BORDER_GRAY
        cshape.line.width = Pt(1)

        # Header tag on card
        tag = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx + Inches(0.25), Inches(1.75), Inches(3.25), Inches(0.6))
        tag.fill.solid()
        tag.fill.fore_color.rgb = bgcol
        tag.line.color.rgb = fgcol
        tag.line.width = Pt(1)
        tt_f = tag.text_frame
        tp = tt_f.paragraphs[0]
        tp.text = col_title
        tp.font.name = "Segoe UI"
        tp.font.size = Pt(13)
        tp.font.bold = True
        tp.font.color.rgb = fgcol
        tp.alignment = PP_ALIGN.CENTER

        # Body text
        bbox = slide2.shapes.add_textbox(cx + Inches(0.25), Inches(2.55), Inches(3.25), Inches(3.9))
        btf = bbox.text_frame
        btf.word_wrap = True
        for pt_idx, pt in enumerate(points):
            p = btf.paragraphs[0] if pt_idx == 0 else btf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11.5)
            p.font.color.rgb = DARK
            p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 3: End-to-End System Architecture Pipeline
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_bg(slide3)
    add_header(slide3, "System Architecture: From Conveyor Video to Verified Packet")
    add_footer(slide3)

    stages = [
        ("1. Video Ingestion", "Hardware Layer", NAVY, [
            "DirectShow USB 3.0 / RTSP",
            "Pristine 1280x720 capture",
            "30 FPS steady acquisition",
            "Diagnostic fallback feed"
        ]),
        ("2. OBB Perception", "Ultralytics YOLO26", RGBColor(80, 40, 180), [
            "Oriented Bounding Boxes",
            "360° rotation invariant",
            "Trained on Plant BOM catalog",
            "Sub-15ms CUDA/CPU latency"
        ]),
        ("3. Motion Tracking", "ByteTrack Algorithm", CYAN, [
            "Persistent integer track_ids",
            "8-state Kalman filtering",
            "Motion velocity vectors",
            "Handles occlusions & tumble"
        ]),
        ("4. QC Gate & Audit", "Tripwire Engine", GREEN, [
            "Vector crossing detection",
            "Drawing No unique mapping",
            "100% Target count gate",
            "Zebra QC print + audit log"
        ])
    ]

    for i, (stitle, ssub, scolor, items) in enumerate(stages):
        sx = Inches(0.8 + i * 3.0)
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(1.6), Inches(2.75), Inches(4.2))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = scolor
        card.line.width = Pt(1.5)

        # Header of stage card
        shead = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, sx, Inches(1.6), Inches(2.75), Inches(0.9))
        shead.fill.solid()
        shead.fill.fore_color.rgb = scolor
        shead.line.fill.background()
        stf = shead.text_frame
        sp1 = stf.paragraphs[0]
        sp1.text = stitle
        sp1.font.name = "Segoe UI"
        sp1.font.size = Pt(12)
        sp1.font.bold = True
        sp1.font.color.rgb = WHITE
        sp1.alignment = PP_ALIGN.CENTER
        sp2 = stf.add_paragraph()
        sp2.text = ssub.upper()
        sp2.font.name = "Segoe UI"
        sp2.font.size = Pt(9)
        sp2.font.color.rgb = RGBColor(220, 230, 255)
        sp2.alignment = PP_ALIGN.CENTER

        # Items
        sbox = slide3.shapes.add_textbox(sx + Inches(0.15), Inches(2.65), Inches(2.45), Inches(3.0))
        s_tf = sbox.text_frame
        s_tf.word_wrap = True
        for it_idx, it in enumerate(items):
            p = s_tf.paragraphs[0] if it_idx == 0 else s_tf.add_paragraph()
            p.text = f"✔ {it}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.color.rgb = DARK
            p.space_after = Pt(10)

    # Bottom workflow connectivity banner
    flow_b = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.733), Inches(0.8))
    flow_b.fill.solid()
    flow_b.fill.fore_color.rgb = NAVY_LIGHT
    flow_b.line.color.rgb = NAVY
    flow_b.line.width = Pt(1)
    fl_tf = flow_b.text_frame
    fl_p = fl_tf.paragraphs[0]
    fl_p.text = "HIGH-PERFORMANCE DATA FLOW: Real-Time Stream -> Zero-Latency MJPEG Generator -> Threadsafe WebSockets -> React UI State"
    fl_p.font.name = "Segoe UI"
    fl_p.font.size = Pt(11)
    fl_p.font.bold = True
    fl_p.font.color.rgb = NAVY
    fl_p.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 4: Drawing Number as Universal Unique Identifier
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_bg(slide4)
    add_header(slide4, "Universal Identifier: Engineering Drawing Numbers")
    add_footer(slide4)

    left_card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.2))
    left_card.fill.solid()
    left_card.fill.fore_color.rgb = WHITE
    left_card.line.color.rgb = BORDER_GRAY
    left_card.line.width = Pt(1)

    ltitle = slide4.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(0.5))
    ltf = ltitle.text_frame
    lp = ltf.paragraphs[0]
    lp.text = "Strict Engineering Drawing Integrity"
    lp.font.name = "Segoe UI"
    lp.font.size = Pt(16)
    lp.font.bold = True
    lp.font.color.rgb = NAVY

    lbody = slide4.shapes.add_textbox(Inches(1.1), Inches(2.3), Inches(5.0), Inches(4.2))
    lbtf = lbody.text_frame
    lbtf.word_wrap = True
    dwg_rules = [
        "100% Non-Nullable Enforcement: Every item in the BOM must have an official engineering drawing number (e.g. HOM196273, DOS210915).",
        "Unified Unique Key: Drawing numbers serve as primary keys across SQLite database, parts catalog, YOLO classes, and vision tracking.",
        "Item Name Association: Technical item descriptions are permanently bound to drawing numbers in parts_catalog table.",
        "YOLO Class Generation: data.yaml classes are explicitly compiled as: {0: 'HOM196273', 1: 'DOS210915', ...} eliminating naming ambiguities."
    ]
    for idx, rule in enumerate(dwg_rules):
        p = lbtf.paragraphs[0] if idx == 0 else lbtf.add_paragraph()
        p.text = f"•  {rule}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(10)

    right_card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.5), Inches(5.733), Inches(5.2))
    right_card.fill.solid()
    right_card.fill.fore_color.rgb = WHITE
    right_card.line.color.rgb = BORDER_GRAY
    right_card.line.width = Pt(1)

    rtitle = slide4.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.1), Inches(0.5))
    rtf = rtitle.text_frame
    rp = rtf.paragraphs[0]
    rp.text = "Intelligent BOM Import & Validation"
    rp.font.name = "Segoe UI"
    rp.font.size = Pt(16)
    rp.font.bold = True
    rp.font.color.rgb = GREEN

    rbody = slide4.shapes.add_textbox(Inches(7.1), Inches(2.3), Inches(5.1), Inches(4.2))
    rbtf = rbody.text_frame
    rbtf.word_wrap = True
    import_rules = [
        "Excel (.xlsx) & CSV Parser: Instantly imports Plant Master BOMs with Master Item Code, Drawing No, and Target Quantities.",
        "Missing Drawing Warning Banner: Upload modal alerts users if any hardware lacks a valid drawing number before committing.",
        "Interactive Correction: Operators can enter missing drawing numbers directly in the modal grid without altering Excel source files.",
        "Item Deletion Control: Allows one-click deletion (Trash icon) of unwanted non-hardware items during upload preview.",
        "Auto-Packaging Exclusion: Automatically filters out non-vision packaging cartons and stickers."
    ]
    for idx, rule in enumerate(import_rules):
        p = rbtf.paragraphs[0] if idx == 0 else rbtf.add_paragraph()
        p.text = f"✔  {rule}"
        p.font.name = "Segoe UI"
        p.font.size = Pt(11.5)
        p.font.color.rgb = DARK
        p.space_after = Pt(10)

    # =========================================================================
    # SLIDE 5: Virtual Tripwire & 100% Match QC Gate
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_bg(slide5)
    add_header(slide5, "Virtual Tripwire & 100% Match Quality Gate")
    add_footer(slide5)

    tw_boxes = [
        ("Directional Flow Vector", "Line Intersection Geometry", CYAN, [
            "2D vector calculation: segments_intersect(prev_centroid, curr_centroid, P1, P2)",
            "Directional vector normal dot-product enforces LEFT_TO_RIGHT conveyor movement.",
            "Eliminates false double-counts: object track_id is debounced once crossing completes.",
            "Operator can drag tripwire handles directly on video viewport to adapt to conveyor speed."
        ]),
        ("100% Match Verification Gate", "Strict Packaging Compliance", GREEN, [
            "Operators press 'Complete Batch' when packet reaches conveyor packing station.",
            "Compares counted vs target quantity for all vision-inspected items in active recipe.",
            "PASS Gate (#107C10): All quantities match 100% -> triggers Zebra QC print payload.",
            "BLOCKED Gate (#D13438): Flags missing or overcounted hardware with exact drawing numbers."
        ])
    ]

    for i, (wtitle, wsub, wcolor, witems) in enumerate(tw_boxes):
        wx = Inches(0.8 + i * 5.9)
        wcard = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, wx, Inches(1.5), Inches(5.6), Inches(4.0))
        wcard.fill.solid()
        wcard.fill.fore_color.rgb = WHITE
        wcard.line.color.rgb = wcolor
        wcard.line.width = Pt(1.5)

        wtbox = slide5.shapes.add_textbox(wx + Inches(0.3), Inches(1.7), Inches(5.0), Inches(0.7))
        wttf = wtbox.text_frame
        wp1 = wttf.paragraphs[0]
        wp1.text = wtitle
        wp1.font.name = "Segoe UI"
        wp1.font.size = Pt(16)
        wp1.font.bold = True
        wp1.font.color.rgb = wcolor
        wp2 = wttf.add_paragraph()
        wp2.text = wsub.upper()
        wp2.font.name = "Segoe UI"
        wp2.font.size = Pt(10)
        wp2.font.color.rgb = SLATE

        wbbox = slide5.shapes.add_textbox(wx + Inches(0.3), Inches(2.45), Inches(5.0), Inches(2.9))
        wbtf = wbbox.text_frame
        wbtf.word_wrap = True
        for it_idx, it in enumerate(witems):
            p = wbtf.paragraphs[0] if it_idx == 0 else wbtf.add_paragraph()
            p.text = f"•  {it}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11.5)
            p.font.color.rgb = DARK
            p.space_after = Pt(8)

    # Bottom Audit Log Banner
    audit_banner = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(5.7), Inches(11.733), Inches(1.1))
    audit_banner.fill.solid()
    audit_banner.fill.fore_color.rgb = WHITE
    audit_banner.line.color.rgb = NAVY
    audit_banner.line.width = Pt(1)

    ab_tf = audit_banner.text_frame
    ab_p1 = ab_tf.paragraphs[0]
    ab_p1.text = "IMMUTABLE AUDIT COMPLIANCE & HIGH-RESOLUTION SNAPSHOTS"
    ab_p1.font.name = "Segoe UI"
    ab_p1.font.size = Pt(11)
    ab_p1.font.bold = True
    ab_p1.font.color.rgb = NAVY

    ab_p2 = ab_tf.add_paragraph()
    ab_p2.text = "Every completed batch automatically archives an annotated high-resolution JPEG snapshot to disk with bounding boxes, drawing numbers, and timestamp. Accessible anytime from the Audit Logs tab for customer traceability and root-cause analysis."
    ab_p2.font.name = "Segoe UI"
    ab_p2.font.size = Pt(10)
    ab_p2.font.color.rgb = DARK

    # =========================================================================
    # SLIDE 6: Dataset & Labeling Studio + Model Training
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_bg(slide6)
    add_header(slide6, "Dataset Creation, Auto-Labeling & On-Premise Training")
    add_footer(slide6)

    d_stages = [
        ("Capture & Ingest", NAVY, [
            "Capture Frame: Snaps pristine raw frame from live conveyor camera.",
            "Browse Upload: Supports dragging high-res component photos directly into the app.",
            "BOM Labels Bar: Quick 1-click selection chips for all items in active recipe."
        ]),
        ("Adaptive Annotation", RGBColor(120, 60, 180), [
            "OpenCV Auto-Box: Dynamic adaptive thresholding + contour analysis for OBB proposals.",
            "Manual Box Tool [R]: Draw precision rotated boxes with custom aspect angles.",
            "Keyboard shortcuts: [R] Box, [V] Select, [Ctrl+Enter] Save & next image."
        ]),
        ("Ultralytics Training", GREEN, [
            "Zero-Config YOLO Training: Generates data.yaml with clean relative paths.",
            "Live Epoch Streaming: Real-time progress bar, loss curves, and mAP50 metrics.",
            "Model Hot-Swap: Activate new weights live into vision engine without app restart."
        ])
    ]

    for i, (dtitle, dcolor, dpoints) in enumerate(d_stages):
        dx = Inches(0.8 + i * 4.0)
        dcard = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, dx, Inches(1.5), Inches(3.75), Inches(5.2))
        dcard.fill.solid()
        dcard.fill.fore_color.rgb = WHITE
        dcard.line.color.rgb = dcolor
        dcard.line.width = Pt(1.5)

        dtbox = slide6.shapes.add_textbox(dx + Inches(0.2), Inches(1.7), Inches(3.35), Inches(0.6))
        dttf = dtbox.text_frame
        dp = dttf.paragraphs[0]
        dp.text = dtitle
        dp.font.name = "Segoe UI"
        dp.font.size = Pt(15)
        dp.font.bold = True
        dp.font.color.rgb = dcolor

        dbbox = slide6.shapes.add_textbox(dx + Inches(0.2), Inches(2.4), Inches(3.35), Inches(4.1))
        dbtf = dbbox.text_frame
        dbtf.word_wrap = True
        for p_idx, pt in enumerate(dpoints):
            p = dbtf.paragraphs[0] if p_idx == 0 else dbtf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11)
            p.font.color.rgb = DARK
            p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 7: User Experience: "Industrial Office Ribbon"
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_bg(slide7)
    add_header(slide7, "UI/UX Design: The Industrial Office Ribbon")
    add_footer(slide7)

    u_features = [
        ("MS Office Ribbon Paradigm", NAVY, "Categorized tabs (Home / Inspection, BOM Recipes, Dataset & Labeling, Model Training, Audit Logs) familiar to plant operators accustomed to Microsoft Word and Excel. Zero hidden hamburger menus or complex nested modals."),
        ("High-Contrast Utilitarian Aesthetic", DARK, "Built for high-glare manufacturing shopfloors. Light-mode background (#F3F2F1) with crisp typography, high-visibility green (#107C10) and red (#D13438) status banners, and large touch/click targets suitable for glove use."),
        ("65% / 35% Split Inspection Workspace", CYAN, "Left Viewport (65%) shows real-time conveyor MJPEG stream with virtual tripwire and live bounding boxes. Right Pane (35%) shows an Excel-style dense BOM Recipe Grid with live Target, Counted, and Balance counters."),
        ("Comprehensive Status & Traceability", GREEN, "Bottom status bar features live FPS counter, camera latency indicator, active YOLO26 model file badge, total batch pass/fail counter, zoom controls, and author engineering sign-off ('Made with ❤️ by Aman').")
    ]

    for i, (utitle, ucolor, udesc) in enumerate(u_features):
        row = i // 2
        col = i % 2
        ux = Inches(0.8 + col * 5.9)
        uy = Inches(1.5 + row * 2.65)

        ucard = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, ux, uy, Inches(5.6), Inches(2.4))
        ucard.fill.solid()
        ucard.fill.fore_color.rgb = WHITE
        ucard.line.color.rgb = BORDER_GRAY
        ucard.line.width = Pt(1)

        utbox = slide7.shapes.add_textbox(ux + Inches(0.25), uy + Inches(0.18), Inches(5.1), Inches(0.5))
        uttf = utbox.text_frame
        up = uttf.paragraphs[0]
        up.text = utitle
        up.font.name = "Segoe UI"
        up.font.size = Pt(14)
        up.font.bold = True
        up.font.color.rgb = ucolor

        ubbox = slide7.shapes.add_textbox(ux + Inches(0.25), uy + Inches(0.68), Inches(5.1), Inches(1.6))
        ubtf = ubbox.text_frame
        ubtf.word_wrap = True
        up2 = ubtf.paragraphs[0]
        up2.text = udesc
        up2.font.name = "Segoe UI"
        up2.font.size = Pt(11)
        up2.font.color.rgb = DARK

    # =========================================================================
    # SLIDE 8: Cross-Platform Deployment & Portability
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_bg(slide8)
    add_header(slide8, "Cross-Platform Mandate & Autonomous Deployment")
    add_footer(slide8)

    plat_cards = [
        ("Windows 11 Dev & Testing", NAVY, [
            "start_windows.bat: One-click autonomous launcher script.",
            "DirectShow Camera Backend: Zero-latency instantaneous frame capture.",
            "Mock Hardware Simulator: /simulate-crossing endpoint for offline automated testing without physical conveyor hardware.",
            "Built-in verification: Tests all 29 pytest test suites before launching FastAPI server on port 8000."
        ]),
        ("Ubuntu Linux 22.04/24.04 LTS Prod", RGBColor(220, 80, 0), [
            "setup_ubuntu.sh: Production deployment automation script with apt package provisioning and venv isolation.",
            "systemd Service: bom-inspector.service configuration for 24/7 autonomous plant line auto-start on boot.",
            "Pure Pathlib Portability: 100% path safety using pathlib.Path—zero Windows drive letter hardcoding.",
            "SQLite Zero-Config Database: Zero external database daemon dependencies."
        ])
    ]

    for i, (ptitle, pcolor, ppoints) in enumerate(plat_cards):
        px = Inches(0.8 + i * 5.9)
        pcard = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px, Inches(1.5), Inches(5.6), Inches(5.2))
        pcard.fill.solid()
        pcard.fill.fore_color.rgb = WHITE
        pcard.line.color.rgb = pcolor
        pcard.line.width = Pt(1.5)

        ptbox = slide8.shapes.add_textbox(px + Inches(0.3), Inches(1.75), Inches(5.0), Inches(0.6))
        pttf = ptbox.text_frame
        pp = pttf.paragraphs[0]
        pp.text = ptitle
        pp.font.name = "Segoe UI"
        pp.font.size = Pt(16)
        pp.font.bold = True
        pp.font.color.rgb = pcolor

        pbbox = slide8.shapes.add_textbox(px + Inches(0.3), Inches(2.5), Inches(5.0), Inches(4.0))
        pbtf = pbbox.text_frame
        pbtf.word_wrap = True
        for pt_idx, pt in enumerate(ppoints):
            p = pbtf.paragraphs[0] if pt_idx == 0 else pbtf.add_paragraph()
            p.text = f"✔  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11.5)
            p.font.color.rgb = DARK
            p.space_after = Pt(12)

    # =========================================================================
    # SLIDE 9: Plant Impact, Summary & Roadmap
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_bg(slide9)
    add_header(slide9, "Summary & Future Automation Roadmap")
    add_footer(slide9)

    summary_items = [
        ("Proven Plant Impact", GREEN, [
            "100% Hardware Match: Eliminates missing screw complaints and costly field technician visits.",
            "30 FPS Real-Time Inspection: Zero conveyor slowdown or operator bottlenecks.",
            "Universal Drawing Number Integrity: Complete synchronization across Engineering, ERP, and Vision AI.",
            "Rapid Kit Changeover: Scan new master barcode in <2 seconds to switch active inspection recipe."
        ]),
        ("Phase 2 Industrial Roadmap", NAVY, [
            "PLC Pneumatic Reject Flipper: Integrate RS-485 Modbus relay to auto-divert defect packets.",
            "Multi-Camera Stereo Depth: Dual-camera top/side perspective for complex 3D hardware stacking.",
            "Enterprise SAP/ERP Sync: Direct automated sync of plant production orders and lot dispatch records.",
            "Edge AI TPU Acceleration: Deploy on NVIDIA Jetson Orin for ultra-low power plant enclosures."
        ])
    ]

    for i, (stitle, scolor, spoints) in enumerate(summary_items):
        sx = Inches(0.8 + i * 5.9)
        scard = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(1.5), Inches(5.6), Inches(4.3))
        scard.fill.solid()
        scard.fill.fore_color.rgb = WHITE
        scard.line.color.rgb = scolor
        scard.line.width = Pt(1.5)

        stbox = slide9.shapes.add_textbox(sx + Inches(0.3), Inches(1.75), Inches(5.0), Inches(0.6))
        sttf = stbox.text_frame
        sp = sttf.paragraphs[0]
        sp.text = stitle
        sp.font.name = "Segoe UI"
        sp.font.size = Pt(16)
        sp.font.bold = True
        sp.font.color.rgb = scolor

        sbbox = slide9.shapes.add_textbox(sx + Inches(0.3), Inches(2.5), Inches(5.0), Inches(3.1))
        sbtf = sbbox.text_frame
        sbtf.word_wrap = True
        for pt_idx, pt in enumerate(spoints):
            p = sbtf.paragraphs[0] if pt_idx == 0 else sbtf.add_paragraph()
            p.text = f"•  {pt}"
            p.font.name = "Segoe UI"
            p.font.size = Pt(11.5)
            p.font.color.rgb = DARK
            p.space_after = Pt(10)

    # Engineering Sign-Off Card
    sign_off = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(6.0), Inches(11.733), Inches(0.9))
    sign_off.fill.solid()
    sign_off.fill.fore_color.rgb = NAVY_LIGHT
    sign_off.line.color.rgb = NAVY
    sign_off.line.width = Pt(1)

    so_tf = sign_off.text_frame
    so_p1 = so_tf.paragraphs[0]
    so_p1.text = "ENGINEERING SIGN-OFF & OPERATIONAL READINESS"
    so_p1.font.name = "Segoe UI"
    so_p1.font.size = Pt(11)
    so_p1.font.bold = True
    so_p1.font.color.rgb = NAVY

    so_p2 = so_tf.add_paragraph()
    so_p2.text = "Developed & Commissioned by Aman  •  Plant Line 1 (Khalapur)  •  Status: Production Verified (All 29 Tests Passing)"
    so_p2.font.name = "Segoe UI"
    so_p2.font.size = Pt(10)
    so_p2.font.bold = True
    so_p2.font.color.rgb = DARK

    # Save presentation
    prs.save(str(output_path))
    print(f"Presentation generated successfully: {output_path}")

if __name__ == "__main__":
    out_file = Path("Industrial_BOM_Vision_Inspector_Overview.pptx")
    create_deck(out_file)
