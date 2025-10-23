import importlib.resources

from dataclasses import dataclass
from struct import pack
from pathlib import Path


@dataclass
class Header:
    """Various settings needed for GX header generation"""

    # constants
    MAGIC_BYTES = b"\x78\x67\x63\x6f\x64\x65\x20\x31\x2e\x30\x0a\x00\x00\x00\x00\x00"
    BMP_OFFSET = b"\x3a\x00\x00\x00"
    GCODE_OFFSET = b"\xb0\x38\x00\x00"
    FILAMENT_USAGE_2 = b"\x00\x00\x00\x00"
    MULTI_EXTRUDER_TYPE = b"\x0b\x00"
    UNDOCUMENTED_VALUE_1 = b"\x64\x00"
    UNDOCUMENTED_VALUE_2 = b"\x01\xff"

    # numeric values
    print_time_seconds: int
    filament_usage_mm: int
    layer_height_microns: int
    shell_count: int
    print_speed_mms: int
    hotbed_temperature_degrees: int
    extruder_temp_degrees: int

    # optional override for the BMP thumbnail.  When provided, this value will be
    # used instead of the bundled `thumbnail.bmp`.  It must contain a complete
    # 24‑bit BMP (80×60) including its 54‑byte header and pixel data.
    thumbnail_override: bytes | None = None

    # byte values
    print_time_bytes: bytes = b""
    filament_usage_bytes: bytes = b""
    layer_height_bytes: bytes = b""
    shell_count_bytes: bytes = b""
    print_speed_bytes: bytes = b""
    hotbed_temperature_bytes: bytes = b""
    extruder_temp_bytes: bytes = b""
    thumbnail_bytes: bytes = b""

    # assembled header, without BMP
    assembled_header: bytes = b""

    def __post_init__(self):
        self.print_time_bytes: bytes = pack("i", self.print_time_seconds)
        self.filament_usage_bytes: bytes = pack("i", self.filament_usage_mm)
        self.layer_height_bytes: bytes = pack("h", self.layer_height_microns)
        self.shell_count_bytes: bytes = pack("h", self.shell_count)
        self.print_speed_bytes: bytes = pack("h", self.print_speed_mms)
        self.hotbed_temperature_bytes: bytes = pack(
            "h", self.hotbed_temperature_degrees
        )
        self.extruder_temp_bytes: bytes = pack("h", self.extruder_temp_degrees)

        # Select thumbnail: use override if provided, otherwise fall back to bundled BMP.
        if self.thumbnail_override is not None:
            self.thumbnail_bytes = self.thumbnail_override
        else:
            thumbnail = importlib.resources.files("gx_converter").joinpath("thumbnail.bmp")
            self.thumbnail_bytes = thumbnail.read_bytes()
        # with open(Path(thumbnail), "rb") as f:
        #     self.thumbnail_bytes = f.read()

        self.assembled_header = (
            self.MAGIC_BYTES
            + self.BMP_OFFSET
            + self.GCODE_OFFSET
            + self.GCODE_OFFSET
            + self.print_time_bytes
            + self.filament_usage_bytes
            + self.FILAMENT_USAGE_2
            + self.MULTI_EXTRUDER_TYPE
            + self.layer_height_bytes
            + self.UNDOCUMENTED_VALUE_1
            + self.shell_count_bytes
            + self.print_speed_bytes
            + self.hotbed_temperature_bytes
            + self.extruder_temp_bytes
            + self.extruder_temp_bytes
            + self.UNDOCUMENTED_VALUE_2
            + self.thumbnail_bytes
        )
