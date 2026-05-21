from pptx import Presentation
from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
import os
import uuid
import random
from copy import deepcopy
import platform
import shutil
import subprocess
try:
    import spacy  # type: ignore
except Exception:
    spacy = None  # type: ignore
import requests
import json
import re
from PIL import Image
import io

# Optional Windows-only COM automation (guarded)
WIN32_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import win32com.client  # type: ignore
        import pythoncom  # type: ignore
        WIN32_AVAILABLE = True
    except Exception:
        WIN32_AVAILABLE = False

# Load spaCy model for text analysis (graceful fallback if unavailable)
if spacy is not None:
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        try:
            from spacy.cli import download  # type: ignore
            download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            nlp = None
else:
    nlp = None

UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

def fetch_image_from_pexels(query, save_dir="Uploads/images"):
    """Fallback provider using Pexels API."""
    try:
        api_key = (os.getenv("PEXELS_API_KEY") or PEXELS_API_KEY or "").strip()
        if not api_key:
            return None
        q = str(query or "").strip()
        q = re.sub(r"[\n\r]+", " ", q)
        q = re.sub(r"[\"'(){}\[\]:]", "", q)
        q = re.sub(r"\s+", " ", q)
        q = q[:120] or "abstract background"
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}
        params = {"query": q, "per_page": 1}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        try:
            resp.raise_for_status()
        except Exception:
            print(f"Pexels API error ({resp.status_code}) for query '{q}': {resp.text[:180]}")
            return None
        photos = resp.json().get("photos", [])
        if not photos:
            return None
        image_url = photos[0].get("src", {}).get("large") or photos[0].get("src", {}).get("original")
        if not image_url:
            return None
        image_filename = f"slideimg_{uuid.uuid4().hex[:8]}.jpg"
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)
        img = requests.get(image_url, timeout=20)
        img.raise_for_status()
        with open(image_path, "wb") as f:
            f.write(img.content)
        print(f"Successfully fetched image from Pexels: {image_path}")
        return image_path
    except Exception as e:
        print(f"Pexels fetch failed for '{query}': {e}")
        return None

def fetch_image_from_pollinations(query, save_dir="Uploads/images"):
    """Fetch an AI-generated image from Pollinations.ai (FREE, no daily limits).
    Uses image.pollinations.ai/prompt/ endpoint which is confirmed working.
    """
    import urllib.parse
    import time

    # Clean and simplify the query for image generation
    q = str(query or "").strip()
    q = re.sub(r"[\n\r]+", " ", q)
    q = re.sub(r"[\"'(){}\'\[\]:;!@#$%^&*]", "", q)
    q = re.sub(r"\s+", " ", q)
    # Keep first 6 words for focused image
    words = [w for w in q.split() if len(w) > 2]
    q = " ".join(words[:6]) if words else "professional presentation background"
    if not q.strip():
        q = "professional presentation background"

    os.makedirs(save_dir, exist_ok=True)

    # Try up to 2 times with different seeds
    for attempt in range(2):
        try:
            seed = random.randint(1, 999999)
            prompt = f"{q}, professional stock photo, high quality, realistic"
            encoded_prompt = urllib.parse.quote(prompt)
            
            # CONFIRMED WORKING endpoint: image.pollinations.ai/prompt/
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&seed={seed}&nologo=true"

            print(f"  [Pollinations attempt {attempt+1}] Fetching image for: '{q}'")
            
            # Small delay between slides to avoid rate limiting
            if attempt > 0:
                time.sleep(3)
            else:
                time.sleep(1.5)

            img_resp = requests.get(url, timeout=60, allow_redirects=True)
            
            if img_resp.status_code == 402 or img_resp.status_code == 429:
                print(f"  ⚠️ Pollinations returned {img_resp.status_code}. Retrying with simpler prompt...")
                # Try a much simpler prompt
                simple_prompt = urllib.parse.quote(q)
                url = f"https://image.pollinations.ai/prompt/{simple_prompt}?width=800&height=600&seed={seed+1}&nologo=true"
                time.sleep(3)
                img_resp = requests.get(url, timeout=60, allow_redirects=True)

            img_resp.raise_for_status()

            content_type = img_resp.headers.get('content-type', '')
            if 'image' not in content_type and len(img_resp.content) < 10000:
                print(f"  ⚠️ Response is not an image (content-type: {content_type}, size: {len(img_resp.content)})")
                continue

            if len(img_resp.content) < 5000:
                print(f"  ⚠️ Image too small ({len(img_resp.content)} bytes)")
                continue

            image_filename = f"slideimg_{uuid.uuid4().hex[:8]}.jpg"
            image_path = os.path.join(save_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(img_resp.content)
            print(f"  ✅ Successfully generated AI image: {image_path} ({len(img_resp.content)} bytes)")
            return image_path

        except Exception as e:
            print(f"  ❌ Pollinations attempt {attempt+1} failed for '{q}': {e}")

    # All Pollinations attempts failed, try Pexels then placeholder
    print(f"  Falling back to Pexels/Placeholder for '{query}'")
    p = fetch_image_from_pexels(query, save_dir)
    return p if p else create_placeholder_image(query, save_dir)


def fetch_image_from_unsplash(query, save_dir="Uploads/images"):
    """Fetch a relevant image from Unsplash (primary source).
    Falls back to Pollinations (1 free image), then Pexels, then placeholder.
    """
    try:
        api_key = (os.getenv("UNSPLASH_API_KEY") or UNSPLASH_API_KEY or "").strip()
        if not api_key:
            print("No Unsplash API key, trying Pollinations...")
            return fetch_image_from_pollinations(query, save_dir)

        # Clean query for stock photo search
        q = str(query or "").strip()
        q = re.sub(r"[\n\r]+", " ", q)
        q = re.sub(r"[\"'(){}\[\]:;!@#$%^&*]", "", q)
        q = re.sub(r"\s+", " ", q)
        words = [w for w in q.split() if len(w) > 2]
        q = " ".join(words[:4]) if words else "abstract background"
        q = q[:80]
        if not q.strip():
            q = "abstract background"

        url = "https://api.unsplash.com/search/photos"
        headers = {
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1",
        }
        params = {
            "query": q,
            "per_page": 3,
            "content_filter": "high",
            "orientation": "landscape"
        }
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()

        results = response.json().get("results", [])
        if results:
            # Pick best landscape image
            best_img = max(results, key=lambda img: img.get("width", 0))
            image_url = best_img["urls"].get("regular") or best_img["urls"].get("small")
            if image_url:
                image_filename = f"slideimg_{uuid.uuid4().hex[:8]}.jpg"
                save_dir_abs = os.path.abspath(save_dir)
                os.makedirs(save_dir_abs, exist_ok=True)
                image_path = os.path.join(save_dir_abs, image_filename)
                img = requests.get(image_url, timeout=20)
                img.raise_for_status()
                with open(image_path, "wb") as f:
                    f.write(img.content)
                rel_path = os.path.join(save_dir, image_filename)
                print(f"  ✅ Unsplash image fetched for '{q}': {rel_path}")
                return rel_path

        print(f"  No Unsplash results for '{q}', trying placeholder...")
        return create_placeholder_image(query, save_dir)
    except Exception as e:
        print(f"  Unsplash failed for '{query}': {e}. Trying placeholder...")
        return create_placeholder_image(query, save_dir)

def get_contrast_text_color(slide, slide_width, slide_height):
    """
    Detect the background color of the slide and return 'dark' or 'light'
    based on the average brightness to ensure text readability.
    """
    try:
        # Check for background image
        # This is a simplified version. In a real scenario, we might scan the image.
        # For now, we look at the theme color or background fill if available.
        # Fallback to 'light' background (dark text) if we can't determine.
        
        # Check if there's a full-slide image (likely background)
        for shape in slide.shapes:
            if shape.shape_type == 13: # PICTURE
                # If picture covers most of the slide, assume dark background for safety 
                # (most presentation backgrounds are dark/image based)
                if shape.width > slide_width * 0.8 and shape.height > slide_height * 0.8:
                    return "dark" # implies light text
        
        # Default to light background (= dark text)
        return "light"
    except Exception:
        return "light"

def get_text_color_for_contrast(contrast_type, theme_colors=None):
    """
    Returns an RGBColor object (White or Black) based on background contrast.
    If theme colors provided, can pick one of them.
    """
    if contrast_type == "dark":
        return RGBColor(255, 255, 255) # White text for dark background
    else:
        # Use primary theme color if it's dark enough, else black
        if theme_colors and len(theme_colors) > 0:
            try:
                hex_color = theme_colors[0].lstrip('#')
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                # Check brightness of theme color
                brightness = (r * 299 + g * 587 + b * 114) / 1000
                if brightness < 150: # Dark enough for light background
                    return RGBColor(r, g, b)
            except:
                pass
        return RGBColor(0, 0, 0) # Black text for light background

def create_placeholder_image(query, save_dir="Uploads/images"):
    """
    Create a beautiful placeholder image with gradient background and text
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a beautiful gradient placeholder image
        width, height = 800, 600
        
        # Create gradient background
        img = Image.new('RGB', (width, height), color=(41, 128, 185))  # Blue gradient start
        draw = ImageDraw.Draw(img)
        
        # Create gradient effect
        for y in range(height):
            r = int(41 + (y / height) * 30)  # Blue to lighter blue
            g = int(128 + (y / height) * 40)
            b = int(185 + (y / height) * 20)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add a subtle pattern
        for i in range(0, width, 50):
            for j in range(0, height, 50):
                draw.ellipse([i, j, i+2, j+2], fill=(255, 255, 255, 30))
        
        # Add border
        draw.rectangle([0, 0, width-1, height-1], outline=(255, 255, 255), width=5)
        
        # Add icon placeholder
        icon_size = 80
        icon_x = (width - icon_size) // 2
        icon_y = (height - icon_size) // 2 - 50
        draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], 
                    outline=(255, 255, 255), width=3, fill=(255, 255, 255, 50))
        
        # Add text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw the query text
        text = query[:40] + "..." if len(query) > 40 else query
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 + 50
        
        # Add text shadow
        draw.text((x+2, y+2), text, fill=(0, 0, 0, 100), font=font)
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Add "Image Placeholder" text
        placeholder_text = "Image Placeholder"
        placeholder_bbox = draw.textbbox((0, 0), placeholder_text, font=font)
        placeholder_width = placeholder_bbox[2] - placeholder_bbox[0]
        placeholder_x = (width - placeholder_width) // 2
        placeholder_y = y + text_height + 20
        
        draw.text((placeholder_x, placeholder_y), placeholder_text, fill=(255, 255, 255, 150), font=font)
        
        # Save the image
        image_filename = f"placeholder_{uuid.uuid4().hex[:8]}.png"
        os.makedirs(save_dir, exist_ok=True)
        image_path = os.path.join(save_dir, image_filename)
        img.save(image_path)
        
        print(f"Created beautiful placeholder image: {image_path}")
        return image_path
    except Exception as e:
        print(f"Failed to create placeholder image: {e}")
        return None

def add_custom_slide(prs, slide_data, image_path=None):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    layout = slide_data.get("layout", "").lower()
    
    # Add image first if available
    if layout == "image left, text right" and image_path:
        slide.shapes.add_picture(image_path, Inches(0.2), Inches(1), Inches(4), Inches(4))
        txBox = slide.shapes.add_textbox(Inches(4.5), Inches(1), Inches(5), Inches(4))
    elif layout == "image right, text left" and image_path:
        txBox = slide.shapes.add_textbox(Inches(0.2), Inches(1), Inches(5), Inches(4))
        slide.shapes.add_picture(image_path, Inches(5.5), Inches(1), Inches(4), Inches(4))
    elif layout == "full image" and image_path:
        slide.shapes.add_picture(image_path, Inches(0.2), Inches(0.2), Inches(9), Inches(6))
        txBox = slide.shapes.add_textbox(Inches(1), Inches(5.5), Inches(8), Inches(1.2))
    else:
        txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(4))
    
    tf = txBox.text_frame
    tf.text = slide_data.get("title", "")
    for bullet in slide_data.get("bullets", []):
        p = tf.add_paragraph()
        p.text = bullet
        p.level = 1
    
    # Detect contrast and apply appropriate text color
    slide_width = prs.slide_width
    slide_height = prs.slide_height
    contrast_type = get_contrast_text_color(slide, slide_width, slide_height)
    text_color = get_text_color_for_contrast(contrast_type, slide_data.get("theme", ["#003087", "#FFFFFF"]))
    
    # Apply contrast-based text color to all paragraphs
    for paragraph in tf.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = text_color
    
    return slide

def add_two_column_content(slide, slide_data, presentation, slide_width, slide_height):
    """Render a two-column layout with a single centered bold title at the top,
    then two body text columns (left/right) below. Sizes are derived from template.
    slide_data keys:
      - title (top centered)
      - body_left, body_right (string or list). If missing, split 'bullets' evenly.
    """
    # Layout ratios: 45% (left) + 10% (gap) + 45% (right)
    # No overlap by construction
    top_margin = Inches(0.2)
    bottom_margin = Inches(0.2)

    # Determine content
    title_text = slide_data.get("title", "")
    body_left = slide_data.get("body_left")
    body_right = slide_data.get("body_right")
    if body_left is None and body_right is None:
        bullets = slide_data.get("bullets", [])
        half = (len(bullets) + 1) // 2
        body_left = "\n".join(bullets[:half])
        body_right = "\n".join(bullets[half:])

    # Detect contrast and text color once
    contrast_type = get_contrast_text_color(slide, slide_width, slide_height)
    text_color = get_text_color_for_contrast(contrast_type, slide_data.get("theme", ["#003087", "#FFFFFF"]))

    # Scale fonts with slide width, but respect template inheritance if available
    scale_w = slide_width / Inches(10)  # 10in wide as baseline
    try:
        tmp = slide.shapes.add_textbox(Inches(0.1), Inches(0.1), Inches(1), Inches(0.5))
        tf = tmp.text_frame
        tf.text = "Tmp"
        inherited = get_inherited_font_size(tmp, slide, presentation)
        base_pt = inherited.pt if inherited else 20
        # Title/body base sizes and scaled
        title_pt = int(max(20, min(44, base_pt * 1.3 * scale_w)))
        body_pt = int(max(12, min(28, base_pt * 0.9 * scale_w)))
        slide.shapes._spTree.remove(tmp._element)
    except Exception:
        title_pt = int(28 * scale_w)
        body_pt = int(18 * scale_w)

    # Title area box (top centered)
    title_height = int(slide_height * 0.16)
    title_box = slide.shapes.add_textbox(Inches(0), top_margin, slide_width, title_height)
    ttf = title_box.text_frame
    ttf.clear()
    ttf.word_wrap = True
    p_title = ttf.paragraphs[0]
    p_title.text = title_text
    p_title.alignment = PP_ALIGN.CENTER
    for run in p_title.runs:
        run.font.bold = True
        run.font.size = Pt(title_pt)
        run.font.color.rgb = text_color

    # Columns area
    top_of_columns = top_margin + title_height + Inches(0.05)
    column_height = slide_height - top_of_columns - bottom_margin
    left_x = int(slide_width * 0.0)
    left_w = int(slide_width * 0.45)
    right_x = int(slide_width * 0.55)
    right_w = int(slide_width * 0.45)

    def body_to_lines(body_text):
        if isinstance(body_text, list):
            return body_text
        if isinstance(body_text, str):
            return [ln for ln in body_text.splitlines() if ln.strip()]
        return []

    def add_body_column(left_pos, width_pos, body_text):
        tx = slide.shapes.add_textbox(left_pos, top_of_columns, width_pos, column_height)
        tf = tx.text_frame
        tf.clear()
        tf.word_wrap = True
        lines = body_to_lines(body_text)
        if not lines:
            return
        # First paragraph
        tf.text = lines[0]
        for run in tf.paragraphs[0].runs:
            run.font.size = Pt(body_pt)
            run.font.color.rgb = text_color
        # Remaining as paragraphs
        for ln in lines[1:]:
            p = tf.add_paragraph()
            p.text = ln
            p.level = 1
            for run in p.runs:
                run.font.size = Pt(body_pt)
                run.font.color.rgb = text_color
        tf.margin_left = Inches(0.02)
        tf.margin_right = Inches(0.02)
        tf.margin_top = Inches(0.02)
        tf.margin_bottom = Inches(0.02)

    # Left column near left border
    add_body_column(left_x, left_w, body_left)
    # Right column near right border
    add_body_column(right_x, right_w, body_right)

def generate_gamma_style_ppt(slides_content, template_path=None, layout_index=None):
    if template_path and os.path.exists(template_path):
        prs = Presentation(template_path)
        for i in range(len(prs.slides)-1, -1, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
    else:
        prs = Presentation()
    # Use user-selected layout if provided
    if layout_index is not None and 0 <= layout_index < len(prs.slide_layouts):
        base_layout = prs.slide_layouts[layout_index]
    else:
        base_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[0]
    for slide_data in slides_content:
        image_path = None
        image_desc = slide_data.get("image_desc")
        if image_desc:
            try:
                image_path = fetch_image_from_unsplash(image_desc)
            except Exception as e:
                print(f"Image fetch failed for '{image_desc}': {e}")
        # Add slide with selected or default layout
        slide = prs.slides.add_slide(base_layout)
        slide_width = prs.slide_width
        slide_height = prs.slide_height
        padding = Inches(0.5)
        img_width = int(slide_width * 0.4)
        img_height = int(slide_height * 0.6)
        # Find first textbox placeholder (for text)
        txBox = None
        for shape in slide.shapes:
            if shape.is_placeholder and shape.placeholder_format.type in [1, 2, 14]:  # TITLE, BODY, CONTENT
                txBox = shape
                break
        
        if not txBox:
            txBox = slide.shapes.add_textbox(padding, padding, slide_width - 2*padding, slide_height - 2*padding)
        # If layout requests two-column text, render that and skip default single-column text
        layout_name = str(slide_data.get("layout", "")).strip().lower()
        if layout_name in ("two-column", "two column", "two columns"):
            add_two_column_content(slide, slide_data, prs, slide_width, slide_height)
        else:
            tf = txBox.text_frame
            tf.clear()
            tf.word_wrap = True
            tf.text = slide_data.get("title", "")
            for bullet in slide_data.get("bullets", []):
                p = tf.add_paragraph()
                p.text = bullet
                p.level = 1
                p.font.size = Pt(18)
        
        # Image placement (if any) - Add image first so we can detect background
        if image_path:
            img_placeholder = None
            for shape in slide.shapes:
                if shape.is_placeholder and shape.placeholder_format.type == 18:  # PICTURE
                    img_placeholder = shape
                    break
        if img_placeholder and os.path.exists(image_path):
            img_placeholder.insert_picture(image_path)
        else:
            if image_path and os.path.exists(image_path):
                img = slide.shapes.add_picture(image_path, padding, slide_height - img_height - padding, width=img_width, height=img_height)
                from PIL import Image as PILImage
                with PILImage.open(image_path) as pil_img:
                    aspect = pil_img.width / pil_img.height
                    if img_width / img_height > aspect:
                        new_width = int(img_height * aspect)
                        img.width = new_width
                        img.left = padding
                    else:
                        new_height = int(img_width / aspect)
                        img.height = new_height
                        img.top = slide_height - new_height - padding
        
        # Detect contrast and get appropriate text color AFTER adding image
        contrast_type = get_contrast_text_color(slide, slide_width, slide_height)
        text_color = get_text_color_for_contrast(contrast_type, slide_data.get("theme", ["#003087", "#FFFFFF"]))

        # Apply contrast-based text color to default single-column case
        if layout_name not in ("two-column", "two column", "two columns"):
            for paragraph in tf.paragraphs:
                for run in paragraph.runs:
                    run.font.color.rgb = text_color
            tf.margin_left = Inches(0.2)
            tf.margin_right = Inches(0.2)
            tf.margin_top = Inches(0.1)
            tf.margin_bottom = Inches(0.1)
            tf.vertical_anchor = MSO_VERTICAL_ANCHOR.TOP
            for paragraph in tf.paragraphs:
                paragraph.alignment = PP_ALIGN.LEFT
    output_path = os.path.join("outputs", f"gamma_style_{uuid.uuid4().hex[:8]}.pptx")
    prs.save(output_path)
    return output_path

def normalize_text(text):
    """Normalize text by removing extra spaces, newlines, and converting to lowercase for comparison."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip()).lower()
    return text

def analyze_text_role(text, paragraph_level):
    """Analyze the role of text (e.g., title, body, bullet) using NLP and paragraph level."""
    doc = nlp(text) if 'nlp' in globals() and nlp else None
    if paragraph_level > 0:
        return "bullet"
    if any(line.strip().startswith(("-", "•", "*")) for line in text.splitlines()):
        return "bullet"
    if len(text.split()) < 5 or (doc is not None and len(doc.ents) > 0):
        return "title"
    else:
        return "body"

def get_inherited_font_size(shape, slide, presentation):
    """Get the inherited font size from shape, slide, or presentation theme if not explicitly set."""
    if shape.text_frame.paragraphs:
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                if run.font.size is not None:
                    return run.font.size
    slide_layout = slide.slide_layout
    if slide_layout:
        for shape in slide_layout.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.size is not None:
                            return run.font.size
    return Pt(18)

def get_inherited_font_color(shape, slide, presentation):
    """Get the inherited font color from shape, slide, or presentation theme if not explicitly set."""
    if shape.text_frame.paragraphs:
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                if hasattr(run.font.color, 'rgb') and run.font.color.rgb is not None:
                    return run.font.color.rgb
    slide_layout = slide.slide_layout
    if slide_layout:
        for shape in slide_layout.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        if hasattr(run.font.color, 'rgb') and run.font.color.rgb is not None:
                            return run.font.color.rgb
    return RGBColor(0, 0, 0)

def copy_run_formatting(src_run, dst_run, shape, slide, presentation):
    # NO scaling, just copy original
    font_size = src_run.font.size
    if font_size is None:
        font_size = get_inherited_font_size(shape, slide, presentation)
    dst_run.font.size = font_size
    if src_run.font.name:
        dst_run.font.name = src_run.font.name
    if src_run.font.bold is not None:
        dst_run.font.bold = src_run.font.bold
    if src_run.font.italic is not None:
        dst_run.font.italic = src_run.font.italic
    if hasattr(src_run.font.color, 'rgb') and src_run.font.color.rgb is not None:
        dst_run.font.color.rgb = src_run.font.color.rgb
    else:
        dst_run.font.color.rgb = get_inherited_font_color(shape, slide, presentation)

def copy_paragraph_formatting(src_paragraph, dst_paragraph):
    if src_paragraph.alignment is not None:
        dst_paragraph.alignment = src_paragraph.alignment
    else:
        dst_paragraph.alignment = PP_ALIGN.LEFT
    if src_paragraph.space_before is not None:
        dst_paragraph.space_before = src_paragraph.space_before
    if src_paragraph.space_after is not None:
        dst_paragraph.space_after = src_paragraph.space_after
    if src_paragraph.line_spacing is not None:
        dst_paragraph.line_spacing = src_paragraph.line_spacing
    if src_paragraph.level is not None:
        dst_paragraph.level = src_paragraph.level

def copy_text_frame_formatting(src_text_frame, dst_text_frame, shape, slide, presentation):
    dst_text_frame.clear()
    if src_text_frame.margin_left is not None:
        dst_text_frame.margin_left = src_text_frame.margin_left
    if src_text_frame.margin_right is not None:
        dst_text_frame.margin_right = src_text_frame.margin_right
    if src_text_frame.margin_top is not None:
        dst_text_frame.margin_top = src_text_frame.margin_top
    if src_text_frame.margin_bottom is not None:
        dst_text_frame.margin_bottom = src_text_frame.margin_bottom
    if src_text_frame.vertical_anchor is not None:
        dst_text_frame.vertical_anchor = src_text_frame.vertical_anchor
    dst_text_frame.word_wrap = src_text_frame.word_wrap if src_text_frame.word_wrap is not None else True

    for src_paragraph in src_text_frame.paragraphs:
        dst_paragraph = dst_text_frame.add_paragraph()
        copy_paragraph_formatting(src_paragraph, dst_paragraph)
        for src_run in src_paragraph.runs:
            if src_run.text:
                dst_run = dst_paragraph.add_run()
                dst_run.text = src_run.text
                copy_run_formatting(src_run, dst_run, shape, slide, presentation)

def add_text_box(slide, src_shape, slide_width, slide_height, scale_factor, presentation, image_positions=None):
    text_box = slide.shapes.add_textbox(
        left=src_shape.left,
        top=src_shape.top,
        width=src_shape.width,
        height=src_shape.height
    )
    text_frame = text_box.text_frame
    text_frame.word_wrap = True
    copy_text_frame_formatting(src_shape.text_frame, text_frame, src_shape, slide, presentation)

def add_image_to_slide(slide, image_path, left, top, width, height, slide_width, slide_height, scale_factor):
    slide.shapes.add_picture(image_path, int(left), int(top), width=int(width), height=int(height))

def take_screenshot_of_master(ppt_path, output_folder):
    try:
        ppt_path = os.path.abspath(ppt_path)
        print(f"[DEBUG] Opening PPT file for screenshot: {ppt_path}")

        if not os.path.exists(ppt_path):
            raise FileNotFoundError(f"PPT template not found: {ppt_path}")

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Windows path: use COM automation
        if WIN32_AVAILABLE:
            import pythoncom  # type: ignore
            import win32com.client  # type: ignore
            pythoncom.CoInitialize()
            ppt_app = win32com.client.Dispatch("PowerPoint.Application")
            ppt_app.Visible = True
            presentation = ppt_app.Presentations.Open(ppt_path, WithWindow=False)

            if presentation.Slides.Count < 1:
                raise Exception("No slides found in template PPT")
            slide = presentation.Slides(1)

            temp_image_path = os.path.join(output_folder, f"temp_{uuid.uuid4().hex[:8]}.png")
            temp_image_path = os.path.abspath(temp_image_path)
            slide.Export(temp_image_path, "PNG", 1280, 720)

            presentation.Close()
            ppt_app.Quit()
            pythoncom.CoUninitialize()

            if not os.path.exists(temp_image_path):
                raise Exception("Failed to export slide as image")
            print(f"[DEBUG] Slide screenshot exported (COM): {temp_image_path}")
            return temp_image_path

        # Non-Windows path: try LibreOffice if available
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if soffice:
            try:
                # Kill any existing LibreOffice processes to avoid conflicts
                try:
                    subprocess.run(["pkill", "-f", "soffice"], capture_output=True, timeout=5)
                    import time
                    time.sleep(1)  # Wait for process to terminate
                except:
                    pass
                
                # Convert all slides to PNGs, then pick the first
                cmd = [soffice, "--headless", "--convert-to", "png", "--outdir", output_folder, ppt_path]
                print(f"[DEBUG] Running LibreOffice export: {' '.join(cmd)}")
                
                # Run with timeout and better error handling
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=30,
                    env=dict(os.environ, HOME=os.path.expanduser("~"))
                )
                
                if result.returncode != 0:
                    print(f"[DEBUG] LibreOffice stderr: {result.stderr}")
                    print(f"[DEBUG] LibreOffice stdout: {result.stdout}")
                
                base = os.path.splitext(os.path.basename(ppt_path))[0]
                # Find a generated PNG (pick the first)
                candidates = [f for f in os.listdir(output_folder) if f.startswith(base) and f.lower().endswith('.png')]
                if candidates:
                    first_png = os.path.join(output_folder, sorted(candidates)[0])
                    print(f"[DEBUG] Slide screenshot exported (LibreOffice): {first_png}")
                    return first_png
                else:
                    print(f"[DEBUG] No PNG files found in {output_folder}")
                    print(f"[DEBUG] Files in directory: {os.listdir(output_folder)}")
            except subprocess.TimeoutExpired:
                print("[DEBUG] LibreOffice export timed out")
            except Exception as e:
                print(f"LibreOffice export failed: {e}")
                import traceback
                traceback.print_exc()

        # Fallback: no screenshot capability
        print("[WARN] No screenshot method available on this platform. Proceeding without template background.")
        print("[INFO] To enable LibreOffice background processing:")
        print("[INFO] 1. Go to System Preferences > Security & Privacy > Privacy")
        print("[INFO] 2. Select 'Full Disk Access' and add LibreOffice")
        print("[INFO] 3. Select 'Automation' and ensure LibreOffice has permissions")
        return None
    except Exception as e:
        print(f"Error taking template slide screenshot: {e}")
        try:
            if 'presentation' in locals():
                presentation.Close()
            if 'ppt_app' in locals():
                ppt_app.Quit()
            if WIN32_AVAILABLE:
                import pythoncom  # type: ignore
                pythoncom.CoUninitialize()
        except:
            pass
        return None

def generate_ppt(content_path, template_path, layout_index=1):
    try:
        print(f"Template path: {template_path}")
        print(f"Content path: {content_path}")
        print(f"Layout index: {layout_index}")

        if not os.path.exists(template_path):
            raise FileNotFoundError("Template file not found")
        if content_path and not os.path.exists(content_path):
            raise FileNotFoundError("Content file not found")

        screenshot_dir = os.path.join("Uploads", "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = take_screenshot_of_master(template_path, screenshot_dir)
        if not screenshot_path:
            print("[WARN] Failed to capture master slide screenshot. Continuing with template layouts (no screenshot background).")

        content_ppt = Presentation(content_path)
        template_ppt = Presentation(template_path)
        content_slide_width = content_ppt.slide_width
        content_slide_height = content_ppt.slide_height
        # If we couldn't take a screenshot, we still want to leverage the template's master/layouts
        if not screenshot_path:
            output_ppt = Presentation(template_path)
            # Remove any existing slides from the template so we add fresh ones with the same style
            for i in range(len(output_ppt.slides)-1, -1, -1):
                rId = output_ppt.slides._sldIdLst[i].rId
                output_ppt.part.drop_rel(rId)
                del output_ppt.slides._sldIdLst[i]
            print("[INFO] Using template background and layouts (no screenshot)")
        else:
            output_ppt = Presentation()
            print("[INFO] Using screenshot background")
        output_ppt.slide_width = content_slide_width
        output_ppt.slide_height = content_slide_height

        # Choose base layout: use provided layout_index if valid, else default
        try:
            base_idx = int(layout_index)
        except Exception:
            base_idx = None
        default_layout_index = 6 if len(output_ppt.slide_layouts) > 6 else 0
        if base_idx is not None and 0 <= base_idx < len(output_ppt.slide_layouts):
            base_layout = output_ppt.slide_layouts[base_idx]
        else:
            base_layout = output_ppt.slide_layouts[default_layout_index]
        print(f"Content PPT loaded with {len(content_ppt.slides)} slides")
        print(f"Content slide dimensions: {content_slide_width}x{content_slide_height}")
        print(f"Using layout index: {list(output_ppt.slide_layouts).index(base_layout)}")

        for slide_idx, slide in enumerate(content_ppt.slides):
            print(f"Processing slide {slide_idx + 1}")
            new_slide = output_ppt.slides.add_slide(base_layout)
            if screenshot_path and os.path.exists(screenshot_path):
                new_slide.shapes.add_picture(
                    screenshot_path, 
                    left=0, 
                    top=0, 
                    width=content_slide_width, 
                    height=content_slide_height
                )
                print(f"Added background image to slide {slide_idx + 1}")
            # If no screenshot, we rely on the template's background from the chosen layout
            # Remove default placeholders to avoid duplicates with copied content
            try:
                for shp in list(new_slide.shapes):
                    if getattr(shp, 'is_placeholder', False):
                        new_slide.shapes._spTree.remove(shp._element)
            except Exception:
                pass

            image_positions = []
            for shape in slide.shapes:
                if shape.shape_type == 13:
                    image_positions.append({
                        "left": shape.left,
                        "top": shape.top,
                        "width": shape.width,
                        "height": shape.height
                    })

            image_count = 0
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text and shape.text.strip():
                    add_text_box(new_slide, shape, content_slide_width, content_slide_height, 1.0, output_ppt, image_positions=image_positions)
                if shape.shape_type == 13:
                    image_count += 1
                    image_stream = shape.image.blob
                    image_filename = f"temp_image_{uuid.uuid4().hex[:8]}.png"
                    image_path = os.path.join("Uploads", "images", image_filename)
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    with open(image_path, 'wb') as f:
                        f.write(image_stream)
                    add_image_to_slide(
                        new_slide, image_path, 
                        shape.left, shape.top, 
                        shape.width, shape.height, 
                        content_slide_width, content_slide_height, 1.0
                    )
                    print(f"Added image to slide at adjusted position ({shape.left}, {shape.top})")

            print(f"Total images found in slide {slide_idx + 1}: {image_count}")

        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"generated_{uuid.uuid4().hex[:8]}.pptx")
        output_ppt.save(output_path)
        print(f"PPT saved to: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating PPT: {e}")
        raise Exception(f"Failed to generate PPT: {str(e)}")
    finally:
        try:
            if 'screenshot_path' in locals() and isinstance(screenshot_path, str) and screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except Exception as _cleanup_err:
            print(f"[WARN] Could not remove temp screenshot: {_cleanup_err}")

# ...rest of your code (extract_ppt_content, clean_template_ppt, refine_ppt, etc.) remains unchanged...
def extract_ppt_content(ppt_path):
    """Extract content from a PPT file as structured data."""
    ppt = Presentation(ppt_path)
    content = []
    for slide_idx, slide in enumerate(ppt.slides):
        slide_content = {"slide": slide_idx + 1, "shapes": []}
        for shape in slide.shapes:
            shape_data = {}
            if hasattr(shape, "text") and shape.text and shape.text.strip():
                shape_data["type"] = "text"
                shape_data["text"] = shape.text
                shape_data["position"] = {
                    "left": shape.left,
                    "top": shape.top,
                    "width": shape.width,
                    "height": shape.height
                }
                shape_data["formatting"] = []
                for paragraph in shape.text_frame.paragraphs:
                    para_data = {
                        "alignment": paragraph.alignment.value if paragraph.alignment else None,
                        "level": paragraph.level if paragraph.level is not None else 0
                    }
                    runs = []
                    for run in paragraph.runs:
                        run_data = {
                            "text": run.text,
                            "bold": run.font.bold if run.font.bold is not None else False,
                            "italic": run.font.italic if run.font.italic is not None else False,
                            "size": run.font.size.pt if run.font.size else None,
                            "color": str(run.font.color.rgb) if hasattr(run.font.color, 'rgb') and run.font.color.rgb else None
                        }
                        runs.append(run_data)
                    para_data["runs"] = runs
                    shape_data["formatting"].append(para_data)
            elif shape.shape_type == 13:
                shape_data["type"] = "image"
                shape_data["position"] = {
                    "left": shape.left,
                    "top": shape.top,
                    "width": shape.width,
                    "height": shape.height
                }
            if shape_data:
                slide_content["shapes"].append(shape_data)
        content.append(slide_content)
    return content

def clean_template_ppt(template_ppt):
    """Clean duplicate slide layouts, slide masters, themes, and media in the template PPT."""
    seen_layouts = set()
    seen_masters = set()
    seen_themes = set()
    seen_media = set()

    slide_layouts = list(template_ppt.slide_layouts)
    layout_ids_to_remove = []
    for layout in slide_layouts:
        layout_name = layout.name
        if layout_name in seen_layouts:
            layout_ids_to_remove.append(layout)
        else:
            seen_layouts.add(layout_name)
    
    for layout in layout_ids_to_remove:
        for r_id in list(template_ppt.part.rels.keys()):
            if template_ppt.part.rels[r_id].target_part == layout.part:
                template_ppt.part.drop_rel(r_id)
                break
        for sld_layout_id in template_ppt.slide_master.slide_layouts._sldLayoutIdLst:
            if sld_layout_id.rId == template_ppt.part.rels.get_id_of_part(layout.part):
                template_ppt.slide_master.slide_layouts._sldLayoutIdLst.remove(sld_layout_id)
                break
        if layout.part in template_ppt.part.related_parts.values():
            layout_part = layout.part
            template_ppt.part.package.drop_part(layout_part)

    slide_masters = list(template_ppt.slide_masters)
    master_ids_to_remove = []
    for master in slide_masters:
        master_name = master.name if hasattr(master, 'name') else str(id(master))
        if master_name in seen_masters:
            master_ids_to_remove.append(master)
        else:
            seen_masters.add(master_name)

    for master in master_ids_to_remove:
        for r_id in list(template_ppt.part.rels.keys()):
            if template_ppt.part.rels[r_id].target_part == master.part:
                template_ppt.part.drop_rel(r_id)
                break
        for sld_master_id in template_ppt.slide_masters._sldMasterIdLst:
            if sld_master_id.rId == template_ppt.part.rels.get_id_of_part(master.part):
                template_ppt.slide_masters._sldMasterIdLst.remove(sld_master_id)
                break
        if master.part in template_ppt.part.related_parts.values():
            master_part = master.part
            template_ppt.part.package.drop_part(master_part)

    themes = []
    for rel in template_ppt.part.rels.values():
        if rel.target_part.partname.startswith('/ppt/theme/theme'):
            themes.append(rel.target_part)
    
    for theme in themes[1:]:
        theme_name = theme.partname
        if theme_name in seen_themes:
            for r_id in list(template_ppt.part.rels.keys()):
                if template_ppt.part.rels[r_id].target_part == theme:
                    template_ppt.part.drop_rel(r_id)
                    break
            if theme in template_ppt.part.related_parts.values():
                template_ppt.part.package.drop_part(theme)
        else:
            seen_themes.add(theme_name)

    for slide in template_ppt.slides:
        for shape in slide.shapes:
            if shape.shape_type == 13:
                image_part = shape.image.part
                image_name = image_part.partname
                if image_name in seen_media:
                    new_image_name = f"/ppt/media/image_{uuid.uuid4().hex[:8]}.{image_name.split('.')[-1]}"
                    image_part.partname = new_image_name
                seen_media.add(image_part.partname)


def fill_template_with_ai_content(template_path, slides_content):
    prs = Presentation(template_path)
    layout_index = 6 if len(prs.slide_layouts) > 6 else 0
    blank_layout = prs.slide_layouts[layout_index]
    # Remove existing slides
    for i in range(len(prs.slides)-1, -1, -1):
        rId = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[i]
    # Add AI slides
    for slide in slides_content:
        s = prs.slides.add_slide(blank_layout)
        txBox = s.shapes.add_textbox(Pt(100), Pt(100), Pt(700), Pt(400))
        tf = txBox.text_frame
        tf.text = slide['title']
        for bullet in slide['bullets']:
            p = tf.add_paragraph()
            p.text = bullet
            p.level = 1
    output_path = os.path.join("outputs", f"ai_generated_{uuid.uuid4().hex[:8]}.pptx")
    prs.save(output_path)
    return output_path

def fix_text_contrast_in_ppt(ppt_path):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.util import Inches
    import os

    def get_bg_brightness(slide, slide_width, slide_height):
        # Check for large image as background (assume light)
        for shape in slide.shapes:
            if shape.shape_type == 13:
                if (shape.left < Inches(0.5) and shape.top < Inches(0.5) and 
                    shape.width > slide_width * 0.8 and shape.height > slide_height * 0.8):
                    return 255  # Assume white bg for most templates
        # Check background fill safely (guard _NoFill)
        try:
            if hasattr(slide, 'background') and hasattr(slide.background, 'fill') and slide.background.fill:
                fill = slide.background.fill
                if hasattr(fill, 'fore_color'):
                    try:
                        fc = fill.fore_color
                        if getattr(fc, 'rgb', None):
                            r, g, b = fc.rgb
                            brightness = (r + g + b) / 3
                            return brightness
                    except Exception:
                        pass
        except Exception:
            pass
        return 255  # Default: white

    def get_text_brightness(rgb):
        if rgb is None:
            return 0
        r, g, b = rgb
        return (r + g + b) / 3

    prs = Presentation(ppt_path)
    slide_width = prs.slide_width
    slide_height = prs.slide_height
    changed = False
    for slide in prs.slides:
        bg_brightness = get_bg_brightness(slide, slide_width, slide_height)
        for shape in slide.shapes:
            if hasattr(shape, 'has_text_frame') and shape.has_text_frame and shape.text_frame.text.strip():
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        # Only adjust explicit colors
                        if getattr(run, 'font', None) and getattr(run.font, 'color', None) and getattr(run.font.color, 'rgb', None):
                            color = run.font.color.rgb
                            text_brightness = get_text_brightness(color)
                            if bg_brightness > 200 and text_brightness > 180:
                                run.font.color.rgb = RGBColor(0, 0, 0)
                                changed = True
                            elif bg_brightness < 80 and text_brightness < 100:
                                run.font.color.rgb = RGBColor(255, 255, 255)
                                changed = True
    if changed:
        out_path = os.path.join("outputs", f"contrast_fixed_{os.path.basename(ppt_path)}")
        prs.save(out_path)
        return out_path
    else:
        return ppt_path

def refine_ppt(converted_path, content_path, api_url, api_key):
    import shutil
    import os
    # Copy converted ppt as is
    temp_path = os.path.join("outputs", f"temp_{os.path.basename(converted_path)}")
    shutil.copyfile(converted_path, temp_path)
    # Fix color contrast
    out_path = fix_text_contrast_in_ppt(temp_path)
    return out_path

def generate_enhanced_ppt(slides_content, template_path=None, layout_preference="auto"):
    """
    Enhanced PPT generation with proper layout handling, text fitting, and template preservation.
    """
    if template_path and os.path.exists(template_path):
        prs = Presentation(template_path)
        # Clear existing slides but keep template structure (masters, themes, backgrounds)
        for i in range(len(prs.slides)-1, -1, -1):
            rId = prs.slides._sldIdLst[i].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[i]
    else:
        prs = Presentation()
    
    slide_width = prs.slide_width
    slide_height = prs.slide_height
    
    for i, slide_data in enumerate(slides_content):
        # Determine layout based on preference and slide type
        layout_type = determine_layout_type(slide_data, layout_preference, i)
        
        # Create slide - use blank layout for full control but PRESERVE template background
        layout_idx = 6 if len(prs.slide_layouts) > 6 else 0
        # Try to find blank layout
        for li, sl in enumerate(prs.slide_layouts):
            if sl.name and 'blank' in sl.name.lower():
                layout_idx = li
                break
        slide = prs.slides.add_slide(prs.slide_layouts[layout_idx])
        
        # Remove default placeholder shapes (but keep background elements from template)
        for shp in list(slide.shapes):
            if getattr(shp, 'is_placeholder', False):
                try:
                    slide.shapes._spTree.remove(shp._element)
                except:
                    pass
        
        # Add content with proper fitting
        add_content_to_slide(slide, slide_data, layout_type, slide_width, slide_height)
    
    # Save the presentation
    output_filename = f"enhanced_ai_pptx_{uuid.uuid4().hex[:8]}.pptx"
    output_path = os.path.join("outputs", output_filename)
    os.makedirs("outputs", exist_ok=True)
    prs.save(output_path)
    
    return output_path

def determine_layout_type(slide_data, layout_preference, slide_index):
    """
    Determine the best layout type for a slide.
    Respects user preference, falls back to smart auto-detection.
    """
    # If user picked a specific layout, use it (except for title slide)
    if layout_preference != "auto":
        # First slide is always title-content style
        if slide_index == 0:
            return "title_slide"
        return layout_preference.replace("-", "_")
    
    # Auto mode: pick based on content
    title = slide_data.get("title", "").lower()
    bullets = slide_data.get("bullets", [])
    has_image = bool(slide_data.get("image_desc"))

    # First slide = title slide
    if slide_index == 0:
        return "title_slide"
    
    # Check for conclusion/summary keywords
    if any(kw in title for kw in ["conclusion", "summary", "takeaway", "thank", "end"]):
        return "title_content"
    
    # If image hint present, alternate between image-left and image-right
    if has_image:
        if slide_index % 2 == 1:
            return "image_left"
        else:
            return "image_right"
    
    # Many bullets -> two columns
    if len(bullets) > 5:
        return "two_column"
    
    return "title_content"

def _fit_font_size(text_items, max_width_emu, max_height_emu, base_size_pt=18, min_size_pt=10):
    """
    Calculate font size that fits text within the given box dimensions.
    Returns font size in Pt.
    """
    if not text_items:
        return Pt(base_size_pt)
    
    total_chars = sum(len(str(t)) for t in text_items)
    num_lines = len(text_items)
    
    # Rough estimate: each character is ~60% of font height wide
    # Available width in characters at base size
    char_width_ratio = 0.55
    
    # Convert EMU to points (1 inch = 914400 EMU, 1 inch = 72 points)
    max_width_pt = max_width_emu * 72.0 / 914400.0
    max_height_pt = max_height_emu * 72.0 / 914400.0
    
    # Try from base_size down
    for size in range(base_size_pt, min_size_pt - 1, -1):
        chars_per_line = max_width_pt / (size * char_width_ratio)
        # Count total lines needed (with word wrap)
        total_lines = 0
        for item in text_items:
            lines_needed = max(1, int(len(str(item)) / max(1, chars_per_line)) + 1)
            total_lines += lines_needed
        
        line_height = size * 1.5  # 1.5x line spacing
        total_height_needed = total_lines * line_height
        
        if total_height_needed <= max_height_pt:
            return Pt(size)
    
    return Pt(min_size_pt)

def add_content_to_slide(slide, slide_data, layout_type, slide_width, slide_height):
    """
    Add content to slide with proper fitting based on layout type.
    """
    title = slide_data.get("title", "")
    bullets = slide_data.get("bullets", [])
    image_desc = slide_data.get("image_desc", "")
    theme = slide_data.get("theme", ["#1a365d", "#e2e8f0"])
    
    # Fetch image if description provided
    image_path = None
    if image_desc:
        try:
            image_path = fetch_image_from_unsplash(image_desc)
        except Exception as e:
            print(f"Image fetch failed for '{image_desc}': {e}")
    
    if layout_type == "title_slide":
        _add_title_slide(slide, title, bullets, image_path, theme, slide_width, slide_height)
    elif layout_type == "title_content":
        _add_title_content(slide, title, bullets, theme, slide_width, slide_height)
    elif layout_type == "image_left":
        _add_image_side(slide, title, bullets, image_path, theme, slide_width, slide_height, image_on_left=True)
    elif layout_type == "image_right":
        _add_image_side(slide, title, bullets, image_path, theme, slide_width, slide_height, image_on_left=False)
    elif layout_type == "full_image":
        _add_full_image(slide, title, bullets, image_path, theme, slide_width, slide_height)
    elif layout_type == "two_column":
        _add_two_column(slide, title, bullets, theme, slide_width, slide_height)
    else:
        # Fallback
        _add_title_content(slide, title, bullets, theme, slide_width, slide_height)

def _get_text_color(slide, slide_width, slide_height, theme):
    """Get appropriate text color based on background contrast."""
    contrast_type = get_contrast_text_color(slide, slide_width, slide_height)
    return get_text_color_for_contrast(contrast_type, theme)

def _add_title_slide(slide, title, bullets, image_path, theme, slide_width, slide_height):
    """Title/intro slide with centered large title and optional subtitle bullets."""
    # Add background image if available
    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, 0, 0, slide_width, slide_height)
        # Add dark overlay for readability
        overlay = slide.shapes.add_shape(1, 0, 0, slide_width, slide_height)
        overlay.fill.solid()
        overlay.fill.fore_color.rgb = RGBColor(0, 0, 0)
        try:
            overlay.fill.transparency = 0.45
        except:
            pass
        overlay.line.fill.background()
        text_color = RGBColor(255, 255, 255)
    else:
        text_color = _get_text_color(slide, slide_width, slide_height, theme)
    
    # Title: centered vertically
    margin_h = Inches(1.2)
    title_box = slide.shapes.add_textbox(
        int(margin_h), int(slide_height * 0.25),
        int(slide_width - 2 * margin_h), int(slide_height * 0.3)
    )
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(40)
        run.font.bold = True
        run.font.color.rgb = text_color
    
    # Subtitle bullets (first 2-3 bullets as overview)
    if bullets:
        subtitle_text = " | ".join(bullets[:3])
        sub_box = slide.shapes.add_textbox(
            int(margin_h), int(slide_height * 0.58),
            int(slide_width - 2 * margin_h), int(slide_height * 0.2)
        )
        sf = sub_box.text_frame
        sf.clear()
        sf.word_wrap = True
        sf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        sf.text = subtitle_text
        sp = sf.paragraphs[0]
        sp.alignment = PP_ALIGN.CENTER
        for run in sp.runs:
            run.font.size = Pt(16)
            run.font.bold = False
            run.font.color.rgb = text_color

def _add_title_content(slide, title, bullets, theme, slide_width, slide_height):
    """Standard title + bullet points layout with auto-fitting text."""
    text_color = _get_text_color(slide, slide_width, slide_height, theme)
    
    margin_h = Inches(0.8)
    margin_v = Inches(0.5)
    content_width = slide_width - 2 * int(margin_h)
    
    # Title box at top
    title_height = int(slide_height * 0.18)
    title_box = slide.shapes.add_textbox(
        int(margin_h), int(margin_v), content_width, title_height
    )
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for run in p.runs:
        run.font.size = Pt(32)
        run.font.bold = True
        run.font.color.rgb = text_color
    
    # Divider line
    divider_top = int(margin_v) + title_height + int(Inches(0.1))
    div = slide.shapes.add_shape(
        1, int(margin_h), divider_top,
        int(content_width * 0.3), Inches(0.04)
    )
    try:
        primary_color = theme[0] if theme else "#1a365d"
        r, g, b = int(primary_color[1:3], 16), int(primary_color[3:5], 16), int(primary_color[5:7], 16)
        div.fill.solid()
        div.fill.fore_color.rgb = RGBColor(r, g, b)
        div.line.fill.background()
    except:
        pass

    # Bullets box
    bullets_top = divider_top + int(Inches(0.25))
    bullets_height = slide_height - bullets_top - int(margin_v)
    
    # Calculate adaptive font size
    body_font = _fit_font_size(bullets, content_width, bullets_height, base_size_pt=20, min_size_pt=12)
    
    bullets_box = slide.shapes.add_textbox(
        int(margin_h), bullets_top, content_width, bullets_height
    )
    bf = bullets_box.text_frame
    bf.clear()
    bf.word_wrap = True
    bf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    for idx, bullet in enumerate(bullets or []):
        p = bf.add_paragraph() if idx > 0 else bf.paragraphs[0]
        p.text = f"\u2022  {bullet}"
        p.level = 0
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        p.space_before = Pt(2)
        for run in p.runs:
            run.font.size = body_font
            run.font.bold = False
            run.font.color.rgb = text_color

def _add_image_side(slide, title, bullets, image_path, theme, slide_width, slide_height, image_on_left=True):
    """Layout with image on one side and text on the other. Handles aspect ratio properly."""
    text_color = _get_text_color(slide, slide_width, slide_height, theme)
    
    margin = Inches(0.4)
    gap = Inches(0.3)
    top_margin = Inches(0.4)
    bottom_margin = Inches(0.4)
    
    # Image takes 42% width, text takes remaining
    img_width_max = int(slide_width * 0.42)
    img_height_max = slide_height - int(top_margin) - int(bottom_margin)
    text_width = slide_width - img_width_max - int(margin) - int(gap)
    
    # Place image with proper aspect ratio
    actual_img_width = img_width_max
    actual_img_height = img_height_max
    
    if image_path and os.path.exists(image_path):
        try:
            with Image.open(image_path) as im:
                aspect = im.width / im.height if im.height else 1.0
        except:
            aspect = 16/9
        
        # Fit within bounds maintaining aspect ratio
        w = img_width_max
        h = int(w / aspect)
        if h > img_height_max:
            h = img_height_max
            w = int(h * aspect)
        actual_img_width = w
        actual_img_height = h
        
        if image_on_left:
            img_left = int(margin)
        else:
            img_left = slide_width - int(margin) - actual_img_width
        
        # Center vertically
        img_top = int(top_margin) + max(0, (img_height_max - actual_img_height) // 2)
        
        # Add rounded corner effect by adding image
        slide.shapes.add_picture(
            image_path, img_left, img_top,
            width=actual_img_width, height=actual_img_height
        )
    
    # Text region
    if image_on_left:
        text_left = int(margin) + actual_img_width + int(gap)
    else:
        text_left = int(margin)
    
    text_top = int(top_margin)
    text_height = slide_height - int(top_margin) - int(bottom_margin)
    
    # Title
    title_height = int(text_height * 0.2)
    title_box = slide.shapes.add_textbox(text_left, text_top, text_width, title_height)
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    for run in p.runs:
        run.font.size = Pt(26)
        run.font.bold = True
        run.font.color.rgb = text_color
    
    # Bullets
    bullets_top = text_top + title_height + int(Inches(0.15))
    bullets_height = text_height - title_height - int(Inches(0.15))
    
    body_font = _fit_font_size(bullets, text_width, bullets_height, base_size_pt=16, min_size_pt=10)
    
    bullets_box = slide.shapes.add_textbox(text_left, bullets_top, text_width, bullets_height)
    bf = bullets_box.text_frame
    bf.clear()
    bf.word_wrap = True
    bf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    for idx, bullet in enumerate(bullets or []):
        p = bf.add_paragraph() if idx > 0 else bf.paragraphs[0]
        p.text = f"\u2022  {bullet}"
        p.level = 0
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(6)
        for run in p.runs:
            run.font.size = body_font
            run.font.bold = False
            run.font.color.rgb = text_color

def _add_full_image(slide, title, bullets, image_path, theme, slide_width, slide_height):
    """Full background image with semi-transparent text overlay strip at bottom."""
    # Background image
    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, 0, 0, slide_width, slide_height)
    
    # Semi-transparent dark strip at bottom
    strip_height = int(slide_height * 0.38)
    strip_top = slide_height - strip_height - int(Inches(0.3))
    strip_left = int(slide_width * 0.06)
    strip_width = int(slide_width * 0.88)
    
    text_bg = slide.shapes.add_shape(1, strip_left, strip_top, strip_width, strip_height)
    text_bg.fill.solid()
    text_bg.fill.fore_color.rgb = RGBColor(0, 0, 0)
    try:
        text_bg.fill.transparency = 0.65
    except:
        pass
    text_bg.line.fill.background()
    
    text_color = RGBColor(255, 255, 255)
    
    inner_margin = int(strip_width * 0.05)
    inner_left = strip_left + inner_margin
    inner_width = strip_width - 2 * inner_margin
    
    # Title inside strip
    title_h = int(strip_height * 0.25)
    title_box = slide.shapes.add_textbox(
        inner_left, strip_top + int(strip_height * 0.06),
        inner_width, title_h
    )
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(28)
        run.font.bold = True
        run.font.color.rgb = text_color
    
    # Bullets inside strip
    bullets_top = strip_top + int(strip_height * 0.06) + title_h + int(strip_height * 0.04)
    bullets_h = strip_top + strip_height - bullets_top - int(strip_height * 0.06)
    
    body_font = _fit_font_size(bullets, inner_width, bullets_h, base_size_pt=16, min_size_pt=10)
    
    bul_box = slide.shapes.add_textbox(inner_left, bullets_top, inner_width, bullets_h)
    bf = bul_box.text_frame
    bf.clear()
    bf.word_wrap = True
    bf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    
    for idx, bullet in enumerate(bullets or []):
        p = bf.add_paragraph() if idx > 0 else bf.paragraphs[0]
        p.text = f"\u2022  {bullet}"
        p.level = 0
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(4)
        for run in p.runs:
            run.font.size = body_font
            run.font.bold = False
            run.font.color.rgb = text_color

def _add_two_column(slide, title, bullets, theme, slide_width, slide_height):
    """Two-column layout with title on top and bullets split into two columns."""
    text_color = _get_text_color(slide, slide_width, slide_height, theme)
    
    margin_h = Inches(0.8)
    margin_v = Inches(0.5)
    gap = Inches(0.5)
    content_width = slide_width - 2 * int(margin_h)
    
    # Title
    title_height = int(slide_height * 0.18)
    title_box = slide.shapes.add_textbox(int(margin_h), int(margin_v), content_width, title_height)
    tf = title_box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.text = title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    for run in p.runs:
        run.font.size = Pt(30)
        run.font.bold = True
        run.font.color.rgb = text_color
    
    # Divider
    div_top = int(margin_v) + title_height + int(Inches(0.1))
    div = slide.shapes.add_shape(
        1, int(margin_h) + int(content_width * 0.35), div_top,
        int(content_width * 0.3), Inches(0.04)
    )
    try:
        primary_color = theme[0] if theme else "#1a365d"
        r, g, b = int(primary_color[1:3], 16), int(primary_color[3:5], 16), int(primary_color[5:7], 16)
        div.fill.solid()
        div.fill.fore_color.rgb = RGBColor(r, g, b)
        div.line.fill.background()
    except:
        pass
    
    # Split bullets
    mid = (len(bullets) + 1) // 2
    left_bullets = bullets[:mid]
    right_bullets = bullets[mid:]
    
    col_top = div_top + int(Inches(0.3))
    col_height = slide_height - col_top - int(margin_v)
    col_width = (content_width - int(gap)) // 2
    
    body_font = _fit_font_size(left_bullets or right_bullets, col_width, col_height, base_size_pt=16, min_size_pt=10)
    
    def add_column(left_pos, column_bullets):
        box = slide.shapes.add_textbox(left_pos, col_top, col_width, col_height)
        bf = box.text_frame
        bf.clear()
        bf.word_wrap = True
        bf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
        for idx, bullet in enumerate(column_bullets or []):
            p = bf.add_paragraph() if idx > 0 else bf.paragraphs[0]
            p.text = f"\u2022  {bullet}"
            p.level = 0
            p.alignment = PP_ALIGN.LEFT
            p.space_after = Pt(6)
            for run in p.runs:
                run.font.size = body_font
                run.font.bold = False
                run.font.color.rgb = text_color
    
    # Left column
    add_column(int(margin_h), left_bullets)
    # Right column
    add_column(int(margin_h) + col_width + int(gap), right_bullets)
