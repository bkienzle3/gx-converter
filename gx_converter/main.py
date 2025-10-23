"""main.py

Main entry point for gx_converter. This script converts gcode created in Cura to a format that
can be used with current firmware versions of FlashForge Adventurer 3 and Monoprice Voxel 3"""

import argparse

from pathlib import Path

from .g_code_property_extractor import GCodePropertyExtractor
from .g_code_transformer import GCodeTransformer
from .header import Header

import base64
import re
from io import BytesIO
from PIL import Image


# -----------------------------------------------------------------------------
# Thumbnail extraction helper
def extract_thumbnail_from_gcode(gcode: str) -> bytes | None:
    """
    Attempt to extract a thumbnail image embedded in the g-code comments.
    If found, decode the base64 PNG, resize to 80×60 and save as a 24‑bit BMP.
    Returns the BMP bytes (including header), or None if no valid thumbnail is found.
    """
    match = re.search(
        r";\s*thumbnail begin\s+(\d+)x(\d+)\s+\d+[\s\n]+([\s\S]*?)\s*;\s*thumbnail end",
        gcode,
        re.MULTILINE,
    )
    if not match:
        return None
    # Strip leading '; ' and concatenate base64 lines
    b64_data = "".join(line.lstrip("; ").strip() for line in match.group(3).splitlines())
    try:
        png_bytes = base64.b64decode(b64_data)
    except Exception:
        return None
    try:
        with Image.open(BytesIO(png_bytes)) as img:
            img = img.convert("RGB")
            # Resize to 80×60 to match .gx requirements
            img_resized = img.resize((80, 60))
            buffer = BytesIO()
            img_resized.save(buffer, format="BMP")
            bmp = buffer.getvalue()
            # Ensure correct length (54 header + 80*60*3 pixel bytes = 14454)
            if len(bmp) != 14454:
                return None
            return bmp
    except Exception:
        return None


def get_parser():
    parser = argparse.ArgumentParser(
        description="Convert Cura/Bambu/Orca gcode to .gx format"
    )
    parser.add_argument("gcode", type=str, help="File to convert")
    parser.add_argument(
        "--output",
        type=str,
        help="Output file. If not specified, will output based on gcode filename.",
        required=False,
    )
    return parser


def main():
    """Entry point for application"""

    parser = get_parser()
    args = parser.parse_args()

    gcode_file = Path(args.gcode)
    if not gcode_file.exists():
        print("File not found")
        raise SystemExit

    with open(gcode_file, "r") as f:
        code = f.read()

    hotbed_temp = GCodePropertyExtractor.get_hotbed_temperature(code)
    nozzle_temp = GCodePropertyExtractor.get_nozzle_temperature(code)
    print_time = GCodePropertyExtractor.get_print_time(code)
    filament_usage = GCodePropertyExtractor.get_filament_usage(code)
    layer_height = GCodePropertyExtractor.get_layer_height(code)
    shell_count = 3
    print_speed = 60

    code = GCodeTransformer.convert(code)

    # Try to extract a thumbnail from the original g-code and pass it into Header.
    thumbnail_bytes = extract_thumbnail_from_gcode(code)
    header = Header(
        print_time,
        filament_usage,
        layer_height,
        shell_count,
        print_speed,
        hotbed_temp,
        nozzle_temp,
        thumbnail_override=thumbnail_bytes,
    )

    gx = header.assembled_header + code.encode("utf-8")
    output_file = (
        Path(args.output)
        if args.output
        else Path(gcode_file.parent, gcode_file.stem + ".gx")
    )

    with open(output_file, "wb") as f:
        f.write(gx)


if __name__ == "__main__":
    main()
