import io
from pathlib import Path
from typing import Optional
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from config import EXPORTS_DIR


def generate_styled_qr(data: str, filename_prefix: str = "qr", primary_color: tuple = (34, 158, 217), bg_color: tuple = (15, 23, 42)) -> Path:
    """
    Generates a sleek, high-resolution QR code image with rounded modules and telegram aesthetic.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Render with styled rounded modules
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            back_color=bg_color,
            front_color=primary_color
        )
    )

    output_path = EXPORTS_DIR / f"{filename_prefix}_{abs(hash(data)) % 1000000}.png"
    img.save(str(output_path), format="PNG")
    return output_path
