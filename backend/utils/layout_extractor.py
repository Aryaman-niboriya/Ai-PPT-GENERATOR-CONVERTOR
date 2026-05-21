from pptx import Presentation
import os

def extract_layouts(template_path):
    try:
        # Check if file exists and is accessible
        if not os.path.exists(template_path):
            raise FileNotFoundError("Template file not found on server")
        
        prs = Presentation(template_path)
        layout_names = []
        seen_layouts = set()  # To track unique layouts and avoid duplicates
        
        for i, layout in enumerate(prs.slide_layouts):
            name = layout.name if layout.name else f"Layout {i}"
            # Avoid adding duplicate layout names
            if name not in seen_layouts:
                layout_names.append({"index": i, "name": name})
                seen_layouts.add(name)
            else:
                print(f"Skipping duplicate layout: {name}")
        
        if not layout_names:
            print("No layouts found in template")
            return [{"index": 0, "name": "No layouts found in template"}]
        
        print(f"Extracted {len(layout_names)} unique layouts")
        return layout_names
    except FileNotFoundError as e:
        print(f"Error extracting layouts: {e}")
        return [{"index": 0, "name": f"Error: Template file not found"}]
    except Exception as e:
        print(f"Error extracting layouts: {e}")
        return [{"index": 0, "name": f"Error: Invalid or corrupted PPT file"}]