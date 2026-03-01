"""
content_selector.py - Reads both radar repos, selects viral content, generates reel scripts.

Parses video markdown files from LATEST-AI-RADAR and NATE-HERK-RADAR,
scores content by virality potential, and generates 3 reel scripts per run.
"""

import os
import re
import json
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

# ---------------------------------------------------------------------------
# Viral hooks templates - attention grabbers for first 3 seconds
# ---------------------------------------------------------------------------
HOOK_TEMPLATES = [
    "This AI tool is replacing {tool} and nobody's talking about it",
    "Stop everything. {tool} just changed the game",
    "{tool} can do THIS now and it's insane",
    "I found the AI tool that does {topic} for FREE",
    "Why is nobody talking about {tool}?",
    "This AI trick will save you hours every day",
    "{tool} vs {tool2} — the winner surprised me",
    "The AI tool that's making people $1000/week",
    "You're using AI wrong. Here's what experts do instead",
    "3 AI tools that replaced my entire workflow",
    "This free AI tool is better than the $20/month one",
    "The AI secret that top creators don't share",
    "I tested {tool} for 30 days. Here's the truth",
    "This AI hack is going viral for a reason",
    "The #{rank} AI tool nobody expected",
]

# CTA templates for reel endings
CTA_TEMPLATES = [
    "Follow for daily AI tools and tips",
    "Save this for later. Follow for more AI updates",
    "Which tool are you trying first? Comment below",
    "Follow if you want to stay ahead with AI",
    "Double tap if this was useful. More tomorrow",
    "Share this with someone who needs to see it",
]

# Trending AI topics that boost virality
TRENDING_TOPICS = [
    "claude code", "chatgpt", "gemini", "n8n", "automation",
    "agents", "clawdbot", "voice ai", "free", "no code",
    "make money", "side hustle", "workflow", "api",
]

# Hashtag sets for Instagram captions
HASHTAG_SETS = [
    "#AI #ArtificialIntelligence #AITools #TechTips #AIAutomation",
    "#AINews #FutureOfAI #TechTrends #Automation #AIAgents",
    "#ClaudeCode #ChatGPT #AIHacks #ProductivityTips #NoCode",
    "#AIForBusiness #TechLife #DigitalMarketing #AIWorkflow #FreeTool",
    "#LearnAI #AITutorial #TechReview #Innovation #Startup",
]


def load_state(state_path):
    """Load state tracking which content has been used."""
    if os.path.exists(state_path):
        with open(state_path, "r") as f:
            return json.load(f)
    return {"used_video_ids": [], "used_topics": [], "last_run": None}


def save_state(state, state_path):
    """Save state to avoid repeating content."""
    state["last_run"] = datetime.now().isoformat()
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def parse_video_markdown(filepath):
    """Parse a video markdown file and extract structured data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    video = {"filepath": str(filepath), "tools": [], "timestamps": []}

    # Extract title
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    if title_match:
        video["title"] = title_match.group(1).strip()

    # Extract metadata fields
    for field, key in [
        (r"\*\*Date:\*\*\s*(.+)", "date"),
        (r"\*\*Channel:\*\*\s*(.+)", "channel"),
        (r"\*\*URL:\*\*\s*(.+)", "url"),
        (r"\*\*Duration:\*\*\s*(.+)", "duration"),
        (r"\*\*Views:\*\*\s*(.+)", "views"),
    ]:
        match = re.search(field, content)
        if match:
            video[key] = match.group(1).strip()

    # Extract video ID from URL
    url = video.get("url", "")
    vid_match = re.search(r"watch\?v=([^&\s]+)", url)
    if vid_match:
        video["video_id"] = vid_match.group(1)

    # Extract summary
    summary_match = re.search(
        r"## Summary\s*\n\s*(.+?)(?=\n##|\n---|\Z)", content, re.DOTALL
    )
    if summary_match:
        video["summary"] = summary_match.group(1).strip()

    # Extract tools from table
    tool_rows = re.findall(
        r"\|\s*\d+\s*\|\s*\*\*(.+?)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|",
        content,
    )
    for name, desc, price in tool_rows:
        video["tools"].append(
            {"name": name.strip(), "description": desc.strip(), "price": price.strip()}
        )

    # Extract timestamps
    ts_matches = re.findall(r"-\s*\*\*(\d+:\d+)\*\*\s*[-–]\s*(.+)", content)
    for time_code, topic in ts_matches:
        video["timestamps"].append({"time": time_code, "topic": topic.strip()})

    # Parse views to number for scoring
    views_str = video.get("views", "0")
    try:
        views_str = views_str.replace(",", "").replace("K", "000").replace("M", "000000")
        views_str = re.sub(r"[^0-9.]", "", views_str)
        video["views_num"] = int(float(views_str)) if views_str else 0
    except ValueError:
        video["views_num"] = 0

    return video


def load_all_videos(matt_path, nate_path):
    """Load all video markdown files from both radar repos."""
    videos = []

    for repo_path, source in [(matt_path, "matt_wolfe"), (nate_path, "nate_herk")]:
        videos_dir = Path(repo_path) / "videos"
        if not videos_dir.exists():
            print(f"Warning: {videos_dir} not found")
            continue

        for md_file in sorted(videos_dir.glob("*.md")):
            try:
                video = parse_video_markdown(md_file)
                video["source"] = source
                videos.append(video)
            except Exception as e:
                print(f"Error parsing {md_file}: {e}")

    return videos


def fetch_transcript(video_id):
    """Fetch full transcript for a video (if available)."""
    if YouTubeTranscriptApi is None:
        return None
    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([entry["text"] for entry in transcript_data])
        return full_text
    except Exception:
        return None


def score_video(video, state):
    """Score a video for virality potential (higher = better)."""
    score = 0

    # Views score (more views = proven content)
    views = video.get("views_num", 0)
    if views > 100000:
        score += 30
    elif views > 50000:
        score += 20
    elif views > 20000:
        score += 10

    # Recency score (newer = better)
    try:
        date = datetime.strptime(video.get("date", "2026-01-01"), "%Y-%m-%d")
        days_ago = (datetime.now() - date).days
        if days_ago < 7:
            score += 25
        elif days_ago < 14:
            score += 15
        elif days_ago < 30:
            score += 10
    except ValueError:
        pass

    # Trending tools score
    title_lower = video.get("title", "").lower()
    summary_lower = video.get("summary", "").lower()
    combined = title_lower + " " + summary_lower
    for topic in TRENDING_TOPICS:
        if topic in combined:
            score += 5

    # Tool count score (more tools = more content to work with)
    tool_count = len(video.get("tools", []))
    score += min(tool_count * 3, 15)

    # Penalty for already-used content
    video_id = video.get("video_id", "")
    if video_id in state.get("used_video_ids", []):
        score -= 50

    # Bonus for engaging title patterns
    engaging_words = ["secret", "free", "insane", "best", "new", "just", "easy",
                      "broke", "changed", "killed", "replaced", "zero", "beginner"]
    for word in engaging_words:
        if word in title_lower:
            score += 3

    return score


def generate_reel_script(video, transcript=None):
    """Generate a reel script from video content."""
    title = video.get("title", "AI Tool Update")
    tools = video.get("tools", [])
    summary = video.get("summary", "")
    source = video.get("source", "unknown")

    # Pick main tool for hook
    main_tool = tools[0]["name"] if tools else "this AI tool"
    second_tool = tools[1]["name"] if len(tools) > 1 else "ChatGPT"

    # Generate hook
    hook_template = random.choice(HOOK_TEMPLATES)
    hook = hook_template.format(
        tool=main_tool,
        tool2=second_tool,
        topic=title.split("(")[0].strip()[:40],
        rank=random.randint(1, 5),
    )

    # Generate key points from tools and summary
    key_points = []

    # Point from summary
    if summary:
        sentences = re.split(r'[.!?]+', summary)
        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if clean_sentences:
            key_points.append(clean_sentences[0][:100])

    # Points from tools
    for tool in tools[:4]:
        point = f"{tool['name']}: {tool['description'][:60]}"
        if tool.get("price") and tool["price"] not in ("N/A", "Various"):
            point += f" ({tool['price']})"
        key_points.append(point)

    # Points from transcript if available
    if transcript:
        # Extract interesting sentences from transcript
        t_sentences = re.split(r'[.!?]+', transcript)
        interesting = [
            s.strip() for s in t_sentences
            if len(s.strip()) > 30
            and any(kw in s.lower() for kw in ["free", "easy", "best", "new", "amazing", "powerful", "money"])
        ]
        for s in interesting[:2]:
            key_points.append(s[:100])

    # Limit to 5 key points
    key_points = key_points[:5]
    if not key_points:
        key_points = [f"{main_tool} is changing the AI game", "Here's what you need to know"]

    # Generate CTA
    cta = random.choice(CTA_TEMPLATES)

    # Generate caption with hashtags
    tool_names = [t["name"] for t in tools[:3]]
    tool_tags = " ".join([f"#{t.replace(' ', '')}" for t in tool_names])
    hashtags = random.choice(HASHTAG_SETS)

    caption = f"{hook}\n\n"
    caption += f"Tools mentioned: {', '.join(tool_names)}\n\n" if tool_names else ""
    caption += f"Source: {'Matt Wolfe' if source == 'matt_wolfe' else 'Nate Herk'}\n\n"
    caption += f"{tool_tags} {hashtags}"

    # Build voiceover script (what gets spoken)
    voiceover_parts = [hook]
    for i, point in enumerate(key_points):
        voiceover_parts.append(point)
    voiceover_parts.append(cta)

    # Build display text (what shows on screen, shorter)
    display_texts = [hook[:50]]
    for point in key_points:
        display_texts.append(point[:60])
    display_texts.append(cta[:40])

    return {
        "hook": hook,
        "key_points": key_points,
        "cta": cta,
        "voiceover_script": " ... ".join(voiceover_parts),
        "voiceover_parts": voiceover_parts,
        "display_texts": display_texts,
        "caption": caption,
        "title": title,
        "main_tool": main_tool,
        "source": source,
        "video_id": video.get("video_id", ""),
        "search_query": f"{main_tool} AI technology",
    }


def select_content(matt_path, nate_path, state_path, count=3):
    """Select top content and generate reel scripts."""
    state = load_state(state_path)
    videos = load_all_videos(matt_path, nate_path)

    if not videos:
        print("No videos found in radar repos!")
        return [], state

    # Score and sort videos
    scored = [(score_video(v, state), v) for v in videos]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Select top videos, avoiding same source consecutively
    selected = []
    used_sources = []
    for score, video in scored:
        if len(selected) >= count:
            break
        # Try to alternate sources
        if len(selected) < count:
            selected.append(video)
            used_sources.append(video.get("source"))

    # Generate scripts
    scripts = []
    for video in selected:
        # Try to fetch transcript for richer content
        transcript = None
        video_id = video.get("video_id")
        if video_id:
            transcript = fetch_transcript(video_id)

        script = generate_reel_script(video, transcript)
        scripts.append(script)

        # Update state
        if video_id:
            state["used_video_ids"].append(video_id)

    return scripts, state


if __name__ == "__main__":
    # Test: load and display content
    from dotenv import load_dotenv
    load_dotenv()

    matt_path = os.getenv("RADAR_MATT_PATH", "../LATEST-AI-RADAR")
    nate_path = os.getenv("RADAR_NATE_PATH", "../NATE-HERK-RADAR")
    state_path = os.path.join(os.path.dirname(__file__), "..", "state.json")

    scripts, state = select_content(matt_path, nate_path, state_path, count=3)

    for i, script in enumerate(scripts, 1):
        print(f"\n{'='*60}")
        print(f"REEL #{i}: {script['title']}")
        print(f"{'='*60}")
        print(f"HOOK: {script['hook']}")
        print(f"\nKEY POINTS:")
        for j, point in enumerate(script['key_points'], 1):
            print(f"  {j}. {point}")
        print(f"\nCTA: {script['cta']}")
        print(f"\nVOICEOVER: {script['voiceover_script'][:200]}...")
        print(f"\nCAPTION:\n{script['caption']}")
