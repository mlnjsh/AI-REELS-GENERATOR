"""
video_composer.py - Assembles final Instagram Reel videos using MoviePy v2.

Creates 9:16 portrait videos (1080x1920) with:
- Animated gradient backgrounds
- Bold text overlays synced to voiceover
- Burned-in captions/subtitles
- AI voiceover audio
"""

import os
import math
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    ImageClip,
)
from moviepy.video.fx import CrossFadeIn, CrossFadeOut

# ---------------------------------------------------------------------------
# Video settings
# ---------------------------------------------------------------------------
WIDTH = 1080
HEIGHT = 1920
FPS = 30

# Color palette
COLORS = {
    "text_white": (255, 255, 255),
    "text_yellow": (255, 220, 50),
    "text_cyan": (0, 220, 255),
    "accent_purple": (130, 80, 255),
    "hook_color": (255, 220, 50),
    "point_color": (255, 255, 255),
    "cta_color": (0, 220, 255),
}

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


def get_font(size, bold=True):
    """Get font, falling back to system fonts if custom not available."""
    candidates = (
        ["Montserrat-Bold.ttf", "Montserrat-ExtraBold.ttf"]
        if bold
        else ["Montserrat-Regular.ttf", "Montserrat-Medium.ttf"]
    )
    for name in candidates:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    system_fonts = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in system_fonts:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)

    return ImageFont.load_default()


def create_gradient_frame(w, h, t, duration):
    """Create an animated gradient background frame as numpy array."""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)

    phase = (t / max(duration, 1)) * 2 * math.pi
    r1 = int(15 + 10 * math.sin(phase))
    g1 = int(5 + 10 * math.sin(phase + 1))
    b1 = int(40 + 20 * math.sin(phase + 2))
    r2 = int(5 + 10 * math.sin(phase + 3))
    g2 = int(15 + 10 * math.sin(phase + 4))
    b2 = int(35 + 20 * math.sin(phase + 5))

    for y in range(h):
        ratio = y / h
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    return np.array(img)


def make_gradient_background(duration):
    """Create animated gradient background clip."""
    def frame_func(t):
        return create_gradient_frame(WIDTH, HEIGHT, t, duration)

    clip = ColorClip(size=(WIDTH, HEIGHT), color=(10, 10, 20), duration=duration)
    return clip.with_updated_frame_function(frame_func).with_fps(FPS)


def render_text_image(text, font_size=60, color=(255, 255, 255), max_width=900,
                      bg_color=None, padding=20):
    """Render text to a numpy array with word wrapping."""
    font = get_font(font_size)
    chars_per_line = max(int(max_width / (font_size * 0.52)), 12)
    wrapped = textwrap.fill(text, width=chars_per_line)
    lines = wrapped.split("\n")

    dummy = Image.new("RGB", (1, 1))
    dd = ImageDraw.Draw(dummy)
    bboxes = [dd.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [bb[3] - bb[1] for bb in bboxes]
    line_widths = [bb[2] - bb[0] for bb in bboxes]

    total_h = sum(line_heights) + (len(lines) - 1) * 12 + padding * 2
    total_w = max(line_widths) + padding * 2

    if bg_color:
        img = Image.new("RGBA", (total_w, total_h), (*bg_color, 200))
    else:
        img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)
    y = padding
    for i, line in enumerate(lines):
        x = (total_w - line_widths[i]) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 180))
        draw.text((x, y), line, font=font, fill=color)
        y += line_heights[i] + 12

    return np.array(img)


def create_text_clip(text, font_size=60, color=(255, 255, 255), position="center",
                     start_time=0, duration=3, bg_color=None, fade_dur=0.3):
    """Create a text overlay clip with fade effects."""
    text_img = render_text_image(text, font_size, color, bg_color=bg_color)

    clip = (
        ImageClip(text_img, transparent=True)
        .with_duration(duration)
        .with_start(start_time)
        .with_position(position)
        .with_effects([CrossFadeIn(fade_dur), CrossFadeOut(fade_dur)])
    )
    return clip


def create_caption_clip(text, start_s, end_s):
    """Create a burned-in caption at the bottom of the screen."""
    dur = max(end_s - start_s, 0.3)
    text_img = render_text_image(
        text, font_size=42, color=(255, 255, 255),
        max_width=950, bg_color=(0, 0, 0), padding=15,
    )
    clip = (
        ImageClip(text_img, transparent=True)
        .with_duration(dur)
        .with_start(start_s)
        .with_position(("center", HEIGHT - 350))
        .with_effects([CrossFadeIn(0.1), CrossFadeOut(0.1)])
    )
    return clip


def create_progress_bar(duration):
    """Create a thin animated progress bar at the bottom."""
    bar_h = 4

    def frame_func(t):
        progress = t / max(duration, 0.1)
        bar = np.zeros((bar_h, WIDTH, 3), dtype=np.uint8)
        fill_w = int(WIDTH * progress)
        if fill_w > 0:
            bar[:, :fill_w] = [130, 80, 255]
        return bar

    clip = (
        ColorClip(size=(WIDTH, bar_h), color=(130, 80, 255), duration=duration)
        .with_updated_frame_function(frame_func)
        .with_fps(FPS)
        .with_position(("center", HEIGHT - bar_h))
    )
    return clip


def compose_reel(script, audio_result, output_path):
    """
    Compose a complete Instagram Reel video.

    Args:
        script: dict from content_selector (hook, key_points, display_texts, etc.)
        audio_result: dict from audio_generator (audio_path, phrases, duration_ms)
        output_path: path to save the final MP4
    """
    # Load audio first to get exact duration
    audio = AudioFileClip(audio_result["audio_path"])
    audio_duration = audio.duration
    duration = audio_duration  # Match video to audio exactly
    phrases = audio_result["phrases"]
    clips = []

    # 1. Background
    bg = make_gradient_background(duration)
    clips.append(bg)

    # 2. Top branding
    branding = create_text_clip(
        "AI TOOLS DAILY", font_size=28, color=COLORS["accent_purple"],
        position=("center", 80), start_time=0, duration=duration, fade_dur=0.5,
    )
    clips.append(branding)

    # 3. Main display texts synced to audio
    display_texts = script.get("display_texts", [])
    if phrases and display_texts:
        part_count = len(display_texts)
        phrases_per = max(1, len(phrases) // part_count)

        for i, dt in enumerate(display_texts):
            si = i * phrases_per
            ei = min((i + 1) * phrases_per, len(phrases)) - 1
            if si >= len(phrases):
                break

            start_s = phrases[si]["start_ms"] / 1000
            end_s = phrases[min(ei, len(phrases) - 1)]["end_ms"] / 1000
            text_dur = max(end_s - start_s, 1.5)

            if i == 0:
                color, fs = COLORS["hook_color"], 65
            elif i == len(display_texts) - 1:
                color, fs = COLORS["cta_color"], 55
            else:
                color, fs = COLORS["point_color"], 58

            prefix = f"{i}. " if 0 < i < len(display_texts) - 1 else ""
            clips.append(create_text_clip(
                prefix + dt, font_size=fs, color=color,
                position=("center", HEIGHT // 2 - 100),
                start_time=start_s, duration=text_dur, fade_dur=0.3,
            ))

    # 4. Captions
    for phrase in phrases:
        s = phrase["start_ms"] / 1000
        e = phrase["end_ms"] / 1000
        if e > s:
            clips.append(create_caption_clip(phrase["text"], s, e))

    # 5. Progress bar
    clips.append(create_progress_bar(duration))

    # 6. Source watermark
    source_name = "Matt Wolfe" if script.get("source") == "matt_wolfe" else "Nate Herk"
    clips.append(create_text_clip(
        f"via {source_name}", font_size=24, color=(150, 150, 150),
        position=(WIDTH - 250, HEIGHT - 50), start_time=0,
        duration=duration, fade_dur=1.0,
    ))

    # Composite
    video = CompositeVideoClip(clips, size=(WIDTH, HEIGHT))

    # Attach audio and set duration to match
    video = video.with_audio(audio).with_duration(audio_duration)

    # Export
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video.write_videofile(
        output_path, fps=FPS, codec="libx264", audio_codec="aac",
        bitrate="5000k", preset="medium", threads=4, logger=None,
    )

    audio.close()
    video.close()
    return output_path


if __name__ == "__main__":
    print("Run via generate_reels.py for full pipeline.")
