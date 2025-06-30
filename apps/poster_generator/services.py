from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, HexColor
from io import BytesIO
import os
import textwrap
import math
import logging

logger = logging.getLogger(__name__)

class PosterGeneratorService:
    def __init__(self):
        self.font_path = os.path.join(settings.BASE_DIR, 'static/fonts/')
        self.assets_path = os.path.join(settings.BASE_DIR, 'static/poster_assets/')
        
    def get_package_details(self, package_type):
        """Get enhanced package details with colors and icons"""
        details = {
            'umrah_classic': {
                'duration': '15 Days',
                'color_scheme': {
                    'primary': "#055126",      # Forest Green
                    'secondary': '#FFD700',    # Gold
                    'accent': '#FFFFFF',       # White
                    'text': '#2C3E50',         # Dark Blue Gray
                    'gradient_start': '#2E8B57',
                    'gradient_end': '#32CD32'
                },
                'features': [
                    '✈️ Visa & Transportation',
                    '🏨 Flight & Accommodation',
                    '🍽️ Meals & Assistance',
                    '🇸🇦 Saudi Airline available',
                    '📞 24×7 support from our team',
                    '🕌 Guided religious tours in Makkah & Madinah'
                ],
                'description': 'Embark on a spiritually fulfilling Umrah with premium service, expert guidance, and worry-free travel.',
                'badge_text': 'MOST POPULAR'
            },
            'umrah_delux': {
                'duration': '18 Days',
                'color_scheme': {
                    'primary': '#8B4513',      # Saddle Brown
                    'secondary': '#DAA520',    # Goldenrod
                    'accent': '#F5F5F5',       # White Smoke
                    'text': '#2C3E50',
                    'gradient_start': '#8B4513',
                    'gradient_end': '#A0522D'
                },
                'features': [
                    '✈️ Premium Visa & Transportation',
                    '🏨 Business Class Flight & 4-Star Hotel',
                    '🍽️ All Meals & VIP Assistance',
                    '🇸🇦 Saudi Airline Premium',
                    '📞 24×7 dedicated support',
                    '🕌 Private guided tours in Makkah & Madinah',
                    '🗺️ Ziyarat tours included'
                ],
                'description': 'Experience luxury Umrah with premium services and exclusive amenities.',
                'badge_text': 'PREMIUM'
            },
            'umrah_luxury': {
                'duration': '21 Days',
                'color_scheme': {
                    'primary': '#4B0082',      # Indigo
                    'secondary': '#FFD700',    # Gold
                    'accent': '#F8F8FF',       # Ghost White
                    'text': '#2C3E50',
                    'gradient_start': '#4B0082',
                    'gradient_end': '#6A5ACD'
                },
                'features': [
                    '✈️ VIP Visa & Luxury Transportation',
                    '🏨 First Class Flight & 5-Star Hotel',
                    '🍽️ Gourmet Meals & Personal Assistant',
                    '🇸🇦 Saudi Airline First Class',
                    '📞 24×7 personal concierge',
                    '🕌 Private scholar-led tours',
                    '🛍️ Exclusive Ziyarat & shopping tours'
                ],
                'description': 'Ultimate luxury Umrah experience with personalized service and premium amenities.',
                'badge_text': 'LUXURY'
            }
        }
        
        # Hajj packages
        hajj_packages = {
            'hajj_classic': {
                'duration': '40 Days',
                'color_scheme': {
                    'primary': '#DC143C',      # Crimson
                    'secondary': '#FFD700',    # Gold
                    'accent': '#FFFFFF',
                    'text': '#2C3E50',
                    'gradient_start': '#DC143C',
                    'gradient_end': '#FF6347'
                },
                'features': [
                    '✈️ Complete Hajj Transportation',
                    '🏨 Standard Accommodation',
                    '🍽️ All Meals Included',
                    '🕌 Guided Hajj Rituals',
                    '📞 24×7 Support',
                    '🗺️ Ziyarat Tours'
                ],
                'description': 'Complete Hajj pilgrimage with all essential services.',
                'badge_text': 'COMPLETE'
            },
            'hajj_delux': {
                'duration': '45 Days',
                'color_scheme': {
                    'primary': '#8B0000',      # Dark Red
                    'secondary': '#DAA520',    # Goldenrod
                    'accent': '#F5F5F5',
                    'text': '#2C3E50',
                    'gradient_start': '#8B0000',
                    'gradient_end': '#A52A2A'
                },
                'features': [
                    '✈️ Premium Hajj Transportation',
                    '🏨 4-Star Accommodation',
                    '🍽️ Premium Meals',
                    '🕌 Expert Hajj Guidance',
                    '📞 Dedicated Support Team',
                    '🗺️ Extended Ziyarat Tours'
                ],
                'description': 'Premium Hajj experience with enhanced comfort.',
                'badge_text': 'PREMIUM'
            },
            'hajj_luxury': {
                'duration': '50 Days',
                'color_scheme': {
                    'primary': '#800080',      # Purple
                    'secondary': '#FFD700',    # Gold
                    'accent': '#F8F8FF',
                    'text': '#2C3E50',
                    'gradient_start': '#800080',
                    'gradient_end': '#9370DB'
                },
                'features': [
                    '✈️ VIP Hajj Transportation',
                    '🏨 5-Star Luxury Hotels',
                    '🍽️ Gourmet Dining',
                    '🕌 Personal Hajj Scholar',
                    '📞 Personal Concierge',
                    '🛍️ Luxury Ziyarat & Shopping'
                ],
                'description': 'Luxury Hajj pilgrimage with exclusive services.',
                'badge_text': 'LUXURY'
            }
        }
        
        # Ramadan packages
        ramadan_packages = {
            'ramadan_early': {
                'duration': '10 Days',
                'color_scheme': {
                    'primary': '#006400',      # Dark Green
                    'secondary': '#FFFF00',    # Yellow
                    'accent': '#FFFFFF',
                    'text': '#2C3E50',
                    'gradient_start': '#006400',
                    'gradient_end': '#228B22'
                },
                'features': [
                    '✈️ Early Ramadan Travel',
                    '🏨 Premium Accommodation',
                    '🍽️ Iftar & Suhoor Included',
                    '🕌 Tarawih Prayers',
                    '📞 Spiritual Guidance',
                    '🗺️ Holy Sites Tours'
                ],
                'description': 'Early Ramadan Umrah experience.',
                'badge_text': 'EARLY BIRD'
            },
            'ramadan_laylat': {
                'duration': '7 Days',
                'color_scheme': {
                    'primary': '#191970',      # Midnight Blue
                    'secondary': '#FFD700',    # Gold
                    'accent': '#FFFFFF',
                    'text': '#2C3E50',
                    'gradient_start': '#191970',
                    'gradient_end': '#4169E1'
                },
                'features': [
                    '✈️ Special Laylat al-Qadr Package',
                    '🏨 Premium Hotel Stay',
                    '🍽️ Special Ramadan Meals',
                    '🕌 Night of Power Experience',
                    '📞 Spiritual Support',
                    '🗺️ Sacred Sites Visit'
                ],
                'description': 'Special Laylat al-Qadr package.',
                'badge_text': 'SPECIAL'
            },
            'ramadan_full': {
                'duration': '30 Days',
                'color_scheme': {
                    'primary': '#8B4513',      # Saddle Brown
                    'secondary': '#FFD700',    # Gold
                    'accent': '#FFFFFF',
                    'text': '#2C3E50',
                    'gradient_start': '#8B4513',
                    'gradient_end': '#A0522D'
                },
                'features': [
                    '✈️ Complete Month Stay',
                    '🏨 Long-term Accommodation',
                    '🍽️ Daily Iftar & Suhoor',
                    '🕌 All Tarawih Prayers',
                    '📞 Month-long Support',
                    '🗺️ Comprehensive Tours'
                ],
                'description': 'Complete month of Ramadan experience.',
                'badge_text': 'COMPLETE'
            }
        }
        
        details.update(hajj_packages)
        details.update(ramadan_packages)
        
        return details.get(package_type, details['umrah_classic'])
    
    def create_gradient_background(self, width, height, start_color, end_color):
        """Create a gradient background"""
        try:
            image = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(image)
            
            # Convert hex colors to RGB
            start_rgb = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
            end_rgb = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))
            
            for y in range(height):
                ratio = y / height
                r = int(start_rgb[0] * (1 - ratio) + end_rgb[0] * ratio)
                g = int(start_rgb[1] * (1 - ratio) + end_rgb[1] * ratio)
                b = int(start_rgb[2] * (1 - ratio) + end_rgb[2] * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b))
            
            return image
        except Exception as e:
            logger.error(f"Error creating gradient background: {e}")
            # Return a solid color background as fallback
            return Image.new('RGB', (width, height), (46, 125, 50))
    
    def add_rounded_rectangle(self, draw, coords, radius, fill=None, outline=None, width=1):
        """Draw a rounded rectangle"""
        try:
            x1, y1, x2, y2 = coords
            
            # Draw the main rectangle
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)
            
            # Draw the corners
            draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=fill, outline=outline, width=width)
            draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 360, fill=fill, outline=outline, width=width)
            draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=fill, outline=outline, width=width)
            draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=fill, outline=outline, width=width)
        except Exception as e:
            logger.error(f"Error drawing rounded rectangle: {e}")
            # Fallback to regular rectangle
            draw.rectangle(coords, fill=fill, outline=outline, width=width)
    
    def get_fonts(self):
        """Load fonts with fallback"""
        try:
            fonts = {}
            font_sizes = {
                'title': 52,
                'heading': 38,
                'subheading': 28,
                'body': 22,
                'small': 18,
                'tiny': 14
            }
            
            # Try to load custom fonts
            for font_name, size in font_sizes.items():
                try:
                    # Try different font files
                    font_files = ['arial-bold.ttf', 'arial.ttf', 'Arial.ttf', 'arial-unicode-ms.ttf']
                    font_loaded = False
                    
                    for font_file in font_files:
                        font_path = os.path.join(self.font_path, font_file)
                        if os.path.exists(font_path):
                            if 'bold' in font_name or font_name in ['title', 'heading', 'subheading']:
                                if 'bold' in font_file.lower():
                                    fonts[font_name] = ImageFont.truetype(font_path, size)
                                    font_loaded = True
                                    break
                            else:
                                if 'bold' not in font_file.lower():
                                    fonts[font_name] = ImageFont.truetype(font_path, size)
                                    font_loaded = True
                                    break
                    
                    if not font_loaded:
                        # Use default font with appropriate size
                        fonts[font_name] = ImageFont.load_default()
                        
                except Exception as e:
                    logger.warning(f"Could not load font for {font_name}: {e}")
                    fonts[font_name] = ImageFont.load_default()
            
            return fonts
            
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            default_font = ImageFont.load_default()
            return {
                'title': default_font,
                'heading': default_font,
                'subheading': default_font,
                'body': default_font,
                'small': default_font,
                'tiny': default_font
            }
    
    def create_attractive_poster(self, poster_data, user_data, package_details, format='jpg'):
        """Create an attractive Canva-style poster"""
        try:
            # Poster dimensions
            width, height = 1080, 1350  # Instagram post size
            
            # Create gradient background
            colors = package_details['color_scheme']
            poster = self.create_gradient_background(width, height, colors['gradient_start'], colors['gradient_end'])
            
            # Add overlay for better text readability
            overlay = Image.new('RGBA', (width, height), (255, 255, 255, 30))
            poster = Image.alpha_composite(poster.convert('RGBA'), overlay)
            
            draw = ImageDraw.Draw(poster)
            fonts = self.get_fonts()
            
            # Add decorative elements
            self.add_decorative_elements(draw, width, height, colors)
            
            # Header section with company name
            if user_data.get('company_name'):
                self.draw_header_section(draw, user_data['company_name'], colors, fonts, width)
            
            # Main title section
            self.draw_main_title(draw, poster_data['package_name'], colors, fonts, width, 180)
            
            # Price badge
            self.draw_price_badge(draw, poster_data['price'], colors, fonts, width, 280)
            
            # Package badge
            self.draw_package_badge(draw, package_details['badge_text'], colors, fonts, width, 350)
            
            # Duration info
            self.draw_duration_info(draw, package_details['duration'], colors, fonts, width, 420)
            
            # Features section
            self.draw_features_section(draw, package_details['features'], colors, fonts, width, 500)
            
            # Description
            self.draw_description(draw, package_details['description'], colors, fonts, width, 950)
            
            # Contact information
            self.draw_contact_section(draw, user_data, colors, fonts, width, height)
            
            # Call to action
            self.draw_cta_button(draw, colors, fonts, width, height - 150)
            
            return poster.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error creating attractive poster: {e}")
            raise
    
    def add_decorative_elements(self, draw, width, height, colors):
        """Add decorative elements to the poster"""
        try:
            # Top decorative line
            draw.rectangle([50, 120, width-50, 125], fill=colors['secondary'])
            
            # Side decorative elements
            for i in range(5):
                y = 200 + i * 100
                draw.ellipse([20, y, 40, y+20], fill=colors['secondary'])
                draw.ellipse([width-40, y, width-20, y+20], fill=colors['secondary'])
        except Exception as e:
            logger.error(f"Error adding decorative elements: {e}")
    
    def draw_header_section(self, draw, company_name, colors, fonts, width):
        """Draw header section with company name"""
        try:
            # Background for header
            self.add_rounded_rectangle(draw, [30, 30, width-30, 100], 15, 
                                     fill=colors['accent'], outline=colors['primary'], width=3)
            
            # Company name
            bbox = draw.textbbox((0, 0), company_name, font=fonts['heading'])
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, 50), company_name, fill=colors['primary'], font=fonts['heading'])
        except Exception as e:
            logger.error(f"Error drawing header section: {e}")
    
    def draw_main_title(self, draw, title, colors, fonts, width, y):
        """Draw main title with styling"""
        try:
            # Wrap text if too long
            max_chars = 25
            if len(title) > max_chars:
                words = title.split()
                lines = []
                current_line = []
                for word in words:
                    if len(' '.join(current_line + [word])) <= max_chars:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append(' '.join(current_line))
            else:
                lines = [title]
            
            total_height = len(lines) * 60
            start_y = y - total_height // 2
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=fonts['title'])
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                
                # Add text shadow
                draw.text((x+3, start_y + i*60 + 3), line, fill=(0, 0, 0, 77), font=fonts['title'])
                draw.text((x, start_y + i*60), line, fill=colors['accent'], font=fonts['title'])
        except Exception as e:
            logger.error(f"Error drawing main title: {e}")
    
    def draw_price_badge(self, draw, price, colors, fonts, width, y):
        """Draw attractive price badge"""
        try:
            price_text = f"Starting From ₹{price:,.0f}"
            bbox = draw.textbbox((0, 0), price_text, font=fonts['heading'])
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Badge background
            badge_width = text_width + 40
            badge_height = text_height + 20
            x = (width - badge_width) // 2
            
            # Create starburst effect
            self.draw_starburst(draw, x + badge_width//2, y + badge_height//2, 60, colors['secondary'])
            
            # Badge rectangle
            self.add_rounded_rectangle(draw, [x, y, x + badge_width, y + badge_height], 
                                     25, fill=colors['secondary'], outline=colors['primary'], width=3)
            
            # Price text
            text_x = x + (badge_width - text_width) // 2
            text_y = y + (badge_height - text_height) // 2
            draw.text((text_x, text_y), price_text, fill=colors['primary'], font=fonts['heading'])
        except Exception as e:
            logger.error(f"Error drawing price badge: {e}")
    
    def draw_package_badge(self, draw, badge_text, colors, fonts, width, y):
        """Draw package type badge"""
        try:
            bbox = draw.textbbox((0, 0), badge_text, font=fonts['subheading'])
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            badge_width = text_width + 30
            badge_height = text_height + 15
            x = (width - badge_width) // 2
            
            # Badge with different color
            badge_color = '#FF4500' if 'LUXURY' in badge_text else '#32CD32'
            self.add_rounded_rectangle(draw, [x, y, x + badge_width, y + badge_height], 
                                     15, fill=badge_color)
            
            text_x = x + (badge_width - text_width) // 2
            text_y = y + (badge_height - text_height) // 2
            draw.text((text_x, text_y), badge_text, fill='white', font=fonts['subheading'])
        except Exception as e:
            logger.error(f"Error drawing package badge: {e}")
    
    def draw_duration_info(self, draw, duration, colors, fonts, width, y):
        """Draw duration information"""
        try:
            duration_text = f"📅 Duration: {duration}"
            bbox = draw.textbbox((0, 0), duration_text, font=fonts['body'])
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            
            # Background
            self.add_rounded_rectangle(draw, [x-15, y-10, x + text_width + 15, y + 35], 
                                     10, fill=(255, 255, 255, 204))
            
            draw.text((x, y), duration_text, fill=colors['text'], font=fonts['body'])
        except Exception as e:
            logger.error(f"Error drawing duration info: {e}")
    
    def draw_features_section(self, draw, features, colors, fonts, width, start_y):
        """Draw features section with icons"""
        try:
            # Section title
            title = "Package Includes:"
            bbox = draw.textbbox((0, 0), title, font=fonts['heading'])
            title_width = bbox[2] - bbox[0]
            x = (width - title_width) // 2
            draw.text((x, start_y), title, fill=colors['accent'], font=fonts['heading'])
            
            # Features background
            features_height = len(features) * 35 + 40
            self.add_rounded_rectangle(draw, [40, start_y + 50, width-40, start_y + 50 + features_height], 
                                     20, fill=(255, 255, 255, 230), outline=colors['primary'], width=2)
            
            # Draw features
            y_offset = start_y + 70
            for feature in features:
                # Feature text with better spacing
                draw.text((70, y_offset), feature, fill=colors['text'], font=fonts['body'])
                y_offset += 35
        except Exception as e:
            logger.error(f"Error drawing features section: {e}")
    
    def draw_description(self, draw, description, colors, fonts, width, y):
        """Draw package description"""
        try:
            # Wrap text
            max_chars = 60
            wrapped_text = textwrap.fill(description, width=max_chars)
            lines = wrapped_text.split('\n')
            
            total_height = len(lines) * 30
            
            # Background
            self.add_rounded_rectangle(draw, [40, y-10, width-40, y + total_height + 20], 
                                     15, fill=(255, 255, 255, 204))
            
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=fonts['body'])
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text((x, y + i*30), line, fill=colors['text'], font=fonts['body'])
        except Exception as e:
            logger.error(f"Error drawing description: {e}")
    
    def draw_contact_section(self, draw, user_data, colors, fonts, width, height):
        """Draw contact information section"""
        try:
            contact_y = height - 100
            
            # Background
            self.add_rounded_rectangle(draw, [30, contact_y-10, width-30, height-20], 
                                     15, fill=colors['primary'])
            
            # Contact info
            phone = user_data.get('phone', '')
            email = user_data.get('email', '')
            
            if phone:
                phone_text = f"📞 {phone}"
                bbox = draw.textbbox((0, 0), phone_text, font=fonts['small'])
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text((x, contact_y + 10), phone_text, fill=colors['accent'], font=fonts['small'])
            
            if email:
                email_text = f"📧 {email}"
                bbox = draw.textbbox((0, 0), email_text, font=fonts['small'])
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text((x, contact_y + 35), email_text, fill=colors['accent'], font=fonts['small'])
        except Exception as e:
            logger.error(f"Error drawing contact section: {e}")
    
    def draw_cta_button(self, draw, colors, fonts, width, y):
        """Draw call-to-action button"""
        try:
            cta_text = "BOOK NOW!"
            bbox = draw.textbbox((0, 0), cta_text, font=fonts['heading'])
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            button_width = text_width + 60
            button_height = text_height + 20
            x = (width - button_width) // 2
            
            # Button with gradient effect (simplified)
            self.add_rounded_rectangle(draw, [x, y, x + button_width, y + button_height], 
                                     25, fill='#FF4500', outline='#FF6347', width=3)
            
            # Button text
            text_x = x + (button_width - text_width) // 2
            text_y = y + (button_height - text_height) // 2
            draw.text((text_x, text_y), cta_text, fill='white', font=fonts['heading'])
        except Exception as e:
            logger.error(f"Error drawing CTA button: {e}")
    
    def draw_starburst(self, draw, cx, cy, radius, color):
        """Draw a starburst effect"""
        try:
            points = []
            num_points = 8
            for i in range(num_points * 2):
                angle = i * math.pi / num_points
                if i % 2 == 0:
                    r = radius
                else:
                    r = radius * 0.5
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((x, y))
            
            draw.polygon(points, fill=color)
        except Exception as e:
            logger.error(f"Error drawing starburst: {e}")
    
    def generate_poster(self, poster_data, user_data, template_path=None, format='jpg'):
        """Main method to generate poster"""
        try:
            logger.info(f"Starting poster generation for package: {poster_data.get('package_name', 'Unknown')}")
            
            # Get package details
            package_details = self.get_package_details(poster_data['package_type'])
            logger.info(f"Package details retrieved for type: {poster_data['package_type']}")
            
            # Create attractive poster
            poster_img = self.create_attractive_poster(poster_data, user_data, package_details, format)
            logger.info(f"Poster image created successfully")
            
            # Save based on format
            output = BytesIO()
            
            if format == 'pdf':
                logger.info("Creating PDF from image")
                return self.create_pdf_from_image(poster_img, poster_data, user_data, package_details)
            else:
                logger.info(f"Saving image in {format.upper()} format")
                poster_img.save(output, format=format.upper(), quality=95, optimize=True)
                output.seek(0)
                logger.info("Poster generated successfully")
                return output
                
        except Exception as e:
            logger.error(f"Error generating poster: {str(e)}", exc_info=True)
            # Return None to maintain compatibility with your existing error handling
            return None
    
    def create_pdf_from_image(self, img, poster_data, user_data, package_details):
        """Create PDF from generated image with metadata"""
        try:
            buffer = BytesIO()
            
            # Convert PIL image to bytes
            img_buffer = BytesIO()
            img.save(img_buffer, format='JPEG', quality=95)
            img_buffer.seek(0)
            
            # Create PDF
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Calculate image dimensions to fit A4
            a4_width, a4_height = A4
            img_width, img_height = img.size
            
            # Calculate scaling to fit page with margins
            margin = 50
            max_width = a4_width - 2 * margin
            max_height = a4_height - 2 * margin
            
            scale_width = max_width / img_width
            scale_height = max_height / img_height
            scale = min(scale_width, scale_height)
            
            new_width = img_width * scale
            new_height = img_height * scale
            
            # Center the image
            x = margin + (max_width - new_width) / 2
            y = margin + (max_height - new_height) / 2
            
            # Draw image
            c.drawImage(ImageReader(img_buffer), x, y, width=new_width, height=new_height)
            
            # Add PDF metadata
            c.setTitle(f"{poster_data.get('package_name', 'Travel Package')} - {user_data.get('company_name', 'Travel Company')}")
            c.setAuthor(user_data.get('company_name', 'Travel Company'))
            c.setSubject(f"Travel Package: {poster_data.get('package_name', 'Unknown Package')}")
            c.setKeywords(f"travel, umrah, hajj, {poster_data.get('package_type', '')}")
            
            # Save PDF
            c.save()
            buffer.seek(0)
            
            logger.info("PDF created successfully from image")
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating PDF from image: {e}")
            # Fallback: return image as JPEG
            fallback_buffer = BytesIO()
            img.save(fallback_buffer, format='JPEG', quality=95)
            fallback_buffer.seek(0)
            return fallback_buffer
    
    def create_thumbnail(self, poster_img, size=(300, 300)):
        """Create thumbnail of the poster"""
        try:
            thumbnail = poster_img.copy()
            thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
            
            thumb_buffer = BytesIO()
            thumbnail.save(thumb_buffer, format='JPEG', quality=85)
            thumb_buffer.seek(0)
            
            return thumb_buffer
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    def add_watermark(self, img, watermark_text, user_data):
        """Add subtle watermark to the image"""
        try:
            # Create a transparent overlay
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Load font for watermark
            try:
                font_path = os.path.join(self.font_path, 'arial.ttf')
                if os.path.exists(font_path):
                    watermark_font = ImageFont.truetype(font_path, 24)
                else:
                    watermark_font = ImageFont.load_default()
            except:
                watermark_font = ImageFont.load_default()
            
            # Get text size
            bbox = draw.textbbox((0, 0), watermark_text, font=watermark_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position watermark at bottom right
            x = img.width - text_width - 20
            y = img.height - text_height - 20
            
            # Draw watermark with transparency
            draw.text((x, y), watermark_text, fill=(255, 255, 255, 128), font=watermark_font)
            
            # Composite with original image
            watermarked = Image.alpha_composite(img.convert('RGBA'), overlay)
            return watermarked.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
            return img
    
    def validate_poster_data(self, poster_data):
        """Validate poster data before processing"""
        required_fields = ['package_name', 'package_type', 'price']
        missing_fields = []
        
        for field in required_fields:
            if field not in poster_data or not poster_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate price is numeric
        try:
            float(poster_data['price'])
        except (ValueError, TypeError):
            raise ValueError("Price must be a valid number")
        
        # Validate package type
        valid_types = list(self.get_package_details('umrah_classic').keys()) + [
            'umrah_classic', 'umrah_delux', 'umrah_luxury',
            'hajj_classic', 'hajj_delux', 'hajj_luxury',
            'ramadan_early', 'ramadan_laylat', 'ramadan_full'
        ]
        
        if poster_data['package_type'] not in valid_types:
            logger.warning(f"Unknown package type: {poster_data['package_type']}, using default")
            poster_data['package_type'] = 'umrah_classic'
        
        return True
    
    def validate_user_data(self, user_data):
        """Validate user data"""
        if not user_data:
            raise ValueError("User data is required")
        
        # Company name is required
        if not user_data.get('company_name'):
            raise ValueError("Company name is required")
        
        return True
    
    def get_color_variations(self, base_color):
        """Generate color variations for themes"""
        try:
            # Convert hex to RGB
            base_rgb = tuple(int(base_color[i:i+2], 16) for i in (1, 3, 5))
            
            # Generate lighter and darker variations
            lighter = tuple(min(255, int(c * 1.2)) for c in base_rgb)
            darker = tuple(max(0, int(c * 0.8)) for c in base_rgb)
            
            # Convert back to hex
            lighter_hex = '#{:02x}{:02x}{:02x}'.format(*lighter)
            darker_hex = '#{:02x}{:02x}{:02x}'.format(*darker)
            
            return {
                'base': base_color,
                'lighter': lighter_hex,
                'darker': darker_hex
            }
        except Exception as e:
            logger.error(f"Error generating color variations: {e}")
            return {
                'base': base_color,
                'lighter': base_color,
                'darker': base_color
            }
    
    def create_social_media_variants(self, poster_img):
        """Create different sized variants for social media"""
        variants = {}
        
        sizes = {
            'instagram_post': (1080, 1080),
            'instagram_story': (1080, 1920),
            'facebook_post': (1200, 630),
            'twitter_post': (1024, 512),
            'linkedin_post': (1104, 736)
        }
        
        try:
            for variant_name, size in sizes.items():
                # Create new image with target size
                variant = Image.new('RGB', size, (255, 255, 255))
                
                # Calculate scaling and positioning
                original_ratio = poster_img.width / poster_img.height
                target_ratio = size[0] / size[1]
                
                if original_ratio > target_ratio:
                    # Original is wider, fit to height
                    new_height = size[1]
                    new_width = int(new_height * original_ratio)
                    resized = poster_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Center horizontally
                    x = (size[0] - new_width) // 2
                    y = 0
                else:
                    # Original is taller, fit to width
                    new_width = size[0]
                    new_height = int(new_width / original_ratio)
                    resized = poster_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Center vertically
                    x = 0
                    y = (size[1] - new_height) // 2
                
                # Paste resized image onto variant
                if x >= 0 and y >= 0:
                    variant.paste(resized, (x, y))
                else:
                    # Crop if image is larger than target
                    crop_x = max(0, -x)
                    crop_y = max(0, -y)
                    crop_width = min(resized.width - crop_x, size[0])
                    crop_height = min(resized.height - crop_y, size[1])
                    
                    cropped = resized.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
                    variant.paste(cropped, (max(0, x), max(0, y)))
                
                # Save variant
                variant_buffer = BytesIO()
                variant.save(variant_buffer, format='JPEG', quality=90)
                variant_buffer.seek(0)
                variants[variant_name] = variant_buffer
                
        except Exception as e:
            logger.error(f"Error creating social media variants: {e}")
        
        return variants
    
    def cleanup_temp_files(self):
        """Clean up temporary files if any"""
        try:
            # This method can be used to clean up any temporary files
            # created during poster generation if needed
            pass
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_package_stats(self):
        """Get statistics about available packages"""
        try:
            all_details = {}
            package_types = [
                'umrah_classic', 'umrah_delux', 'umrah_luxury',
                'hajj_classic', 'hajj_delux', 'hajj_luxury', 
                'ramadan_early', 'ramadan_laylat', 'ramadan_full'
            ]
            
            for pkg_type in package_types:
                all_details[pkg_type] = self.get_package_details(pkg_type)
            
            stats = {
                'total_packages': len(all_details),
                'umrah_packages': 3,
                'hajj_packages': 3,
                'ramadan_packages': 3,
                'available_colors': len(set(
                    details['color_scheme']['primary'] 
                    for details in all_details.values()
                ))
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting package stats: {e}")
            return {}