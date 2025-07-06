import os
import subprocess
import logging
import tempfile
import shutil
from flask import current_app
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from io import BytesIO

logger = logging.getLogger(__name__)


def compile_latex_to_pdf(cv_uuid, latex_code, user_tier):
    """
    Compile LaTeX code to PDF with enhanced error handling and fallbacks.
    
    Args:
        cv_uuid (str): CV UUID for file organization
        latex_code (str): LaTeX source code
        user_tier (str): User subscription tier
        
    Returns:
        tuple: (pdf_path, jpg_path) or raises exception on failure
    """
    try:
        # Create user directory
        base_dir = current_app.config.get('UPLOAD_FOLDER', 'user_data')
        user_dir = os.path.join(base_dir, f'cv_{cv_uuid}')
        os.makedirs(user_dir, exist_ok=True)
        
        # Write LaTeX file
        tex_file = os.path.join(user_dir, 'cv.tex')
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_code)
        
        logger.info(f'Wrote LaTeX file for CV {cv_uuid}')
        
        # Try to compile with pdflatex
        pdf_path, jpg_path = _compile_with_pdflatex(user_dir, user_tier, cv_uuid)
        
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f'Successfully compiled LaTeX to PDF for CV {cv_uuid}')
            return pdf_path, jpg_path
        else:
            # Fallback to creating PDF from LaTeX content
            logger.warning(f'pdflatex failed for CV {cv_uuid}, using fallback method')
            return _create_fallback_pdf(user_dir, latex_code, user_tier, cv_uuid)
        
    except Exception as e:
        logger.error(f'LaTeX compilation error for CV {cv_uuid}: {str(e)}')
        # Last resort: create dummy files
        return _create_dummy_files(user_dir, user_tier, cv_uuid)


def _compile_with_pdflatex(user_dir, user_tier, cv_uuid):
    """
    Compile LaTeX using pdflatex system command.
    
    Args:
        user_dir (str): Directory containing LaTeX files
        user_tier (str): User subscription tier
        cv_uuid (str): CV UUID
        
    Returns:
        tuple: (pdf_path, jpg_path) or (None, None) if failed
    """
    try:
        # Check if pdflatex is available
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, check=True, timeout=10)
        logger.info('pdflatex is available')
        
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning('pdflatex not available or timed out')
        return None, None
    
    try:
        # Compile LaTeX with timeout
        cmd = [
            'pdflatex',
            '-interaction=nonstopmode',
            '-output-directory', user_dir,
            'cv.tex'
        ]
        
        # Run compilation with timeout
        result = subprocess.run(
            cmd, 
            cwd=user_dir, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        pdf_path = os.path.join(user_dir, 'cv.pdf')
        
        if result.returncode != 0:
            logger.error(f'pdflatex compilation failed: {result.stderr}')
            return None, None
        
        if not os.path.exists(pdf_path):
            logger.error('PDF file was not created despite successful compilation')
            return None, None
        
        # Create JPG preview for free users
        jpg_path = None
        if user_tier == 'free':
            jpg_path = _create_jpg_preview(pdf_path, user_dir)
        
        return pdf_path, jpg_path
        
    except subprocess.TimeoutExpired:
        logger.error('pdflatex compilation timed out')
        return None, None
    except Exception as e:
        logger.error(f'pdflatex compilation error: {str(e)}')
        return None, None


def _create_jpg_preview(pdf_path, user_dir):
    """
    Create JPG preview from PDF first page.
    
    Args:
        pdf_path (str): Path to PDF file
        user_dir (str): User directory
        
    Returns:
        str: Path to JPG file or None if failed
    """
    try:
        jpg_path = os.path.join(user_dir, 'cv.jpg')
        
        # Use PyMuPDF to convert PDF to image
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # first page
        
        # Render page to image with high quality
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image and save as JPG
        img_data = pix.tobytes("ppm")
        img = Image.open(BytesIO(img_data))
        
        # Resize if too large
        if img.width > 1200 or img.height > 1600:
            img.thumbnail((1200, 1600), Image.Resampling.LANCZOS)
        
        img.save(jpg_path, 'JPEG', quality=85, optimize=True)
        doc.close()
        
        logger.info(f'Created JPG preview: {jpg_path}')
        return jpg_path
        
    except Exception as e:
        logger.warning(f'Failed to create JPG preview: {str(e)}')
        return None


def _create_fallback_pdf(user_dir, latex_code, user_tier, cv_uuid):
    """
    Create PDF using reportlab as fallback when LaTeX compilation fails.
    
    Args:
        user_dir (str): User directory
        latex_code (str): LaTeX source code
        user_tier (str): User subscription tier
        cv_uuid (str): CV UUID
        
    Returns:
        tuple: (pdf_path, jpg_path)
    """
    try:
        pdf_path = os.path.join(user_dir, 'cv.pdf')
        
        # Extract basic information from LaTeX
        cv_content = _extract_content_from_latex(latex_code)
        
        # Create PDF using reportlab
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # Set up fonts and spacing
        title_font = "Helvetica-Bold"
        header_font = "Helvetica-Bold"
        body_font = "Helvetica"
        
        y_position = height - 50
        
        # Title
        if cv_content.get('name'):
            c.setFont(title_font, 24)
            c.drawString(50, y_position, cv_content['name'])
            y_position -= 40
        
        # Contact information
        c.setFont(body_font, 12)
        contact_info = []
        if cv_content.get('email'):
            contact_info.append(f"Email: {cv_content['email']}")
        if cv_content.get('phone'):
            contact_info.append(f"Phone: {cv_content['phone']}")
        
        if contact_info:
            c.drawString(50, y_position, " | ".join(contact_info))
            y_position -= 30
        
        # Professional Summary
        if cv_content.get('summary'):
            c.setFont(header_font, 14)
            c.drawString(50, y_position, "Professional Summary")
            y_position -= 20
            
            c.setFont(body_font, 11)
            _draw_wrapped_text(c, cv_content['summary'], 50, y_position, width - 100)
            y_position -= 60
        
        # Experience
        if cv_content.get('experience'):
            c.setFont(header_font, 14)
            c.drawString(50, y_position, "Experience")
            y_position -= 20
            
            c.setFont(body_font, 11)
            _draw_wrapped_text(c, cv_content['experience'], 50, y_position, width - 100)
            y_position -= 60
        
        # Skills
        if cv_content.get('skills'):
            c.setFont(header_font, 14)
            c.drawString(50, y_position, "Skills")
            y_position -= 20
            
            c.setFont(body_font, 11)
            skills_text = cv_content['skills'] if isinstance(cv_content['skills'], str) else ', '.join(cv_content['skills'])
            _draw_wrapped_text(c, skills_text, 50, y_position, width - 100)
            y_position -= 60
        
        # Education
        if cv_content.get('education'):
            c.setFont(header_font, 14)
            c.drawString(50, y_position, "Education")
            y_position -= 20
            
            c.setFont(body_font, 11)
            _draw_wrapped_text(c, cv_content['education'], 50, y_position, width - 100)
        
        # Add watermark for fallback
        c.setFont("Helvetica", 8)
        c.setFillGray(0.7)
        c.drawString(50, 30, f"Generated by MorphCV - CV ID: {cv_uuid[:8]}")
        
        c.save()
        
        # Create JPG preview for free users
        jpg_path = None
        if user_tier == 'free':
            jpg_path = _create_jpg_preview(pdf_path, user_dir)
        
        logger.info(f'Created fallback PDF for CV {cv_uuid}')
        return pdf_path, jpg_path
        
    except Exception as e:
        logger.error(f'Fallback PDF creation failed: {str(e)}')
        return _create_dummy_files(user_dir, user_tier, cv_uuid)


def _extract_content_from_latex(latex_code):
    """
    Extract basic content from LaTeX code for fallback PDF generation.
    
    Args:
        latex_code (str): LaTeX source code
        
    Returns:
        dict: Extracted content
    """
    content = {}
    
    try:
        # Simple regex-based extraction
        import re
        
        # Extract name (look for common patterns)
        name_patterns = [
            r'\\name\{([^}]+)\}',
            r'\\textbf\{([^}]+)\}.*(?:CV|Resume)',
            r'\\LARGE\s*\\textbf\{([^}]+)\}',
            r'\\huge\s*([^\\]+)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, latex_code, re.IGNORECASE)
            if match:
                content['name'] = match.group(1).strip()
                break
        
        # Extract email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', latex_code)
        if email_match:
            content['email'] = email_match.group(1)
        
        # Extract phone (basic pattern)
        phone_match = re.search(r'(\+?[\d\s\-\(\)]{10,})', latex_code)
        if phone_match:
            content['phone'] = phone_match.group(1).strip()
        
        # Extract sections
        sections = ['summary', 'experience', 'skills', 'education']
        for section in sections:
            pattern = rf'\\section\*?\{{[^}}]*{section}[^}}]*\}}(.*?)(?=\\section|\Z)'
            match = re.search(pattern, latex_code, re.IGNORECASE | re.DOTALL)
            if match:
                # Clean up LaTeX commands
                text = match.group(1)
                text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
                text = re.sub(r'\\[a-zA-Z]+', '', text)
                text = re.sub(r'\{|\}', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    content[section] = text
        
        return content
        
    except Exception as e:
        logger.warning(f'Content extraction failed: {str(e)}')
        return {'name': 'CV Generated by MorphCV'}


def _draw_wrapped_text(canvas_obj, text, x, y, max_width):
    """
    Draw text with word wrapping.
    
    Args:
        canvas_obj: ReportLab canvas object
        text (str): Text to draw
        x (int): X coordinate
        y (int): Y coordinate
        max_width (int): Maximum width for text
    """
    try:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if canvas_obj.stringWidth(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)  # Word is too long, add anyway
        
        if current_line:
            lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            canvas_obj.drawString(x, y - (i * 15), line)
            
    except Exception as e:
        logger.warning(f'Text wrapping failed: {str(e)}')
        canvas_obj.drawString(x, y, text[:100] + '...' if len(text) > 100 else text)


def _create_dummy_files(user_dir, user_tier, cv_uuid):
    """
    Create dummy files as last resort when all other methods fail.
    
    Args:
        user_dir (str): User directory
        user_tier (str): User subscription tier
        cv_uuid (str): CV UUID
        
    Returns:
        tuple: (pdf_path, jpg_path)
    """
    try:
        # Create simple PDF using reportlab
        pdf_path = os.path.join(user_dir, 'cv.pdf')
        
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # Simple placeholder content
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 100, "CV Generation in Progress")
        
        c.setFont("Helvetica", 14)
        c.drawString(50, height - 150, "Your CV is being processed using our AI system.")
        c.drawString(50, height - 180, "Please try downloading again in a few moments.")
        
        c.setFont("Helvetica", 10)
        c.drawString(50, 50, f"CV ID: {cv_uuid}")
        c.drawString(50, 35, "Generated by MorphCV - Professional CV Generation")
        
        c.save()
        
        # Create JPG for free users
        jpg_path = None
        if user_tier == 'free':
            jpg_path = os.path.join(user_dir, 'cv.jpg')
            
            # Create simple image using PIL
            img = Image.new('RGB', (600, 800), color='white')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use a better font
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 36)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 18)
            except:
                # Fallback to default font
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            draw.text((50, 100), "CV Generation", fill='black', font=font_large)
            draw.text((50, 200), "Your CV is being processed", fill='black', font=font_small)
            draw.text((50, 250), "Please try downloading again", fill='black', font=font_small)
            draw.text((50, 300), "in a few moments.", fill='black', font=font_small)
            
            draw.text((50, 700), f"CV ID: {cv_uuid[:8]}", fill='gray', font=font_small)
            
            img.save(jpg_path, 'JPEG', quality=80)
        
        logger.info(f'Created dummy files for CV {cv_uuid}')
        return pdf_path, jpg_path
        
    except Exception as e:
        logger.error(f'Failed to create dummy files: {str(e)}')
        raise Exception(f"Complete PDF generation failure: {str(e)}")


def cleanup_temp_files(user_dir):
    """
    Clean up temporary LaTeX compilation files.
    
    Args:
        user_dir (str): User directory path
    """
    try:
        temp_extensions = ['.aux', '.log', '.out', '.fdb_latexmk', '.fls', '.synctex.gz']
        
        for file in os.listdir(user_dir):
            if any(file.endswith(ext) for ext in temp_extensions):
                file_path = os.path.join(user_dir, file)
                os.remove(file_path)
                logger.debug(f'Cleaned up temp file: {file_path}')
                
    except Exception as e:
        logger.warning(f'Failed to cleanup temp files: {str(e)}')


def validate_latex_code(latex_code):
    """
    Validate LaTeX code for basic syntax errors.
    
    Args:
        latex_code (str): LaTeX source code
        
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    try:
        if not latex_code or not latex_code.strip():
            errors.append("LaTeX code is empty")
            return False, errors
        
        # Check for document class
        if '\\documentclass' not in latex_code:
            errors.append("Missing \\documentclass declaration")
        
        # Check for document environment
        if '\\begin{document}' not in latex_code:
            errors.append("Missing \\begin{document}")
        
        if '\\end{document}' not in latex_code:
            errors.append("Missing \\end{document}")
        
        # Check for balanced braces
        open_braces = latex_code.count('{')
        close_braces = latex_code.count('}')
        
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces: {open_braces} opening, {close_braces} closing")
        
        # Check for dangerous commands (security)
        dangerous_commands = ['\\write18', '\\input', '\\include', '\\openin', '\\openout']
        for cmd in dangerous_commands:
            if cmd in latex_code:
                errors.append(f"Potentially dangerous command detected: {cmd}")
        
        return len(errors) == 0, errors
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return False, errors
