"""g_code_property_extractor.py

This module contains the GCodePropertyExtractor class, which is used for retrieving various
properties in the g-code to be used in gx header generation.
"""

from re import search, RegexFlag


class GCodePropertyExtractor:
    """Methods for retrieving properties in g-code"""

    @staticmethod
    def get_print_time(gcode: str) -> int:
        """Get print time from g-code

        Args:
            gcode: original g-code

        Returns:
            Print time
        """

        # Try Bambu/Orca style first: "; estimated printing time (normal mode) = 3h 34m 11s"
        time_sec = GCodePropertyExtractor._extract_estimated_print_time(gcode)
        if time_sec:
            return time_sec
        # Fallback to Cura style: ";TIME:399"
        return GCodePropertyExtractor._extract_comment_value("TIME", gcode)

    @staticmethod
    def get_layer_height(gcode: str) -> int:
        """Get layer height in microns (µ) from g-code

        Args:
            gcode: original g-code

        Returns:
            Layer height
        """

        # Look for "default_print_profile = 0.20mm" first
        height_microns = GCodePropertyExtractor._extract_layer_height_profile(gcode)
        if height_microns:
            return height_microns
        height = GCodePropertyExtractor._extract_comment_value("Layer height", gcode)
        return height * 10

    @staticmethod
    def get_filament_usage(gcode: str) -> int:
        """Get filament usage from g-code

        Args:
            gcode: original g-code

        Returns:
            Filament usage
        """

        # Parse Bambu/Orca style: "; filament used [mm] = 7114.77"
        usage_mm = GCodePropertyExtractor._extract_filament_used_mm(gcode)
        if usage_mm:
            return usage_mm
        # Fallback to Cura style: ";Filament used: 0.113383m"
        return GCodePropertyExtractor._extract_comment_value("Filament used", gcode)

    @staticmethod
    def get_nozzle_temperature(gcode: str) -> int:
        """Get nozzle temperature from g-code

        Args:
            gcode: original g-code

        Returns:
            Nozzle temperature
        """

        return GCodePropertyExtractor._extract_command_value("M104", "S", gcode)

    @staticmethod
    def get_hotbed_temperature(gcode: str) -> int:
        """Get hotbed temperature from g-code

        Args:
            gcode: original g-code

        Returns:
            Hotbed temperature
        """

        return GCodePropertyExtractor._extract_command_value("M140", "S", gcode)

    @staticmethod
    def _extract_comment_value(comment: str, gcode: str) -> int:
        """Extract a numerical value from g-code

        Args:
            comment: The command containing the value (e.g., TIME)
            gcode: G-code from which to extract

        Returns:
            Numerical value, 0 if failure
        """

        # ;FLAVOR:Marlin
        # ;TIME:399
        # ;Filament used: 0.270103m
        # ;Layer height: 0.18

        result = search(f"^;{comment}:.*", gcode, RegexFlag.MULTILINE)
        if not result:
            return 0

        result = result.group(0)
        value = result.split(":")[1].strip()

        if "m" in value:
            # strip notation and convert meters to mm
            value = value.replace("m", "")
            value_parts = value.split(".")
            value_after_decimal = value_parts[1][:3]
            value = value_parts[0] + value_after_decimal

        # "convert" floats by removing decimal point
        value = value.replace(".", "")

        return int(value)

    @staticmethod
    def _extract_command_value(command: str, value_marker: str, gcode: str) -> int:
        """Extract a numerical value from g-code

        Args:
            command: The command containing the value (e.g., M104)
            value_marker: The marker preceding the desired value (e.g., S)
            gcode: G-code from which to extract

        Returns:
            Numerical value, 0 if failure
        """

        result = search(f"^{command} {value_marker}.*", gcode, RegexFlag.MULTILINE)
        if not result:
            return 0

        result = result.group(0)
        value = 0

        for argument in result.split():
            if value_marker in argument:
                value = int(argument[1:])
                break

        return value

    @staticmethod
    def _extract_estimated_print_time(gcode: str) -> int:
        """
        Extract print time in seconds from lines like:
            "; estimated printing time (normal mode) = 3h 34m 11s"
        """
        match = search(r"estimated printing time.*?=\s*(\d+)h\s*(\d+)m\s*(\d+)s",
                       gcode, RegexFlag.IGNORECASE)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s)
        return 0

    @staticmethod
    def _extract_filament_used_mm(gcode: str) -> int:
        """
        Extract filament usage from lines like:
            "; filament used [mm] = 7114.77"
        Returns millimetres rounded to the nearest integer.
        """
        match = search(r"filament used \[mm\]\s*=\s*([\d.]+)", gcode, RegexFlag.IGNORECASE)
        return int(round(float(match.group(1)))) if match else 0

    @staticmethod
    def _extract_layer_height_profile(gcode: str) -> int:
        """
        Extract layer height from lines like:
            "default_print_profile = 0.20mm"
        Returns microns.
        """
        match = search(r"default_print_profile\s*=\s*([\d.]+)mm", gcode, RegexFlag.IGNORECASE)
        return int(round(float(match.group(1)) * 1000)) if match else 0
