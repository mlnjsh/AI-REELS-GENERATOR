"""
audio_generator.py - Generates AI voiceover audio using Edge TTS (free).

Uses Microsoft Edge TTS to convert reel scripts to MP3 audio with
estimated phrase-level timestamps for subtitle synchronization.
"""

import asyncio
import json
import os
import re

import edge_tts

# Voice options (all free, no API key needed)
VOICES = {
    "male": "en-US-ChristopherNeural",
    "male_alt": "en-US-GuyNeural",
    "female": "en-US-JennyNeural",
    "female_alt": "en-US-AriaNeural",
}

DEFAULT_VOICE = VOICES["male"]
RATE = "+10%"


async def generate_audio(text, output_path, voice=None):
    """
    Generate MP3 audio from text using Edge TTS.
    Returns sentence boundaries for subtitle timing.
    """
    voice = voice or DEFAULT_VOICE
    sentences = []

    communicate = edge_tts.Communicate(text, voice, rate=RATE)

    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sentences.append({
                    "text": chunk["text"],
                    "start_ms": chunk["offset"] // 10000,
                    "duration_ms": chunk["duration"] // 10000,
                })
            elif chunk["type"] == "SentenceBoundary":
                sentences.append({
                    "text": chunk["text"],
                    "start_ms": chunk["offset"] // 10000,
                    "duration_ms": chunk["duration"] // 10000,
                })

    # Calculate end times
    for s in sentences:
        s["end_ms"] = s["start_ms"] + s["duration_ms"]

    total_ms = sentences[-1]["end_ms"] if sentences else 0
    return {"sentences": sentences, "duration_ms": total_ms}


def estimate_phrase_timing(voiceover_parts, total_duration_ms):
    """
    Estimate timing for each voiceover part based on word count.
    This is used when Edge TTS only provides sentence-level boundaries.
    """
    # Count words in each part
    word_counts = [len(part.split()) for part in voiceover_parts]
    total_words = sum(word_counts)
    if total_words == 0:
        total_words = 1

    phrases = []
    current_ms = 0

    for i, (part, wc) in enumerate(zip(voiceover_parts, word_counts)):
        # Allocate duration proportional to word count
        part_duration = int((wc / total_words) * total_duration_ms)
        # Add a small gap between parts
        gap = 200 if i < len(voiceover_parts) - 1 else 0

        phrases.append({
            "text": part,
            "start_ms": current_ms,
            "end_ms": current_ms + part_duration - gap,
            "duration_ms": part_duration - gap,
        })
        current_ms += part_duration

    return phrases


def split_into_display_phrases(phrases, max_words=6):
    """
    Split longer phrases into shorter display chunks for on-screen captions.
    """
    display_phrases = []

    for phrase in phrases:
        words = phrase["text"].split()
        total_words = len(words)
        if total_words == 0:
            continue

        chunk_count = max(1, (total_words + max_words - 1) // max_words)
        words_per_chunk = max(1, total_words // chunk_count)
        phrase_duration = phrase["duration_ms"]
        ms_per_word = phrase_duration / max(total_words, 1)

        word_idx = 0
        for c in range(chunk_count):
            # Take next chunk of words
            end_idx = min(word_idx + words_per_chunk, total_words)
            if c == chunk_count - 1:
                end_idx = total_words

            chunk_words = words[word_idx:end_idx]
            if not chunk_words:
                break

            start_ms = phrase["start_ms"] + int(word_idx * ms_per_word)
            end_ms = phrase["start_ms"] + int(end_idx * ms_per_word)

            display_phrases.append({
                "text": " ".join(chunk_words),
                "start_ms": start_ms,
                "end_ms": end_ms,
                "duration_ms": end_ms - start_ms,
            })
            word_idx = end_idx

    return display_phrases


def generate_audio_for_reel(script, output_dir, reel_num, voice=None):
    """
    Generate audio for a complete reel script.

    Returns dict with audio_path, phrases (for display), duration_ms/duration_s.
    """
    os.makedirs(output_dir, exist_ok=True)

    parts = script.get("voiceover_parts", [])
    # Join with pauses
    full_text = ". ".join(parts)
    full_text = re.sub(r"\.{2,}", ".", full_text)
    full_text = re.sub(r"\s+", " ", full_text).strip()

    audio_path = os.path.join(output_dir, f"reel_{reel_num:02d}_audio.mp3")

    # Generate audio
    result = asyncio.run(generate_audio(full_text, audio_path, voice))
    total_ms = result["duration_ms"]

    # If Edge TTS gave us sentence boundaries, use them
    if result["sentences"]:
        # Map sentence boundaries to our voiceover parts
        phrases = estimate_phrase_timing(parts, total_ms)
    else:
        # Fallback: estimate from audio duration using ffprobe
        total_ms = _get_audio_duration_ms(audio_path)
        phrases = estimate_phrase_timing(parts, total_ms)

    # Split into display-friendly captions
    display_phrases = split_into_display_phrases(phrases)

    # Save subtitle data
    subs_path = os.path.join(output_dir, f"reel_{reel_num:02d}_subs.json")
    with open(subs_path, "w") as f:
        json.dump({
            "phrases": [{"text": p["text"], "start_ms": p["start_ms"],
                         "end_ms": p["end_ms"], "duration_ms": p["duration_ms"]}
                        for p in display_phrases],
            "duration_ms": total_ms,
        }, f, indent=2)

    duration_s = total_ms / 1000 if total_ms > 0 else _get_audio_duration_s(audio_path)

    return {
        "audio_path": audio_path,
        "subs_path": subs_path,
        "phrases": display_phrases,
        "duration_ms": max(total_ms, int(duration_s * 1000)),
        "duration_s": max(duration_s, 1.0),
    }


def _get_audio_duration_ms(path):
    """Get audio duration in ms using ffprobe as fallback."""
    return int(_get_audio_duration_s(path) * 1000)


def _get_audio_duration_s(path):
    """Get audio duration in seconds using ffprobe."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        # Rough estimate from file size (MP3 ~16kB/s at default quality)
        try:
            size = os.path.getsize(path)
            return size / 16000
        except Exception:
            return 30.0


if __name__ == "__main__":
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
