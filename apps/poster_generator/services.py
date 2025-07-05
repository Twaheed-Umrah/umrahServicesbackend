import io
import logging
import time
import gc
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from django.conf import settings
import os
import tempfile

logger = logging.getLogger(__name__)

class PosterGeneratorService:
    """Service for generating posters with text overlays on templates"""
    
    def __init__(self):
        self.default_font_size = 36
        self.title_font_size = 48
        self.price_font_size = 42
        self.company_font_size = 26
        self.contact_font_size = 18
        
        # Try to load custom fonts, fallback to default if not available
        self.font_path = self._get_font_path()
        self.title_font_path = self._get_title_font_path()
    
    def _get_font_path(self):
        """Get path to font file, fallback to default if not found"""
        try:
            font_paths = [
                os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'fonts', 'arial.ttf'),
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf'),
                '/System/Library/Fonts/Arial.ttf',  # macOS
                'C:/Windows/Fonts/arial.ttf',        # Windows
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return font_path
            return None
        except Exception as e:
            logger.warning(f"Error getting font path: {e}")
            return None
    
    def _get_title_font_path(self):
        """Get path to title font file, fallback to regular font"""
        try:
            font_paths = [
                os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'fonts', 'arial-bold.ttf'),
                os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial-bold.ttf'),
                '/System/Library/Fonts/Arial Bold.ttf',  # macOS
                'C:/Windows/Fonts/arialbd.ttf',          # Windows
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    return font_path
            return self.font_path
        except Exception as e:
            logger.warning(f"Error getting title font path: {e}")
            return self.font_path
    
    def _load_font(self, size, bold=False):
        """Load font with specified size"""
        try:
            font_path = self.title_font_path if bold else self.font_path
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
            else:
                return ImageFont.load_default()
        except Exception as e:
            logger.warning(f"Could not load font: {e}")
            return ImageFont.load_default()
    
    def _get_text_dimensions(self, text, font):
        """Get text width and height"""
        try:
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            bbox = temp_draw.textbbox((0, 0), text, font=font)
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            return width, height
        except Exception as e:
            logger.warning(f"Error getting text dimensions: {e}")
            return 100, 20  # Default dimensions
    
    def _add_text_with_shadow(self, draw, position, text, font, text_color='white', shadow_color='black', shadow_offset=2):
        """Add text with shadow effect"""
        try:
            x, y = position
            draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=text_color)
        except Exception as e:
            logger.warning(f"Error adding text with shadow: {e}")
    
    def _add_gradient_text(self, draw, position, text, font, gradient_colors=['#FF6B35', '#F7931E', '#FFD700']):
        """Add colorful gradient-style text effect"""
        try:
            x, y = position
            for i, color in enumerate(gradient_colors):
                offset = i * 1
                draw.text((x + offset, y + offset), text, font=font, fill=color)
        except Exception as e:
            logger.warning(f"Error adding gradient text: {e}")
    
    def _add_stylish_company_name(self, draw, position, company_name, font):
        """Add company name with stylish colorful background"""
        try:
            x, y = position
            text_width, text_height = self._get_text_dimensions(company_name, font)
            
            padding = 15
            bg_width = text_width + (padding * 2)
            bg_height = text_height + (padding * 2)
            
            bg_x = x - padding
            bg_y = y - padding
            
            # Check if rounded_rectangle is available, fallback to rectangle
            try:
                draw.rounded_rectangle(
                    [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
                    radius=12,
                    fill='#2E7D32',
                    outline='#1B5E20',
                    width=3
                )
                
                draw.rounded_rectangle(
                    [bg_x + 2, bg_y + 2, bg_x + bg_width - 2, bg_y + bg_height - 2],
                    radius=10,
                    outline='#4CAF50',
                    width=1
                )
            except AttributeError:
                # Fallback for older PIL versions
                draw.rectangle(
                    [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
                    fill='#2E7D32',
                    outline='#1B5E20',
                    width=3
                )
            
            draw.text((x, y), company_name, font=font, fill='white')
        except Exception as e:
            logger.warning(f"Error adding stylish company name: {e}")
            # Fallback to simple text
            draw.text(position, company_name, font=font, fill='white')
    
    def _add_logo(self, poster_image, logo_path, position, max_size=(100, 100)):
        """Add logo to the poster at specified position with enhanced styling"""
        try:
            if not os.path.exists(logo_path):
                logger.warning(f"Logo not found: {logo_path}")
                return poster_image
            
            logo = Image.open(logo_path)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            logo.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new('L', logo.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0) + logo.size, fill=255)
            
            logo_circular = Image.new('RGBA', logo.size, (0, 0, 0, 0))
            logo_circular.paste(logo, (0, 0))
            logo_circular.putalpha(mask)
            
            poster_image.paste(logo_circular, position, logo_circular)
            
            return poster_image
            
        except Exception as e:
            logger.warning(f"Could not add logo: {e}")
            return poster_image
    
    def _calculate_umrah_style_positions(self, image_width, image_height):
        """Calculate positions based on Umrah poster layout"""
        try:
            positions = {}
            
            positions['logo'] = (50, 20)
            positions['company'] = (50, 140)
            positions['price'] = (image_width - 250, int(image_height * 0.6))
            positions['phone'] = (80, image_height - 100)
            positions['email'] = (80, image_height - 70)
            positions['website'] = (80, image_height - 40)
            
            return positions
        except Exception as e:
            logger.warning(f"Error calculating positions: {e}")
            # Return default positions
            return {
                'logo': (50, 20),
                'company': (50, 140),
                'price': (200, 300),
                'phone': (80, 400),
                'email': (80, 430),
                'website': (80, 460)
            }
    
    def _create_enhanced_price_badge(self, draw, position, price_text, font):
        """Create an enhanced price badge with stylish design"""
        try:
            text_width, text_height = self._get_text_dimensions(price_text, font)
            
            badge_width = text_width + 60
            badge_height = text_height + 40
            badge_x, badge_y = position
            
            shadow_offset = 4
            
            # Draw shadow
            try:
                draw.rounded_rectangle(
                    [badge_x + shadow_offset, badge_y + shadow_offset, 
                     badge_x + badge_width + shadow_offset, badge_y + badge_height + shadow_offset],
                    radius=15,
                    fill='#000000',
                    width=0
                )
            except AttributeError:
                # Fallback for older PIL versions
                draw.rectangle(
                    [badge_x + shadow_offset, badge_y + shadow_offset, 
                     badge_x + badge_width + shadow_offset, badge_y + badge_height + shadow_offset],
                    fill='#000000'
                )
            
            # Draw gradient background
            gradient_colors = ['#FF6B35', '#F7931E']
            for i, color in enumerate(gradient_colors):
                offset = i * 2
                try:
                    draw.rounded_rectangle(
                        [badge_x + offset, badge_y + offset, 
                         badge_x + badge_width - offset, badge_y + badge_height - offset],
                        radius=15 - offset,
                        fill=color,
                        outline='#B71C1C' if i == 0 else None,
                        width=2 if i == 0 else 0
                    )
                except AttributeError:
                    draw.rectangle(
                        [badge_x + offset, badge_y + offset, 
                         badge_x + badge_width - offset, badge_y + badge_height - offset],
                        fill=color,
                        outline='#B71C1C' if i == 0 else None,
                        width=2 if i == 0 else 0
                    )
            
            # Add "Starting From" text
            starting_font = self._load_font(14, bold=True)
            starting_text = "Starting From"
            starting_width, starting_height = self._get_text_dimensions(starting_text, starting_font)
            starting_x = badge_x + (badge_width - starting_width) // 2
            starting_y = badge_y + 8
            
            draw.text((starting_x, starting_y), starting_text, font=starting_font, fill='white')
            
            # Add price text
            price_x = badge_x + (badge_width - text_width) // 2
            price_y = badge_y + starting_height + 15
            
            draw.text((price_x + 2, price_y + 2), price_text, font=font, fill='#000000')
            draw.text((price_x, price_y), price_text, font=font, fill='white')
            
        except Exception as e:
            logger.warning(f"Error creating price badge: {e}")
            # Fallback to simple text
            draw.text(position, price_text, font=font, fill='white')
    
    def _add_stylish_contact_info(self, draw, position, text, font, icon_color='#4CAF50'):
        """Add contact information with stylish background"""
        try:
            x, y = position
            
            text_width, text_height = self._get_text_dimensions(text, font)
            
            padding = 8
            bg_width = text_width + (padding * 2)
            bg_height = text_height + (padding * 2)
            
            try:
                draw.rounded_rectangle(
                    [x - padding, y - padding, x + bg_width - padding, y + bg_height - padding],
                    radius=8,
                    fill='#2E7D32',
                    outline='#1B5E20',
                    width=2
                )
            except AttributeError:
                # Fallback for older PIL versions
                draw.rectangle(
                    [x - padding, y - padding, x + bg_width - padding, y + bg_height - padding],
                    fill='#2E7D32',
                    outline='#1B5E20',
                    width=2
                )
            
            draw.text((x, y), text, font=font, fill='white')
            
        except Exception as e:
            logger.warning(f"Error adding stylish contact info: {e}")
            # Fallback to simple text
            draw.text(position, text, font=font, fill='white')
    
    def _generate_poster_image(self, poster_data, user_data, template_path, logo_path=None):
        """Generate the poster image (internal method)"""
        template_image = None
        try:
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template image not found: {template_path}")
            
            template_image = Image.open(template_path)
            
            if template_image.mode != 'RGB':
                template_image = template_image.convert('RGB')
            
            img_width, img_height = template_image.size
            poster_image = template_image.copy()
            
            # Add logo if provided
            if logo_path and os.path.exists(logo_path):
                poster_image = self._add_logo(poster_image, logo_path, (50, 20), max_size=(100, 100))
            
            draw = ImageDraw.Draw(poster_image)
            
            # Extract data with defaults
            company_name = user_data.get('company_name', 'Your Company')
            price = poster_data.get('price', '0')
            phone = user_data.get('phone', '')
            email = user_data.get('email', '')
            website = user_data.get('website', '')
            
            # Format price properly
            try:
                if isinstance(price, str):
                    price_clean = price.replace(',', '').replace('₹', '').replace(' ', '')
                    if price_clean:
                        price = float(price_clean)
                    else:
                        price = 0
                price_text = f"₹{price:,.0f}"
            except (ValueError, TypeError):
                price_text = f"₹{price}"
            
            # Load fonts
            company_font = self._load_font(self.company_font_size, bold=True)
            price_font = self._load_font(self.price_font_size, bold=True)
            contact_font = self._load_font(self.contact_font_size, bold=False)
            
            # Calculate positions
            positions = self._calculate_umrah_style_positions(img_width, img_height)
            
            # Add elements to poster
            self._add_stylish_company_name(draw, positions['company'], company_name, company_font)
            self._create_enhanced_price_badge(draw, positions['price'], price_text, price_font)
            
            if phone:
                phone_text = f"📞 {phone}"
                self._add_stylish_contact_info(draw, positions['phone'], phone_text, contact_font)
            
            if email:
                email_text = f"✉️ {email}"
                self._add_stylish_contact_info(draw, positions['email'], email_text, contact_font)
            
            if website:
                website_text = f"🌐 {website}"
                self._add_stylish_contact_info(draw, positions['website'], website_text, contact_font)
            
            return poster_image
            
        except Exception as e:
            logger.exception(f"Error generating poster image: {e}")
            raise
        finally:
            # Clean up template image
            if template_image:
                try:
                    template_image.close()
                except:
                    pass
    
    def _safe_delete_file(self, file_path, max_retries=3):
        """Safely delete a file with retry mechanism for Windows"""
        for attempt in range(max_retries):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            except (OSError, PermissionError) as e:
                if attempt < max_retries - 1:
                    gc.collect()  # Force garbage collection
                    time.sleep(0.1)  # Small delay
                    continue
                logger.warning(f"Failed to delete file {file_path} after {max_retries} attempts: {e}")
                return False
        return True
    
    def _generate_pdf(self, image, output_buffer):
        """Generate PDF from image with improved error handling and proper cleanup"""
        temp_file_path = None
        try:
            # Reset buffer
            output_buffer.seek(0)
            output_buffer.truncate()
            
            # Ensure image is in RGB mode for PDF
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create PDF canvas
            c = canvas.Canvas(output_buffer, pagesize=A4)
            page_width, page_height = A4
            
            # Calculate scaling to fit image on page
            img_width, img_height = image.size
            scale_w = (page_width - 2 * inch) / img_width
            scale_h = (page_height - 2 * inch) / img_height
            scale = min(scale_w, scale_h)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2
            
            # Method 1: Use in-memory approach (recommended)
            try:
                # Convert PIL image to bytes
                
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='JPEG', quality = 95 if scale >= 1.0 else min(95, max(75, int(85 + 10 * scale))), optimize=True)
                img_buffer.seek(0)
                
                # Use ImageReader with BytesIO
                img_reader = ImageReader(img_buffer)
                
                # Draw image on PDF
                c.drawImage(
                    img_reader,
                    x, y,
                    width=new_width,
                    height=new_height,
                    preserveAspectRatio=True
                )
                
                # Clean up
                img_buffer.close()
                
            except Exception as e:
                logger.warning(f"In-memory PDF generation failed: {e}, falling back to temp file method")
                
                # Method 2: Fallback to temp file with proper cleanup
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_file_path = temp_file.name
                
                try:
                    # Save image to temp file
                    image.save(temp_file_path, format='JPEG', quality=95, optimize=True)
                    temp_file.close()  # Close the file handle
                    
                    # Force garbage collection and small delay for Windows
                    gc.collect()
                    time.sleep(0.05)
                    
                    # Draw image on PDF
                    c.drawImage(
                        temp_file_path,
                        x, y,
                        width=new_width,
                        height=new_height,
                        preserveAspectRatio=True
                    )
                    
                except Exception as temp_e:
                    logger.error(f"Temp file PDF generation failed: {temp_e}")
                    raise temp_e
                finally:
                    # Clean up temp file
                    if temp_file_path:
                        self._safe_delete_file(temp_file_path)
            
            # Save PDF
            c.save()
            
            # Get buffer content and verify
            output_buffer.seek(0)
            pdf_content = output_buffer.getvalue()
            
            if len(pdf_content) == 0:
                raise Exception("PDF buffer is empty")
            
            # Reset buffer position for reading
            output_buffer.seek(0)
            
            logger.info(f"PDF generated successfully, size: {len(pdf_content)} bytes")
            return output_buffer
            
        except Exception as e:
            logger.exception(f"Error generating PDF: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")
        finally:
            # Final cleanup attempt
            if temp_file_path:
                self._safe_delete_file(temp_file_path)
    
    def generate_poster(self, poster_data, user_data, template_path, format_type='jpg', logo_path=None):
        """
        Generate poster by overlaying text on template image with enhanced styling
        
        Args:
            poster_data: Dict containing package_name, package_type, price, etc.
            user_data: Dict containing company_name, phone, email, website
            template_path: Path to the template background image
            format_type: Output format ('jpg', 'png', 'pdf')
            logo_path: Path to company logo image (optional)
        
        Returns:
            BytesIO object containing the generated poster
        """
        poster_image = None
        try:
            # Validate inputs
            if not poster_data:
                raise ValueError("poster_data cannot be empty")
            if not user_data:
                raise ValueError("user_data cannot be empty")
            if not template_path:
                raise ValueError("template_path cannot be empty")
            
            # Generate the poster image
            poster_image = self._generate_poster_image(poster_data, user_data, template_path, logo_path)
            
            # Generate output in specified format
            output_buffer = io.BytesIO()
            
            if format_type.lower() == 'pdf':
                self._generate_pdf(poster_image, output_buffer)
            elif format_type.lower() == 'png':
                poster_image.save(output_buffer, format='PNG', optimize=True)
            else:  # jpg/jpeg
                if poster_image.mode != 'RGB':
                    poster_image = poster_image.convert('RGB')
                poster_image.save(output_buffer, format='JPEG', quality=95, optimize=True)
            
            # Verify output
            output_buffer.seek(0)
            content = output_buffer.getvalue()
            if len(content) == 0:
                raise Exception(f"Generated {format_type} file is empty")
            
            output_buffer.seek(0)
            logger.info(f"Poster generated successfully in {format_type} format, size: {len(content)} bytes")
            return output_buffer
            
        except Exception as e:
            logger.exception(f"Error generating poster: {e}")
            raise Exception(f"Poster generation failed: {str(e)}")
        finally:
            # Clean up poster image
            if poster_image:
                try:
                    poster_image.close()
                except:
                    pass
            
            # Force garbage collection for Windows
            gc.collect()
    
    def generate_multiple_posters(self, posters_data, user_data, template_path, format_type='jpg', logo_path=None):
        """
        Generate multiple posters at once
        
        Args:
            posters_data: List of dicts containing poster data
            user_data: Dict containing company_name, phone, email, website
            template_path: Path to the template background image
            format_type: Output format ('jpg', 'png', 'pdf')
            logo_path: Path to company logo image (optional)
        
        Returns:
            List of generated posters
        """
        results = []
        
        if not posters_data:
            logger.warning("No poster data provided")
            return results
        
        for i, poster_data in enumerate(posters_data):
            try:
                if not poster_data:
                    logger.warning(f"Skipping empty poster data at index {i}")
                    continue
                    
                result = self.generate_poster(
                    poster_data, 
                    user_data, 
                    template_path, 
                    format_type,
                    logo_path
                )
                results.append({
                    'index': i,
                    'poster_data': poster_data,
                    'file': result,
                    'success': True
                })
            except Exception as e:
                logger.exception(f"Error generating poster {i}: {e}")
                results.append({
                    'index': i,
                    'poster_data': poster_data,
                    'error': str(e),
                    'success': False
                })
        
        return results