"""
generate_reels.py - Main orchestrator for AI Reels Generator.

Runs the full pipeline:
1. Select content from both radar repos
2. Generate AI voiceover audio
3. Compose video with text overlays
4. Output ready-to-post Instagram Reels
5. Send Gmail notification
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from content_selector import select_content, save_state
from audio_generator import generate_audio_for_reel
from video_composer import compose_reel
from notify import send_notification


def run_pipeline(count=3):
    """Run the full reel generation pipeline."""
    print("=" * 60)
    print("AI REELS GENERATOR")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Generating {count} reels...")
    print("=" * 60)

    # Paths
    matt_path = os.getenv("RADAR_MATT_PATH", os.path.join(PROJECT_DIR, "..", "LATEST-AI-RADAR"))
    nate_path = os.getenv("RADAR_NATE_PATH", os.path.join(PROJECT_DIR, "..", "NATE-HERK-RADAR"))
    state_path = os.path.join(PROJECT_DIR, "state.json")
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join(PROJECT_DIR, "output", today)

    # Resolve relative paths
    matt_path = os.path.abspath(matt_path)
    nate_path = os.path.abspath(nate_path)

    print(f"\nMatt Wolfe radar: {matt_path}")
    print(f"Nate Herk radar:  {nate_path}")
    print(f"Output directory:  {output_dir}")

    # Step 1: Select content and generate scripts
    print(f"\n--- Step 1: Selecting content ---")
    scripts, state = select_content(matt_path, nate_path, state_path, count=count)

    if not scripts:
        print("ERROR: No content selected. Check radar repo paths.")
        return

    for i, script in enumerate(scripts, 1):
        print(f"  Reel #{i}: {script['title'][:50]}... (source: {script['source']})")

    # Step 2: Generate audio for each reel
    print(f"\n--- Step 2: Generating audio ---")
    audio_results = []
    for i, script in enumerate(scripts, 1):
        print(f"  Generating audio for reel #{i}...")
        try:
            audio = generate_audio_for_reel(script, output_dir, i)
            audio_results.append(audio)
            print(f"    Duration: {audio['duration_s']:.1f}s | Phrases: {len(audio['phrases'])}")
        except Exception as e:
            print(f"    ERROR generating audio: {e}")
            audio_results.append(None)

    # Step 3: Compose videos
    print(f"\n--- Step 3: Composing videos ---")
    reel_outputs = []
    for i, (script, audio) in enumerate(zip(scripts, audio_results), 1):
        if audio is None:
            print(f"  Skipping reel #{i} (no audio)")
            continue

        output_path = os.path.join(output_dir, f"reel_{i:02d}.mp4")
        print(f"  Composing reel #{i}...")
        try:
            compose_reel(script, audio, output_path)
            reel_outputs.append({
                "path": output_path,
                "title": script["title"],
                "source": script["source"],
                "duration": f"{audio['duration_s']:.0f}s",
                "reel_num": i,
            })
            print(f"    Saved: {output_path}")
        except Exception as e:
            print(f"    ERROR composing video: {e}")
            import traceback
            traceback.print_exc()

    # Step 4: Save caption files
    print(f"\n--- Step 4: Saving captions ---")
    for i, script in enumerate(scripts, 1):
        caption_path = os.path.join(output_dir, f"reel_{i:02d}_caption.txt")
        os.makedirs(output_dir, exist_ok=True)
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(script.get("caption", ""))
        print(f"  Saved: {caption_path}")

    # Step 5: Save state
    save_state(state, state_path)
    print(f"\nState saved to {state_path}")

    # Step 6: Send notification
    print(f"\n--- Step 5: Sending notification ---")
    if reel_outputs:
        send_notification(reel_outputs)

    # Summary
    print(f"\n{'='*60}")
    print(f"DONE! Generated {len(reel_outputs)} reels")
    print(f"Output: {output_dir}")
    print(f"{'='*60}")

    for reel in reel_outputs:
        print(f"  - reel_{reel['reel_num']:02d}.mp4 ({reel['duration']}) - {reel['title'][:40]}...")
        print(f"    Caption: reel_{reel['reel_num']:02d}_caption.txt")

    return reel_outputs


if __name__ == "__main__":
    count = 3
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass

    run_pipeline(count=count)
