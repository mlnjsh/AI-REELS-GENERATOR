"""
video_composer.py - Assembles final Instagram Reel videos using MoviePy.

Creates 9:16 portrait videos (1080x1920) with:
- Animated gradient backgrounds
- Bold text overlays synced to voiceover
- Burned-in captions/subtitles
- AI voiceover audio
"""

import os
import json
import math
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

# ---------------------------------------------------------------------------
# Video settings
# ---------------------------------------------------------------------------
WIDTH = 1080
HEIGHT = 1920
FPS = 30
BG_COLOR = (10, 10, 20)  # Near-black background

# Color palette
COLORS = {
    "bg_dark": (10, 10, 20),
    "bg_gradient_top": (15, 5, 40),      # Dark purple
    "bg_gradient_bottom": (5, 15, 35),    # Dark blue
    "text_white": (255, 255, 255),
    "text_yellow": (255, 220, 50),
    "text_cyan": (0, 220, 255),
    "accent_purple": (130, 80, 255),
    "accent_blue": (60, 120, 255),
    "caption_bg": (0, 0, 0),             # Black background for captions
    "hook_color": (255, 220, 50),        # Yellow for hooks
    "point_color": (255, 255, 255),      # White for key points
    "cta_color": (0, 220, 255),          # Cyan for CTA
}

# Font settings
FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


def get_font(size, bold=True):
    """Get font path, falling back to system fonts if custom not available."""
    # Try custom Montserrat font first
    if bold:
        candidates = ["Montserrat-Bold.ttf", "Montserrat-ExtraBold.ttf"]
    else:
        candidates = ["Montserrat-Regular.ttf", "Montserrat-Medium.ttf"]

    for name in candidates:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    # Fallback to system fonts
    system_fonts = [
        "C:/Windows/Fonts/arialbd.ttf",    # Windows Bold
        "C:/Windows/Fonts/arial.ttf",        # Windows
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
    ]
    for font_path in system_fonts:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    return ImageFont.load_default()


def create_gradient_frame(width, height, t, duration):
    """Create an animated gradient background frame."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Animate colors over time
    progress = t / max(duration, 1)
    phase = progress * 2 * math.pi

    # Shifting gradient colors
    r1 = int(15 + 10 * math.sin(phase))
    g1 = int(5 + 10 * math.sin(phase + 1))
    b1 = int(40 + 20 * math.sin(phase + 2))

    r2 = int(5 + 10 * math.sin(phase + 3))
    g2 = int(15 + 10 * math.sin(phase + 4))
    b2 = int(35 + 20 * math.sin(phase + 5))

    # Draw vertical gradient
    for y in range(height):
        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Add subtle particles/dots
    np.random.seed(int(t * 10) % 1000)
    for _ in range(30):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        alpha = int(30 + 20 * math.sin(phase + x * 0.01))
        size = np.random.randint(1, 4)
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=(255, 255, 255, alpha) if img.mode == "RGBA" else (alpha, alpha, alpha + 20),
        )

    return np.array(img)


def make_gradient_background(duration):
    """Create an animated gradient background clip."""
    def make_frame(t):
        return create_gradient_frame(WIDTH, HEIGHT, t, duration)

    return ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR, duration=duration).fl(
        lambda gf, t: create_gradient_frame(WIDTH, HEIGHT, t, duration)
    )


def render_text_image(text, font_size=60, color=(255, 255, 255), max_width=900,
                      bg_color=None, padding=20):
    """Render text to a PIL Image with word wrapping."""
    font = get_font(font_size)

    # Wrap text
    wrapped = textwrap.fill(text, width=max(int(max_width / (font_size * 0.5)), 15))
    lines = wrapped.split("\n")

    # Calculate dimensions
    dummy_img = Image.new("RGB", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)

    line_bboxes = [dummy_draw.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [bb[3] - bb[1] for bb in line_bboxes]
    line_widths = [bb[2] - bb[0] for bb in line_bboxes]

    total_height = sum(line_heights) + (len(lines) - 1) * 10 + padding * 2
    total_width = max(line_widths) + padding * 2

    # Create image
    if bg_color:
        img = Image.new("RGBA", (total_width, total_height), (*bg_color, 200))
    else:
        img = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)

    # Draw text centered
    y_offset = padding
    for i, line in enumerate(lines):
        x_pos = (total_width - line_widths[i]) // 2
        # Draw shadow
        draw.text((x_pos + 2, y_offset + 2), line, font=font, fill=(0, 0, 0, 180))
        # Draw text
        draw.text((x_pos, y_offset), line, font=font, fill=color)
        y_offset += line_heights[i] + 10

    return np.array(img)


def create_text_clip(text, font_size=60, color=(255, 255, 255), position="center",
                     start_time=0, duration=3, bg_color=None, fade_duration=0.3):
    """Create a text overlay clip with fade in/out."""
    text_img = render_text_image(text, font_size, color, bg_color=bg_color)

    clip = (
        ImageClip(text_img, transparent=True)
        .set_duration(duration)
        .set_start(start_time)
        .set_position(position)
        .crossfadein(fade_duration)
        .crossfadeout(fade_duration)
    )

    return clip


def create_caption_clip(phrase_text, start_s, end_s):
    """Create a caption/subtitle clip at the bottom of the screen."""
    duration = end_s - start_s
    if duration <= 0:
        duration = 0.5

    text_img = render_text_image(
        phrase_text,
        font_size=42,
        color=(255, 255, 255),
        max_width=950,
        bg_color=(0, 0, 0),
        padding=15,
    )

    clip = (
        ImageClip(text_img, transparent=True)
        .set_duration(duration)
        .set_start(start_s)
        .set_position(("center", HEIGHT - 350))
        .crossfadein(0.1)
        .crossfadeout(0.1)
    )

    return clip


def create_progress_bar(duration):
    """Create a thin progress bar at the bottom."""
    bar_height = 4

    def make_frame(t):
        progress = t / max(duration, 0.1)
        bar = np.zeros((bar_height, WIDTH, 3), dtype=np.uint8)
        fill_width = int(WIDTH * progress)
        bar[:, :fill_width] = [130, 80, 255]  # Purple
        return bar

    return (
        ColorClip(size=(WIDTH, bar_height), color=(130, 80, 255), duration=duration)
        .fl(lambda gf, t: make_frame(t))
        .set_position(("center", HEIGHT - bar_height))
    )


def compose_reel(script, audio_result, output_path):
    """
    Compose a complete Instagram Reel video.

    Args:
        script: dict from content_selector (hook, key_points, display_texts, etc.)
        audio_result: dict from audio_generator (audio_path, phrases, duration_ms)
        output_path: path to save the final MP4
    """
    duration = audio_result["duration_s"] + 1.0  # Add 1s buffer at end
    phrases = audio_result["phrases"]

    clips = []

    # 1. Background - animated gradient
    bg = make_gradient_background(duration)
    clips.append(bg)

    # 2. Top branding bar
    branding_text = "AI TOOLS DAILY"
    branding = create_text_clip(
        branding_text,
        font_size=28,
        color=COLORS["accent_purple"],
        position=("center", 80),
        start_time=0,
        duration=duration,
        fade_duration=0.5,
    )
    clips.append(branding)

    # 3. Main display texts - large, bold, center screen
    display_texts = script.get("display_texts", [])
    voiceover_parts = script.get("voiceover_parts", [])

    # Map display texts to timing from phrases
    # We distribute display texts across the audio duration
    if phrases and display_texts:
        part_count = len(display_texts)
        phrase_per_part = max(1, len(phrases) // part_count)

        for i, display_text in enumerate(display_texts):
            # Calculate timing for this display text
            start_phrase_idx = i * phrase_per_part
            end_phrase_idx = min((i + 1) * phrase_per_part, len(phrases)) - 1

            if start_phrase_idx >= len(phrases):
                break

            start_s = phrases[start_phrase_idx]["start_ms"] / 1000
            end_s = phrases[min(end_phrase_idx, len(phrases) - 1)]["end_ms"] / 1000
            text_duration = max(end_s - start_s, 1.5)

            # Choose color based on position
            if i == 0:
                color = COLORS["hook_color"]     # Yellow for hook
                font_size = 65
            elif i == len(display_texts) - 1:
                color = COLORS["cta_color"]      # Cyan for CTA
                font_size = 55
            else:
                color = COLORS["point_color"]    # White for points
                font_size = 58

            # Point number indicator for middle sections
            prefix = ""
            if 0 < i < len(display_texts) - 1:
                prefix = f"{i}. "

            main_text = create_text_clip(
                prefix + display_text,
                font_size=font_size,
                color=color,
                position=("center", HEIGHT // 2 - 100),
                start_time=start_s,
                duration=text_duration,
                fade_duration=0.3,
            )
            clips.append(main_text)

    # 4. Burned-in captions at bottom (synced to audio phrases)
    for phrase in phrases:
        start_s = phrase["start_ms"] / 1000
        end_s = phrase["end_ms"] / 1000
        if end_s > start_s:
            caption = create_caption_clip(phrase["text"], start_s, end_s)
            clips.append(caption)

    # 5. Progress bar at bottom
    progress_bar = create_progress_bar(duration)
    clips.append(progress_bar)

    # 6. Source watermark
    source_name = "Matt Wolfe" if script.get("source") == "matt_wolfe" else "Nate Herk"
    watermark = create_text_clip(
        f"via {source_name}",
        font_size=24,
        color=(150, 150, 150),
        position=(WIDTH - 200, HEIGHT - 50),
        start_time=0,
        duration=duration,
        fade_duration=1.0,
    )
    clips.append(watermark)

    # Composite all clips
    video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))

    # Add audio
    audio = AudioFileClip(audio_result["audio_path"])
    video = video.set_audio(audio)

    # Set final duration to match audio
    video = video.set_duration(duration)

    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="5000k",
        preset="medium",
        threads=4,
        logger=None,  # Suppress verbose moviepy output
    )

    # Cleanup
    audio.close()
    video.close()

    return output_path


if __name__ == "__main__":
    # Test: compose a sample reel
    test_script = {
        "hook": "This AI tool changed everything",
        "key_points": [
            "Claude Code builds apps from prompts",
            "n8n automates your entire workflow",
            "Best part: only $20 per month",
        ],
        "cta": "Follow for daily AI tips",
        "display_texts": [
            "This AI tool changed everything",
            "Claude Code builds apps",
            "n8n automates workflows",
            "Only $20 per month",
            "Follow for daily AI tips",
        ],
        "voiceover_parts": [
            "This AI tool changed everything",
            "Claude Code can now build entire apps from a single prompt",
            "It works with n8n to automate your entire workflow",
            "The best part? It's only 20 dollars a month",
            "Follow for daily AI tools and tips",
        ],
        "source": "nate_herk",
    }

    # Mock audio result for testing
    test_audio = {
        "audio_path": "output/test/reel_01_audio.mp3",
        "phrases": [
            {"text": "This AI tool changed", "start_ms": 0, "end_ms": 2000},
            {"text": "everything Claude Code", "start_ms": 2000, "end_ms": 4500},
            {"text": "can now build entire", "start_ms": 4500, "end_ms": 7000},
            {"text": "apps from a single", "start_ms": 7000, "end_ms": 9000},
            {"text": "prompt It works with", "start_ms": 9000, "end_ms": 11500},
            {"text": "n8n to automate your", "start_ms": 11500, "end_ms": 14000},
            {"text": "entire workflow The best", "start_ms": 14000, "end_ms": 16500},
            {"text": "part It's only twenty", "start_ms": 16500, "end_ms": 19000},
            {"text": "dollars a month Follow", "start_ms": 19000, "end_ms": 21000},
            {"text": "for daily AI tools", "start_ms": 21000, "end_ms": 23000},
        ],
        "duration_ms": 23000,
        "duration_s": 23.0,
    }

    print("Test compose requires audio file. Run via generate_reels.py for full pipeline.")
