import io
import logging
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class PosterGeneratorService:
    """Service for generating posters with text overlays on templates"""
    
    def __init__(self):
        self.default_font_size = 36
        self.title_font_size = 48
        self.price_font_size = 42
        self.company_font_size = 52  # Larger for company name
        self.contact_font_size = 24  # For contact info
        
        # Try to load custom fonts, fallback to default if not available
        self.font_path = self._get_font_path()
        self.title_font_path = self._get_title_font_path()
    
    def _get_font_path(self):
        """Get path to font file, fallback to default if not found"""
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
    
    def _get_title_font_path(self):
        """Get path to title font file, fallback to regular font"""
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
        return self.font_path  # Fallback to regular font
    
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
        # Create a temporary image to measure text
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    
    def _add_text_with_shadow(self, draw, position, text, font, text_color='white', shadow_color='black', shadow_offset=2):
        """Add text with shadow effect"""
        x, y = position
        
        # Draw shadow
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    def _add_logo(self, poster_image, logo_path, position, max_size=(80, 80)):
        """Add logo to the poster at specified position"""
        try:
            if not os.path.exists(logo_path):
                logger.warning(f"Logo not found: {logo_path}")
                return poster_image
            
            logo = Image.open(logo_path)
            
            # Convert to RGBA if not already
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Resize logo while maintaining aspect ratio
            logo.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Paste logo onto poster (with transparency support)
            poster_image.paste(logo, position, logo)
            
            return poster_image
            
        except Exception as e:
            logger.warning(f"Could not add logo: {e}")
            return poster_image
    
    def _calculate_umrah_style_positions(self, image_width, image_height):
        """Calculate positions based on Umrah poster layout"""
        positions = {}
        
        # Logo position - top left (like in reference poster)
        positions['logo'] = (50, 30)
        
        # Company name - top left, next to logo
        positions['company'] = (150, 45)  # Adjusted for logo space
        
        # Price position - middle right in a green badge style area
        # Based on the reference poster, price appears around 60% down, right side
        positions['price'] = (image_width - 200, int(image_height * 0.6))
        
        # Contact info - bottom in a colored bar area
        # Phone number position
        positions['phone'] = (100, image_height - 80)
        
        # Email/website position (next to phone)
        positions['email'] = (100, image_height - 50)
        
        return positions
    
    def _create_price_badge(self, draw, position, price_text, font):
        """Create a price badge similar to the reference poster"""
        # Get text dimensions for badge sizing
        text_width, text_height = self._get_text_dimensions(price_text, font)
        
        # Badge dimensions with padding
        badge_width = text_width + 40
        badge_height = text_height + 20
        badge_x, badge_y = position
        
        # Create rounded rectangle for badge background
        # Green color similar to reference poster
        badge_color = '#2E7D32'  # Dark green
        
        # Draw badge background
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
            radius=10,
            fill=badge_color,
            outline='#1B5E20',  # Darker green for outline
            width=2
        )
        
        # Add "Starting From" text above price
        starting_font = self._load_font(16)
        starting_text = "Starting From"
        starting_width, starting_height = self._get_text_dimensions(starting_text, starting_font)
        starting_x = badge_x + (badge_width - starting_width) // 2
        starting_y = badge_y + 5
        
        draw.text((starting_x, starting_y), starting_text, font=starting_font, fill='white')
        
        # Add price text
        price_x = badge_x + (badge_width - text_width) // 2
        price_y = badge_y + starting_height + 8
        
        draw.text((price_x, price_y), price_text, font=font, fill='white')
    
    def generate_poster(self, poster_data, user_data, template_path, logo_path=None, format_type='jpg'):
        """
        Generate poster by overlaying text on template image with Umrah poster style layout
        
        Args:
            poster_data: Dict containing package_name, package_type, price, etc.
            user_data: Dict containing company_name, phone, email
            template_path: Path to the template background image
            logo_path: Path to company logo image (optional)
            format_type: Output format ('jpg', 'png', 'pdf')
        
        Returns:
            BytesIO object containing the generated poster
        """
        try:
            # Load template image
            if not os.path.exists(template_path):
                raise FileNotFoundError(f"Template image not found: {template_path}")
            
            template_image = Image.open(template_path)
            
            # Convert to RGB if necessary
            if template_image.mode != 'RGB':
                template_image = template_image.convert('RGB')
            
            # Get image dimensions
            img_width, img_height = template_image.size
            
            # Create a copy to work with
            poster_image = template_image.copy()
            
            # Add logo if provided
            if logo_path:
                poster_image = self._add_logo(poster_image, logo_path, (50, 30), max_size=(80, 80))
            
            draw = ImageDraw.Draw(poster_image)
            
            # Prepare text content
            company_name = user_data.get('company_name', 'Your Company')
            price = poster_data.get('price', '0')
            phone = user_data.get('phone', '')
            email = user_data.get('email', '')
            
            # Format price
            price_text = f"₹{price:,}" if isinstance(price, (int, float)) else f"₹{price}"
            
            # Load fonts
            company_font = self._load_font(self.company_font_size, bold=True)
            price_font = self._load_font(self.price_font_size, bold=True)
            contact_font = self._load_font(self.contact_font_size)
            
            # Calculate positions using Umrah poster layout
            positions = self._calculate_umrah_style_positions(img_width, img_height)
            
            # Add company name at top (next to logo area)
            self._add_text_with_shadow(
                draw, 
                positions['company'], 
                company_name, 
                company_font,
                text_color='#2E7D32',  # Green color to match theme
                shadow_color='white',
                shadow_offset=1
            )
            
            # Add price in badge style
            self._create_price_badge(
                draw,
                positions['price'],
                price_text,
                price_font
            )
            
            # Add contact information at bottom
            if phone:
                phone_text = f"📞 {phone}"
                self._add_text_with_shadow(
                    draw,
                    positions['phone'],
                    phone_text,
                    contact_font,
                    text_color='white',
                    shadow_color='black',
                    shadow_offset=1
                )
            
            if email:
                email_text = f"🌐 {email}"
                self._add_text_with_shadow(
                    draw,
                    positions['email'],
                    email_text,
                    contact_font,
                    text_color='white',
                    shadow_color='black',
                    shadow_offset=1
                )
            
            # Generate output based on format
            output_buffer = io.BytesIO()
            
            if format_type.lower() == 'pdf':
                # Generate PDF
                self._generate_pdf(poster_image, output_buffer)
            else:
                # Generate image (JPG/PNG)
                image_format = 'JPEG' if format_type.lower() == 'jpg' else 'PNG'
                if image_format == 'JPEG':
                    # Ensure RGB mode for JPEG
                    if poster_image.mode != 'RGB':
                        poster_image = poster_image.convert('RGB')
                
                poster_image.save(output_buffer, format=image_format, quality=95)
            
            output_buffer.seek(0)
            return output_buffer
            
        except Exception as e:
            logger.exception(f"Error generating poster: {e}")
            raise Exception(f"Poster generation failed: {str(e)}")
    
    def _generate_pdf(self, image, output_buffer):
        """Generate PDF from image"""
        try:
            # Create PDF canvas
            c = canvas.Canvas(output_buffer, pagesize=A4)
            
            # Convert PIL image to bytes for reportlab
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            # Calculate dimensions to fit A4 page
            page_width, page_height = A4
            img_width, img_height = image.size
            
            # Calculate scaling to fit page while maintaining aspect ratio
            scale_w = page_width / img_width
            scale_h = page_height / img_height
            scale = min(scale_w, scale_h) * 0.9  # 90% of page size for margins
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            # Center the image on the page
            x = (page_width - new_width) / 2
            y = (page_height - new_height) / 2
            
            # Draw image on PDF
            c.drawImage(
                ImageReader(img_buffer), 
                x, y, 
                width=new_width, 
                height=new_height
            )
            
            c.save()
            
        except Exception as e:
            logger.exception(f"Error generating PDF: {e}")
            raise Exception(f"PDF generation failed: {str(e)}")