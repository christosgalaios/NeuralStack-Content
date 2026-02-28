"""
TikTok Video Producer & Editor — turns scripts into upload-ready MP4 videos.

Uses FFmpeg for video assembly and Pillow for frame/text rendering.
Falls back gracefully if either tool is unavailable (scripts still generate,
videos are simply skipped).

All output is 9:16 portrait (1080x1920) at 30 fps — the TikTok standard.
"""

import json
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Color palettes for different moods (bg_color, text_color, accent_color)
COLOR_PALETTES = {
    "dark": {
        "bg": (13, 17, 23),
        "text": (240, 246, 252),
        "accent": (88, 166, 255),
        "secondary": (125, 133, 144),
    },
    "neon": {
        "bg": (10, 10, 10),
        "text": (0, 255, 136),
        "accent": (255, 0, 110),
        "secondary": (0, 200, 255),
    },
    "warm": {
        "bg": (30, 20, 15),
        "text": (255, 237, 209),
        "accent": (255, 159, 67),
        "secondary": (255, 107, 107),
    },
    "ice": {
        "bg": (15, 20, 35),
        "text": (220, 235, 255),
        "accent": (0, 180, 255),
        "secondary": (100, 220, 255),
    },
    "hacker": {
        "bg": (0, 0, 0),
        "text": (0, 255, 65),
        "accent": (0, 200, 50),
        "secondary": (0, 150, 40),
    },
}

# Map format moods to palettes
FORMAT_PALETTE_MAP = {
    "hot_take": "neon",
    "myth_bust": "warm",
    "tutorial": "dark",
    "storytime": "warm",
    "listicle": "ice",
    "pov": "neon",
    "before_after": "ice",
    "one_liner": "dark",
    "quick_fact": "ice",
    "hot_take_snap": "neon",
    "code_flash": "hacker",
    "this_or_that": "neon",
    "wait_for_it": "dark",
    "ratio_bait": "neon",
    "text_story": "dark",
}


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _has_pillow() -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
        return True
    except ImportError:
        return False


def check_dependencies() -> Dict[str, bool]:
    return {
        "ffmpeg": _has_ffmpeg(),
        "pillow": _has_pillow(),
    }


# ---------------------------------------------------------------------------
# Frame Generator — creates individual PNG frames using Pillow
# ---------------------------------------------------------------------------

class FrameGenerator:
    """Generates styled text frames as PNG images for video segments."""

    def __init__(self, palette_name: str = "dark") -> None:
        self.palette = COLOR_PALETTES.get(palette_name, COLOR_PALETTES["dark"])
        self._font_paths = self._find_fonts()

    def _find_fonts(self) -> Dict[str, Optional[str]]:
        """Locate available system fonts."""
        candidates = {
            "bold": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:/Windows/Fonts/arialbd.ttf",
            ],
            "regular": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:/Windows/Fonts/arial.ttf",
            ],
            "mono": [
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
                "C:/Windows/Fonts/consola.ttf",
            ],
        }
        found: Dict[str, Optional[str]] = {}
        for style, paths in candidates.items():
            found[style] = None
            for p in paths:
                if Path(p).exists():
                    found[style] = p
                    break
        return found

    def _get_font(self, style: str = "bold", size: int = 72):
        from PIL import ImageFont
        path = self._font_paths.get(style)
        if path:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                pass
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Word-wrap text to fit within max_width pixels."""
        from PIL import ImageDraw, Image
        dummy = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy)

        words = text.split()
        lines: List[str] = []
        current_line = ""

        for word in words:
            test = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines or [""]

    def generate_text_frame(
        self,
        text: str,
        style: str = "hook",
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate a single styled text frame.

        Styles: hook, body, accent, code, cta, label
        """
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (WIDTH, HEIGHT), self.palette["bg"])
        draw = ImageDraw.Draw(img)

        # Style-dependent sizing and positioning
        configs = {
            "hook": {"font_style": "bold", "font_size": 80, "color": self.palette["text"], "y_center": 0.42},
            "body": {"font_style": "regular", "font_size": 56, "color": self.palette["text"], "y_center": 0.45},
            "accent": {"font_style": "bold", "font_size": 72, "color": self.palette["accent"], "y_center": 0.45},
            "code": {"font_style": "mono", "font_size": 52, "color": self.palette["accent"], "y_center": 0.45},
            "cta": {"font_style": "bold", "font_size": 64, "color": self.palette["accent"], "y_center": 0.55},
            "label": {"font_style": "bold", "font_size": 40, "color": self.palette["secondary"], "y_center": 0.30},
        }
        cfg = configs.get(style, configs["body"])

        font = self._get_font(cfg["font_style"], cfg["font_size"])
        max_text_width = int(WIDTH * 0.82)
        lines = self._wrap_text(text, font, max_text_width)

        # Calculate total text block height
        line_heights = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])

        line_spacing = int(cfg["font_size"] * 0.45)
        total_height = sum(line_heights) + line_spacing * (len(lines) - 1)

        # Start Y position (centered at y_center ratio)
        start_y = int(HEIGHT * cfg["y_center"]) - total_height // 2

        # Draw each line centered horizontally
        current_y = start_y
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (WIDTH - text_width) // 2
            draw.text((x, current_y), line, fill=cfg["color"], font=font)
            current_y += line_heights[i] + line_spacing

        # Add a subtle bottom bar accent
        if style in ("hook", "cta"):
            bar_y = int(HEIGHT * 0.72)
            bar_width = int(WIDTH * 0.3)
            bar_x = (WIDTH - bar_width) // 2
            draw.rectangle(
                [bar_x, bar_y, bar_x + bar_width, bar_y + 4],
                fill=self.palette["accent"],
            )

        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".png"))

        img.save(str(output_path), "PNG")
        return output_path

    def generate_split_frame(
        self,
        left_text: str,
        right_text: str,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Generate a split-screen comparison frame (this vs that / before vs after)."""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (WIDTH, HEIGHT), self.palette["bg"])
        draw = ImageDraw.Draw(img)

        # Divider line
        mid_x = WIDTH // 2
        draw.line([(mid_x, int(HEIGHT * 0.25)), (mid_x, int(HEIGHT * 0.75))],
                  fill=self.palette["secondary"], width=3)

        # "VS" badge
        vs_font = self._get_font("bold", 48)
        bbox = draw.textbbox((0, 0), "VS", font=vs_font)
        vs_w = bbox[2] - bbox[0]
        vs_h = bbox[3] - bbox[1]
        vs_x = mid_x - vs_w // 2
        vs_y = HEIGHT // 2 - vs_h // 2
        # Badge background
        pad = 20
        draw.ellipse(
            [vs_x - pad, vs_y - pad, vs_x + vs_w + pad, vs_y + vs_h + pad],
            fill=self.palette["accent"],
        )
        draw.text((vs_x, vs_y), "VS", fill=self.palette["bg"], font=vs_font)

        # Left side text
        left_font = self._get_font("bold", 48)
        max_side_width = int(WIDTH * 0.38)
        left_lines = self._wrap_text(left_text, left_font, max_side_width)
        left_y = int(HEIGHT * 0.38)
        for line in left_lines:
            bbox = draw.textbbox((0, 0), line, font=left_font)
            lw = bbox[2] - bbox[0]
            lx = (mid_x - lw) // 2
            draw.text((lx, left_y), line, fill=self.palette["text"], font=left_font)
            left_y += int(48 * 1.4)

        # Right side text
        right_lines = self._wrap_text(right_text, left_font, max_side_width)
        right_y = int(HEIGHT * 0.38)
        for line in right_lines:
            bbox = draw.textbbox((0, 0), line, font=left_font)
            rw = bbox[2] - bbox[0]
            rx = mid_x + (mid_x - rw) // 2
            draw.text((rx, right_y), line, fill=self.palette["accent"], font=left_font)
            right_y += int(48 * 1.4)

        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".png"))

        img.save(str(output_path), "PNG")
        return output_path

    def generate_label_frame(
        self,
        label: str,
        main_text: str,
        output_path: Optional[Path] = None,
    ) -> Path:
        """Frame with a small label above the main text (e.g., 'HOT TAKE' + the take)."""
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (WIDTH, HEIGHT), self.palette["bg"])
        draw = ImageDraw.Draw(img)

        # Label
        label_font = self._get_font("bold", 36)
        bbox = draw.textbbox((0, 0), label.upper(), font=label_font)
        lw = bbox[2] - bbox[0]
        label_x = (WIDTH - lw) // 2
        label_y = int(HEIGHT * 0.32)

        # Label background pill
        pill_pad_x, pill_pad_y = 24, 10
        draw.rounded_rectangle(
            [label_x - pill_pad_x, label_y - pill_pad_y,
             label_x + lw + pill_pad_x, label_y + (bbox[3] - bbox[1]) + pill_pad_y],
            radius=20,
            fill=self.palette["accent"],
        )
        draw.text((label_x, label_y), label.upper(), fill=self.palette["bg"], font=label_font)

        # Main text below
        main_font = self._get_font("bold", 68)
        max_w = int(WIDTH * 0.82)
        lines = self._wrap_text(main_text, main_font, max_w)
        current_y = int(HEIGHT * 0.42)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=main_font)
            tw = bbox[2] - bbox[0]
            tx = (WIDTH - tw) // 2
            draw.text((tx, current_y), line, fill=self.palette["text"], font=main_font)
            current_y += int(68 * 1.4)

        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".png"))

        img.save(str(output_path), "PNG")
        return output_path


# ---------------------------------------------------------------------------
# Video Assembler — uses FFmpeg to compose frames into a video
# ---------------------------------------------------------------------------

class VideoAssembler:
    """Assembles PNG frames into timed MP4 video segments using FFmpeg."""

    @staticmethod
    def _parse_timing(timing_str: str) -> Tuple[float, float]:
        """Parse '0-3s' into (start_seconds, end_seconds)."""
        clean = timing_str.replace("s", "").strip()
        parts = clean.split("-")
        try:
            start = float(parts[0])
            end = float(parts[1]) if len(parts) > 1 else start + 3
        except (ValueError, IndexError):
            start, end = 0, 3
        return start, end

    @staticmethod
    def frame_to_segment(
        frame_path: Path,
        duration: float,
        output_path: Path,
        effect: str = "none",
    ) -> bool:
        """
        Convert a static PNG frame into a video segment with optional effects.

        Effects: none, zoom_in, zoom_out, fade_in, shake, ken_burns
        """
        total_frames = int(duration * FPS)

        filter_parts = []

        # Base: loop the image for the duration
        input_args = [
            "-loop", "1",
            "-i", str(frame_path),
            "-t", str(duration),
        ]

        # Apply effects
        if effect == "zoom_in":
            filter_parts.append(
                f"zoompan=z='min(1+on/{total_frames}*0.15,1.15)'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )
        elif effect == "zoom_out":
            filter_parts.append(
                f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.15/{total_frames},1.0))'"
                f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )
        elif effect == "fade_in":
            filter_parts.append(f"format=yuv420p,fade=t=in:st=0:d={min(0.5, duration / 2)}")
        elif effect == "shake":
            # Subtle shake effect via random displacement
            filter_parts.append(
                f"crop=w={WIDTH - 20}:h={HEIGHT - 20}"
                f":x='5+random(1)*10':y='5+random(1)*10',"
                f"scale={WIDTH}:{HEIGHT}"
            )
        elif effect == "ken_burns":
            filter_parts.append(
                f"zoompan=z='min(1+on/{total_frames}*0.08,1.08)'"
                f":x='iw/10*on/{total_frames}':y='ih/2-(ih/zoom/2)'"
                f":d={total_frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
            )

        if not filter_parts:
            filter_parts.append(f"format=yuv420p")

        filter_str = ",".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd, check=True, capture_output=True, timeout=60,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("FFmpeg segment creation failed: %s", e)
            return False

    @staticmethod
    def concatenate_segments(
        segment_paths: List[Path],
        output_path: Path,
        crossfade_duration: float = 0.15,
    ) -> bool:
        """Concatenate multiple video segments into one final MP4."""
        if not segment_paths:
            return False

        # If only one segment, just copy it
        if len(segment_paths) == 1:
            shutil.copy2(str(segment_paths[0]), str(output_path))
            return True

        # Use FFmpeg concat demuxer
        concat_file = Path(tempfile.mktemp(suffix=".txt"))
        try:
            lines = [f"file '{seg}'" for seg in segment_paths]
            concat_file.write_text("\n".join(lines), encoding="utf-8")

            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-r", str(FPS),
                str(output_path),
            ]

            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("FFmpeg concat failed: %s", e)
            return False
        finally:
            concat_file.unlink(missing_ok=True)

    @staticmethod
    def add_audio_track(
        video_path: Path,
        output_path: Path,
        duration: float,
    ) -> bool:
        """Add a silent audio track (needed for TikTok upload compatibility)."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={duration}",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("FFmpeg audio track failed: %s", e)
            return False


# ---------------------------------------------------------------------------
# Video Editor — post-production capabilities
# ---------------------------------------------------------------------------

class VideoEditor:
    """Post-production editing: trim, overlay text, adjust speed, add captions."""

    @staticmethod
    def trim(input_path: Path, output_path: Path, start: float, end: float) -> bool:
        """Trim a video to a specific time range."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-ss", str(start),
            "-to", str(end),
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Trim failed: %s", e)
            return False

    @staticmethod
    def adjust_speed(input_path: Path, output_path: Path, speed: float = 1.0) -> bool:
        """Speed up or slow down a video. speed=2.0 means 2x faster."""
        pts_factor = 1.0 / speed
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", f"setpts={pts_factor}*PTS",
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Speed adjust failed: %s", e)
            return False

    @staticmethod
    def add_text_overlay(
        input_path: Path,
        output_path: Path,
        text: str,
        position: str = "bottom",
        font_size: int = 42,
        font_color: str = "white",
        start_time: float = 0,
        end_time: Optional[float] = None,
    ) -> bool:
        """Burn a text overlay onto an existing video."""
        # Position mappings
        positions = {
            "center": f"x=(w-text_w)/2:y=(h-text_h)/2",
            "top": f"x=(w-text_w)/2:y=h*0.08",
            "bottom": f"x=(w-text_w)/2:y=h*0.85",
        }
        pos_str = positions.get(position, positions["bottom"])

        # Find a usable font
        font_file = None
        for candidate in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]:
            if Path(candidate).exists():
                font_file = candidate
                break

        # Escape text for FFmpeg drawtext
        safe_text = text.replace("'", "'\\''").replace(":", "\\:")

        filter_str = (
            f"drawtext=text='{safe_text}'"
            f":fontsize={font_size}:fontcolor={font_color}"
            f":{pos_str}"
        )

        if font_file:
            filter_str += f":fontfile='{font_file}'"

        if end_time is not None:
            filter_str += f":enable='between(t,{start_time},{end_time})'"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Text overlay failed: %s", e)
            return False

    @staticmethod
    def add_caption_track(
        input_path: Path,
        output_path: Path,
        captions: List[Dict[str, Any]],
        font_size: int = 40,
    ) -> bool:
        """
        Burn timed captions/subtitles onto a video.

        captions: [{"text": "...", "start": 0.0, "end": 3.0}, ...]
        """
        font_file = None
        for candidate in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]:
            if Path(candidate).exists():
                font_file = candidate
                break

        filter_parts = []
        for cap in captions:
            safe_text = cap["text"].replace("'", "'\\''").replace(":", "\\:")
            part = (
                f"drawtext=text='{safe_text}'"
                f":fontsize={font_size}:fontcolor=white"
                f":borderw=3:bordercolor=black"
                f":x=(w-text_w)/2:y=h*0.82"
                f":enable='between(t,{cap['start']},{cap['end']})'"
            )
            if font_file:
                part += f":fontfile='{font_file}'"
            filter_parts.append(part)

        filter_str = ",".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning("Caption burn failed: %s", e)
            return False


# ---------------------------------------------------------------------------
# TikTok Video Producer — orchestrates the full production pipeline
# ---------------------------------------------------------------------------

# Map segment roles to visual effects
ROLE_EFFECTS = {
    "hook": "zoom_in",
    "hook_text": "zoom_in",
    "bomb_drop": "zoom_in",
    "text_hook": "fade_in",
    "punchline": "shake",
    "take_drop": "shake",
    "fact_drop": "zoom_out",
    "reveal": "zoom_in",
    "result": "zoom_out",
    "result_flash": "zoom_out",
    "cta": "fade_in",
    "end_card": "fade_in",
    "text_cta": "fade_in",
    "transition": "fade_in",
    "tension_build": "shake",
    "setup": "ken_burns",
    "context": "ken_burns",
    "before": "ken_burns",
    "after": "zoom_in",
}

# Map segment roles to text frame styles
ROLE_FRAME_STYLES = {
    "hook": "hook",
    "hook_text": "hook",
    "bomb_drop": "hook",
    "text_hook": "hook",
    "punchline": "accent",
    "take_drop": "accent",
    "fact_drop": "accent",
    "setup": "body",
    "context": "body",
    "argument": "body",
    "proof": "body",
    "flip": "body",
    "myth_statement": "body",
    "debunk": "body",
    "reality": "body",
    "conflict": "body",
    "turning_point": "body",
    "lesson": "body",
    "discovery": "accent",
    "payoff": "accent",
    "before": "body",
    "after": "accent",
    "breakdown": "body",
    "demo_flash": "code",
    "result_flash": "accent",
    "reveal": "accent",
    "versus_reveal": "body",
    "your_pick": "accent",
    "cta": "cta",
    "end_card": "cta",
    "text_cta": "cta",
    "text_punch": "accent",
    "result": "accent",
    "hold": "hook",
    "stare_out": "hook",
    "smirk_out": "cta",
    "reaction_beat": "accent",
    "tension_build": "hook",
    "bonus": "accent",
    "step_1": "body",
    "step_2": "body",
    "step_3": "body",
    "item_1": "body",
    "item_2": "body",
    "item_3": "body",
}


class TikTokProducer:
    """
    End-to-end video producer. Takes a TikTokScript object and outputs a
    ready-to-upload MP4 file.
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assembler = VideoAssembler()
        self.editor = VideoEditor()

    def produce(self, script: "Any", add_captions: bool = True) -> Optional[Path]:
        """
        Produce a complete TikTok video from a script.

        Returns the path to the final MP4, or None if production failed.
        """
        deps = check_dependencies()
        if not deps["ffmpeg"] or not deps["pillow"]:
            missing = [k for k, v in deps.items() if not v]
            logger.warning(
                "Video production skipped — missing dependencies: %s",
                ", ".join(missing),
            )
            return None

        # Determine palette
        palette_name = FORMAT_PALETTE_MAP.get(script.format_name, "dark")
        frame_gen = FrameGenerator(palette_name)

        work_dir = Path(tempfile.mkdtemp(prefix="tiktok_prod_"))
        segment_videos: List[Path] = []

        try:
            # --- Generate frames and segment videos ---
            for i, seg in enumerate(script.script_segments):
                role = seg.get("role", "body")
                text = seg.get("text", "")
                timing = seg.get("timing", "0-3s")
                _, end = self.assembler._parse_timing(timing)
                start, _ = self.assembler._parse_timing(timing)
                duration = max(end - start, 0.5)

                # Generate the frame
                frame_style = ROLE_FRAME_STYLES.get(role, "body")

                if role == "versus_reveal":
                    # Split screen for this-or-that
                    parts = text.split("Right:")
                    left = parts[0].replace("Left:", "").strip() if parts else text
                    right = parts[1].strip() if len(parts) > 1 else ""
                    frame_path = frame_gen.generate_split_frame(
                        left, right,
                        output_path=work_dir / f"frame_{i:03d}.png",
                    )
                elif role in ("hook_text", "bomb_drop", "text_hook") and script.format_name in (
                    "hot_take_snap", "ratio_bait", "quick_fact"
                ):
                    # Label + text style for short format hooks
                    labels = {
                        "hot_take_snap": "HOT TAKE",
                        "ratio_bait": "HOT TAKE",
                        "quick_fact": "DID YOU KNOW?",
                    }
                    frame_path = frame_gen.generate_label_frame(
                        labels.get(script.format_name, ""),
                        text,
                        output_path=work_dir / f"frame_{i:03d}.png",
                    )
                else:
                    frame_path = frame_gen.generate_text_frame(
                        text,
                        style=frame_style,
                        output_path=work_dir / f"frame_{i:03d}.png",
                    )

                # Convert frame to video segment with effect
                effect = ROLE_EFFECTS.get(role, "none")
                seg_video = work_dir / f"seg_{i:03d}.mp4"

                success = self.assembler.frame_to_segment(
                    frame_path, duration, seg_video, effect=effect,
                )
                if success and seg_video.exists():
                    segment_videos.append(seg_video)
                else:
                    logger.warning("Failed to create segment %d for role '%s'", i, role)

            if not segment_videos:
                logger.warning("No segments produced for script: %s", script.topic)
                return None

            # --- Concatenate all segments ---
            raw_video = work_dir / "raw_concat.mp4"
            if not self.assembler.concatenate_segments(segment_videos, raw_video):
                logger.warning("Failed to concatenate segments for: %s", script.topic)
                return None

            # --- Add burnt-in captions if requested ---
            if add_captions:
                captioned_video = work_dir / "captioned.mp4"
                captions = self._build_caption_track(script)
                if captions and self.editor.add_caption_track(raw_video, captioned_video, captions):
                    current_video = captioned_video
                else:
                    current_video = raw_video
            else:
                current_video = raw_video

            # --- Add silent audio track (TikTok requires audio) ---
            audio_video = work_dir / "with_audio.mp4"
            total_duration = sum(
                max(self.assembler._parse_timing(seg["timing"])[1]
                    - self.assembler._parse_timing(seg["timing"])[0], 0.5)
                for seg in script.script_segments
            )
            if self.assembler.add_audio_track(current_video, audio_video, total_duration):
                current_video = audio_video

            # --- Move final video to output directory ---
            slug = self._slugify(script.topic)
            final_name = f"{slug}-{script.format_name}.mp4"
            final_path = self.output_dir / final_name
            shutil.copy2(str(current_video), str(final_path))

            logger.info("Produced video: %s (%ds)", final_path.name, int(total_duration))
            return final_path

        except Exception as e:
            logger.exception("Video production failed for '%s': %s", script.topic, e)
            return None
        finally:
            # Clean up temp directory
            shutil.rmtree(work_dir, ignore_errors=True)

    def _build_caption_track(self, script: "Any") -> List[Dict[str, Any]]:
        """Build timed caption entries from script segments."""
        captions: List[Dict[str, Any]] = []
        running_start = 0.0

        for seg in script.script_segments:
            text = seg.get("text", "")
            timing = seg.get("timing", "0-3s")
            start, end = self.assembler._parse_timing(timing)
            duration = max(end - start, 0.5)

            # Skip non-spoken segments (stage directions)
            if text.startswith("[") and text.endswith("]"):
                running_start += duration
                continue

            # Truncate long lines for on-screen readability
            display_text = text[:80] + "..." if len(text) > 80 else text

            captions.append({
                "text": display_text,
                "start": round(running_start, 2),
                "end": round(running_start + duration, 2),
            })
            running_start += duration

        return captions

    @staticmethod
    def _slugify(text: str) -> str:
        slug = "".join(c.lower() if c.isalnum() else "-" for c in text)
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")[:60]


__all__ = [
    "TikTokProducer",
    "VideoEditor",
    "VideoAssembler",
    "FrameGenerator",
    "check_dependencies",
    "COLOR_PALETTES",
]
