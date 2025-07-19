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
    """Enhanced Service for generating attractive posters with professional design"""
    
    def __init__(self):
        # Font sizes for different elements
        self.default_font_size = 36
        self.title_font_size = 48
        self.company_title_font_size = 28
        self.price_font_size = 42
        self.company_font_size =35
        self.contact_font_size = 28
        self.starting_from_font_size = 14
        self.package_title_font_size = 52
        
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
    
    def _add_company_logo_with_name(self, draw, position, company_name, logo_path=None):
        """Add company logo with name using same styling as package title"""
        try:
            x, y = position
            current_y = y

            # Add logo if provided (positioned above the text)
            if logo_path and os.path.exists(logo_path):
                try:
                    logo = Image.open(logo_path)

                    if logo.mode != 'RGBA':
                      logo = logo.convert('RGBA')

                    # Resize logo to fit nicely
                      logo_size = (60, 60)
                      logo.thumbnail(logo_size, Image.Resampling.LANCZOS)

                    # Create circular mask for logo
                      mask = Image.new('L', logo.size, 0)
                      mask_draw = ImageDraw.Draw(mask)
                      mask_draw.ellipse((0, 0) + logo.size, fill=255)

                      logo_circular = Image.new('RGBA', logo.size, (0, 0, 0, 0))
                      logo_circular.paste(logo, (0, 0))
                      logo_circular.putalpha(mask)

                # Position logo
                      draw._image.paste(logo_circular, (x, current_y), logo_circular)
                      current_y += logo.size[1] + 10

                except Exception as e:
                      logger.warning(f"Could not add logo: {e}")

        # Company name with same styling as package title
            company_font = self._load_font(self.package_title_font_size, bold=True)

        # Add shadow effect (same as package title)
            shadow_offset = 3
            draw.text((x + shadow_offset, current_y + shadow_offset), company_name, font=company_font, fill='#000000')
            draw.text((x, current_y), company_name, font=company_font, fill='#2E7D32')

        except Exception as e:
            logger.warning(f"Error adding company logo and name: {e}")
            # Fallback (same as package title fallback)
            fallback_font = self._load_font(self.title_font_size, bold=True)
            draw.text(position, company_name, font=fallback_font, fill='#2E7D32')


    def _add_package_title(self, draw, position, package_name, package_type='Package'):
        """Add main package title with attractive styling"""
        try:
            x, y = position
            
            # Main title (e.g., "Tawheed")
            title_font = self._load_font(self.package_title_font_size, bold=True)
            
            # Add shadow effect
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), package_name, font=title_font, fill='#000000')
            draw.text((x, y), package_name, font=title_font, fill='#2E7D32')
            
            # Get title dimensions for positioning subtitle
            title_width, title_height = self._get_text_dimensions(package_name, title_font)
            
            # Subtitle (e.g., "Umrah Package")
            subtitle_y = y + title_height + 5
            subtitle_font = self._load_font(self.title_font_size, bold=True)
            subtitle_text = f"Umrah {package_type}"
            
            # Add subtitle with green color
            draw.text((x + 2, subtitle_y + 2), subtitle_text, font=subtitle_font, fill='#000000')
            draw.text((x, subtitle_y), subtitle_text, font=subtitle_font, fill='#4CAF50')
            
        except Exception as e:
            logger.warning(f"Error adding package title: {e}")
            # Fallback
            fallback_font = self._load_font(self.title_font_size, bold=True)
            draw.text(position, f"{package_name} Package", font=fallback_font, fill='#2E7D32')
    
    def _create_professional_price_badge(self, draw, position, price_text, currency='₹'):
        """Create a professional price badge similar to the second image"""
        try:
            x, y = position
            
            # Format price text
            formatted_price = f"{currency}{price_text:,}" if isinstance(price_text, (int, float)) else f"{currency}{price_text}"
            
            # Calculate dimensions
            price_font = self._load_font(self.price_font_size, bold=True)
            starting_font = self._load_font(self.starting_from_font_size, bold=True)
            
            price_width, price_height = self._get_text_dimensions(formatted_price, price_font)
            starting_width, starting_height = self._get_text_dimensions("Starting From", starting_font)
            
            # Badge dimensions
            badge_width = max(price_width, starting_width) + 40
            badge_height = price_height + starting_height + 30
            
            # Create angled badge shape
            points = [
                (x, y),
                (x + badge_width - 20, y),
                (x + badge_width, y + 20),
                (x + badge_width, y + badge_height),
                (x + 20, y + badge_height),
                (x, y + badge_height - 20)
            ]
            
            # Draw shadow
            shadow_points = [(px + 4, py + 4) for px, py in points]
            draw.polygon(shadow_points, fill='#00000080')
            
            # Draw main badge with gradient effect
            draw.polygon(points, fill='#4CAF50', outline='#2E7D32', width=3)
            
            # Add inner highlight
            inner_points = [(px + 3, py + 3) for px, py in points[:-2]] + [(points[-2][0] - 3, points[-2][1] - 3), (points[-1][0] + 3, points[-1][1] + 3)]
            draw.polygon(inner_points, outline='#66BB6A', width=1)
            
            # Add text
            starting_text_x = x + (badge_width - starting_width) // 2
            starting_text_y = y + 10
            
            price_text_x = x + (badge_width - price_width) // 2
            price_text_y = starting_text_y + starting_height + 5
            
            # Add "Starting From" text
            draw.text((starting_text_x, starting_text_y), "Starting From", font=starting_font, fill='white')
            
            # Add price with shadow
            draw.text((price_text_x + 2, price_text_y + 2), formatted_price, font=price_font, fill='#000000')
            draw.text((price_text_x, price_text_y), formatted_price, font=price_font, fill='white')
            
        except Exception as e:
            logger.warning(f"Error creating price badge: {e}")
            # Fallback
            fallback_font = self._load_font(self.price_font_size, bold=True)
            draw.text(position, f"₹{price_text}", font=fallback_font, fill='#4CAF50')
    
    def _add_bottom_contact_bar(self, draw, image_width, image_height, user_data):
        """Add contact information bar at the bottom"""
        try:
            bar_height = 80
            bar_y = image_height - bar_height
            
            # Draw green background bar
            draw.rectangle([0, bar_y, image_width, image_height], fill='#2E7D32')
            
            # Add "BOOK NOW" badge
            book_now_x = 30
            book_now_y = bar_y + 15
            
            # Book now star burst
            star_points = []
            center_x, center_y = book_now_x + 40, book_now_y + 25
            for i in range(16):
                angle = i * 22.5
                if i % 2 == 0:
                    radius = 35
                else:
                    radius = 20
                import math
                x = center_x + radius * math.cos(math.radians(angle))
                y = center_y + radius * math.sin(math.radians(angle))
                star_points.extend([x, y])
            
            draw.polygon(star_points, fill='#FF5722', outline='#D84315', width=2)
            
            # Book now text
            book_font = self._load_font(16, bold=True)
            book_text_width, book_text_height = self._get_text_dimensions("BOOK", book_font)
            now_text_width, now_text_height = self._get_text_dimensions("NOW", book_font)
            
            draw.text((center_x - book_text_width//2, center_y - book_text_height - 2), "BOOK", font=book_font, fill='white')
            draw.text((center_x - now_text_width//2, center_y + 2), "NOW", font=book_font, fill='white')
            
            # Contact information
            contact_font = self._load_font(self.contact_font_size, bold=True)
            contact_y = bar_y + 20
            
            phone = user_data.get('phone', '')
            email = user_data.get('email', '')
            website = user_data.get('website', '')
            
            current_x = 150
            
            if phone:
                phone_icon = "📞"
                phone_text = f"{phone_icon} {phone}"
                draw.text((current_x, contact_y), phone_text, font=contact_font, fill='white')
                phone_width, _ = self._get_text_dimensions(phone_text, contact_font)
                current_x += phone_width + 40
            
            if email:
                 email_icon = "✉️"  # Better suited for email than 🌐
                 email_text = f"{email_icon} {email}"
                 draw.text((current_x, contact_y), email_text, font=contact_font, fill='white')

                    
        except Exception as e:
            logger.warning(f"Error adding contact bar: {e}")
    
    def _calculate_enhanced_positions(self, image_width, image_height):
        """Calculate positions for enhanced layout"""
        try:
            positions = {}
            
            # Top left area for company logo and name
            positions['company_logo'] = (30, 30)
            
            # Main title area (left side)
            positions['package_title'] = (50, 160)
            
            # Package details (left side, below title)
            positions['package_details'] = (50, 280)
            
            # Price badge (right side, middle)
            positions['price_badge'] = (image_width - 200, int(image_height * 0.45))
            
            # Bottom contact bar is handled separately
            
            return positions
        except Exception as e:
            logger.warning(f"Error calculating positions: {e}")
            # Return default positions
            return {
                'company_logo': (30, 30),
                'package_title': (50, 160), 
                'package_details': (50, 280),
                'price_badge': (400, 300)
            }
    
    def _generate_poster_image(self, poster_data, user_data, template_path, logo_path=None):
        """Generate the enhanced poster image"""
        template_image = None
        try:
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template image not found: {template_path}")
            
            template_image = Image.open(template_path)
            
            if template_image.mode != 'RGB':
                template_image = template_image.convert('RGB')
            
            img_width, img_height = template_image.size
            poster_image = template_image.copy()
            
            draw = ImageDraw.Draw(poster_image)
            
            # Extract data with defaults
            company_name = user_data.get('company_name', 'Your Company')
            package_name = poster_data.get('package_name', company_name)
            package_type = poster_data.get('package_type', 'Package')
            price = poster_data.get('price', '0')
            
            # Format price properly
            try:
                if isinstance(price, str):
                    price_clean = price.replace(',', '').replace('₹', '').replace(' ', '')
                    if price_clean:
                        price = float(price_clean)
                    else:
                        price = 0
                formatted_price = f"{price:,.0f}"
            except (ValueError, TypeError):
                formatted_price = str(price)
            
            # Calculate positions
            positions = self._calculate_enhanced_positions(img_width, img_height)
            
            # Add elements to poster in order
            
            # 1. Company logo and name (top left)
            
            
            # 2. Package title (left side)
            self._add_company_logo_with_name(draw, positions['company_logo'], company_name, logo_path)
            
            
            # 4. Price badge (right side)
            self._create_professional_price_badge(draw, positions['price_badge'], formatted_price)
            
            # 5. Bottom contact bar
            self._add_bottom_contact_bar(draw, img_width, img_height, user_data)
            
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
                image.save(img_buffer, format='JPEG', quality=95 if scale >= 1.0 else min(95, max(75, int(85 + 10 * scale))), optimize=True)
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
        Generate enhanced poster with professional design
        
        Args:
            poster_data: Dict containing package_name, package_type, price, duration, description, etc.
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
            logger.info(f"Enhanced poster generated successfully in {format_type} format, size: {len(content)} bytes")
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
        Generate multiple enhanced posters at once
        
        Args:
            posters_data: List of dicts containing poster data
            user_data: Dict containing company_name, phone, email, website
            template_path: Path to the template background image
            format_type: Output format ('jpg', 'png', 'pdf')
            logo_path: Path to company logo image (optional)
        
        Returns:
            List of generated posters with enhanced design
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