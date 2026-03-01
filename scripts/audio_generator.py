"""
audio_generator.py - Generates AI voiceover audio using Edge TTS (free).

Uses Microsoft Edge TTS to convert reel scripts to MP3 audio with
word-level timestamps for subtitle synchronization.
"""

import asyncio
import json
import os
import re
import tempfile
from pathlib import Path

import edge_tts

# Voice options (all free, no API key needed)
VOICES = {
    "male": "en-US-ChristopherNeural",      # Clear, engaging male voice
    "male_alt": "en-US-GuyNeural",           # Deeper male voice
    "female": "en-US-JennyNeural",           # Clear female voice
    "female_alt": "en-US-AriaNeural",        # Expressive female voice
}

DEFAULT_VOICE = VOICES["male"]

# Speech rate adjustments
RATE = "+10%"        # Slightly faster for engaging pace
VOLUME = "+0%"


async def generate_audio_with_timestamps(text, output_path, voice=None):
    """
    Generate MP3 audio and word-level timestamps from text using Edge TTS.

    Returns:
        dict with keys:
            - audio_path: path to generated MP3
            - subtitles: list of {text, start_ms, end_ms} for each word/phrase
            - duration_ms: total audio duration in milliseconds
    """
    voice = voice or DEFAULT_VOICE
    subtitles = []

    communicate = edge_tts.Communicate(text, voice, rate=RATE, volume=VOLUME)

    # Collect subtitle data from the stream
    audio_chunks = []
    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                subtitles.append({
                    "text": chunk["text"],
                    "start_ms": chunk["offset"] // 10000,  # Convert 100-nanosecond units to ms
                    "duration_ms": chunk["duration"] // 10000,
                })

    # Calculate end times
    for sub in subtitles:
        sub["end_ms"] = sub["start_ms"] + sub["duration_ms"]

    # Get total duration
    duration_ms = subtitles[-1]["end_ms"] if subtitles else 0

    return {
        "audio_path": output_path,
        "subtitles": subtitles,
        "duration_ms": duration_ms,
    }


def group_subtitles_into_phrases(subtitles, max_words=5, max_duration_ms=2500):
    """
    Group word-level subtitles into display phrases for on-screen text.

    Groups words into phrases of max_words or max_duration_ms,
    whichever limit is hit first.
    """
    phrases = []
    current_words = []
    current_start = None

    for sub in subtitles:
        if current_start is None:
            current_start = sub["start_ms"]

        current_words.append(sub["text"])
        current_end = sub["end_ms"]
        current_duration = current_end - current_start

        if len(current_words) >= max_words or current_duration >= max_duration_ms:
            phrases.append({
                "text": " ".join(current_words),
                "start_ms": current_start,
                "end_ms": current_end,
                "duration_ms": current_end - current_start,
            })
            current_words = []
            current_start = None

    # Don't forget the last phrase
    if current_words:
        phrases.append({
            "text": " ".join(current_words),
            "start_ms": current_start,
            "end_ms": subtitles[-1]["end_ms"],
            "duration_ms": subtitles[-1]["end_ms"] - current_start,
        })

    return phrases


def generate_audio_for_reel(script, output_dir, reel_num, voice=None):
    """
    Generate audio for a complete reel script.

    Args:
        script: dict from content_selector with voiceover_parts
        output_dir: directory to save audio files
        reel_num: reel number (1, 2, 3)
        voice: optional voice override

    Returns:
        dict with audio_path, phrases (grouped subtitles), duration_ms
    """
    os.makedirs(output_dir, exist_ok=True)

    # Build the full voiceover text with natural pauses
    parts = script.get("voiceover_parts", [])
    # Add brief pauses between sections
    full_text = ". ".join(parts)
    # Clean up any double periods or weird punctuation
    full_text = re.sub(r'\.{2,}', '.', full_text)
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    audio_path = os.path.join(output_dir, f"reel_{reel_num:02d}_audio.mp3")

    # Run async TTS
    result = asyncio.run(
        generate_audio_with_timestamps(full_text, audio_path, voice)
    )

    # Group word-level subtitles into display phrases
    phrases = group_subtitles_into_phrases(result["subtitles"])

    # Save subtitle data as JSON for video composer
    subs_path = os.path.join(output_dir, f"reel_{reel_num:02d}_subs.json")
    with open(subs_path, "w") as f:
        json.dump({
            "phrases": phrases,
            "duration_ms": result["duration_ms"],
            "word_subtitles": result["subtitles"],
        }, f, indent=2)

    return {
        "audio_path": audio_path,
        "subs_path": subs_path,
        "phrases": phrases,
        "duration_ms": result["duration_ms"],
        "duration_s": result["duration_ms"] / 1000,
    }


async def list_voices():
    """List all available Edge TTS voices (for reference)."""
    voices = await edge_tts.list_voices()
    en_voices = [v for v in voices if v["Locale"].startswith("en-")]
    for v in en_voices:
        print(f"{v['ShortName']:40s} {v['Gender']:10s} {v['Locale']}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "voices":
        asyncio.run(list_voices())
    else:
        # Test: generate a sample reel audio
        test_script = {
            "voiceover_parts": [
                "This AI tool just changed everything",
                "Claude Code can now build entire apps from a single prompt",
                "It works with n8n to automate your entire workflow",
                "The best part? It's only 20 dollars a month",
                "Follow for daily AI tools and tips",
            ]
        }

        result = generate_audio_for_reel(test_script, "output/test", 1)
        print(f"Audio: {result['audio_path']}")
        print(f"Duration: {result['duration_s']:.1f}s")
        print(f"Phrases: {len(result['phrases'])}")
        for p in result["phrases"]:
            print(f"  [{p['start_ms']/1000:.1f}s - {p['end_ms']/1000:.1f}s] {p['text']}")
