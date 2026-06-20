from os import getenv
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_H

# ============= CUSTOMIZATION OPTIONS =============

# Colors (use hex colors or color names)
# QR_FOREGROUND_COLOR = "#7A9069"  # QR code color (try: "#7a9069", "#2C5F2D", etc.)
QR_FOREGROUND_COLOR = "black"  # QR code color (try: "#7a9069", "#2C5F2D", etc.)
# QR_BACKGROUND_COLOR = "#FFFCF0"  # Background color
QR_BACKGROUND_COLOR = "white"  # Background color

# Logo in center (set path to your logo image, or None for no logo)
LOGO_PATH = None  # "static/media/wedding_logo.png"  # Example: "logo.png" or Path("images/wedding_logo.png")
LOGO_SIZE_RATIO = 0.25  # Logo size as fraction of QR code (0.2-0.3 recommended)

# Add table number text below QR code
ADD_TABLE_NUMBER = False
TEXT_COLOR = "#7A9069"
TEXT_FONT_SIZE = 36  # Font size for table number

# QR Code settings
BOX_SIZE = 10  # Size of each box in the QR code grid
BORDER_SIZE = 2  # Border around QR code

# ==================================================

load_dotenv(".env")
SECRET_TOKEN = getenv("SECRET_TOKEN")

# Create output directory
output_dir = Path("qr_codes")
output_dir.mkdir(exist_ok=True)

urls = [
    f"https://danilocatone.com/wedding-photos/table/{i}?t={SECRET_TOKEN}"
    for i in range(1, 17)
] + ["https://danilocatone.com/wedding-photos/menu?t=wmo8RQ"]


def add_logo_to_qr(qr_img: Image.Image, logo_path: Path | str) -> Image.Image:
    """Add a logo image to the center of the QR code."""
    logo = Image.open(logo_path)

    # Calculate logo size
    qr_width, qr_height = qr_img.size
    logo_size = int(qr_width * LOGO_SIZE_RATIO)

    # Resize logo maintaining aspect ratio
    logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)

    # Calculate position to center the logo
    logo_pos = ((qr_width - logo.width) // 2, (qr_height - logo.height) // 2)

    # Paste logo onto QR code
    qr_img.paste(logo, logo_pos, logo if logo.mode == "RGBA" else None)
    return qr_img


def add_text_label(qr_img: Image.Image, text: str) -> Image.Image:
    """Add text label below the QR code."""
    qr_width, qr_height = qr_img.size

    # Create new image with space for text
    padding = 20
    text_height = TEXT_FONT_SIZE + padding * 2
    new_height = qr_height + text_height

    new_img = Image.new("RGB", (qr_width, new_height), QR_BACKGROUND_COLOR)
    new_img.paste(qr_img, (0, 0))

    # Draw text
    draw = ImageDraw.Draw(new_img)

    # Try to use a nice font, fallback to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", TEXT_FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (qr_width - text_width) // 2
    text_y = qr_height + padding

    draw.text((text_x, text_y), text, fill=TEXT_COLOR, font=font)

    return new_img


print(f"Generating QR codes in '{output_dir}/' folder...")
print(f"Colors: {QR_FOREGROUND_COLOR} on {QR_BACKGROUND_COLOR}")
if LOGO_PATH:
    print(f"Logo: {LOGO_PATH}")
if ADD_TABLE_NUMBER:
    print("Adding table numbers")
print()

for i, url in enumerate(urls, start=1):
    # Create QR code with high error correction (needed for logos)
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,  # High error correction for logos
        box_size=BOX_SIZE,
        border=BORDER_SIZE,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate image with custom colors
    img = qr.make_image(fill_color=QR_FOREGROUND_COLOR, back_color=QR_BACKGROUND_COLOR)
    img = img.convert("RGB")  # type: ignore

    # Add logo if specified
    if LOGO_PATH and Path(LOGO_PATH).exists():
        img = add_logo_to_qr(img, LOGO_PATH)

    # Add table number text if enabled
    if ADD_TABLE_NUMBER:
        img = add_text_label(img, f"Table {i}")

    # Save to file
    if url == urls[-1]:  # Last URL is the menu
        filename = output_dir / "menu_qr.png"
    else:
        filename = output_dir / f"table_{i}_qr.png"
    img.save(filename)
    print(f"✓ Created {filename}")

print(f"\nSuccessfully generated {len(urls)} QR codes!")
