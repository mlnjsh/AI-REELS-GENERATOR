# AI REELS GENERATOR

> Automated no-face Instagram Reels from AI/tech YouTube content

Generates 3 ready-to-post Instagram Reels daily using content from [Matt Wolfe](https://www.youtube.com/@mreflow) and [Nate Herk](https://www.youtube.com/@nateherk) YouTube channels.

## How It Works

1. **Content Selection** - Reads video summaries from both radar repos, scores by virality, picks top 3
2. **AI Voiceover** - Edge TTS (free Microsoft voice) generates voiceover with word-level timing
3. **Video Composition** - MoviePy assembles 9:16 portrait video with animated text overlays and captions
4. **Output** - Ready-to-post MP4 files + Instagram caption text with hashtags
5. **Notification** - Gmail alert when reels are ready

## Quick Start

### 1. Install dependencies
```bash
cd AI-REELS-GENERATOR
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Generate reels
```bash
python scripts/generate_reels.py
```

Output goes to `output/YYYY-MM-DD/` with 3 MP4 files + 3 caption files.

## Requirements

| Dependency | Purpose | Cost |
|---|---|---|
| Edge TTS | AI voiceover | Free |
| MoviePy | Video composition | Free |
| Pexels API | Stock footage (optional) | Free |
| YouTube API | Transcript fetching | Free |
| Gmail | Notifications | Free |
| ffmpeg | Video encoding | Free |

## Reel Format

Each reel follows a viral structure:
- **Hook** (0-3s) - Bold text + punchy voiceover
- **Key Points** (3-45s) - Rapid-fire insights with text overlays
- **CTA** (45-60s) - Follow/save call to action

Visual: Dark gradient background, bold Montserrat text, word-by-word captions, progress bar.

## Project Structure

```
AI-REELS-GENERATOR/
├── scripts/
│   ├── generate_reels.py     # Main pipeline
│   ├── content_selector.py   # Content scoring + script generation
│   ├── audio_generator.py    # Edge TTS voiceover
│   ├── video_composer.py     # MoviePy video assembly
│   └── notify.py             # Gmail notifications
├── assets/fonts/             # Montserrat font files
├── output/                   # Generated reels (by date)
├── state.json                # Tracks used content
└── .env                      # API keys and paths
```

## Data Sources

- [LATEST-AI-RADAR](https://github.com/mlnjsh/LATEST-AI-RADAR) - Matt Wolfe channel tracking
- [NATE-HERK-RADAR](https://github.com/mlnjsh/NATE-HERK-RADAR) - Nate Herk channel tracking

## License

MIT

---

*Built with Python, Edge TTS, MoviePy, and YouTube Data API*


---

## Contributors & Domain Experts

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/mlnjsh">
        <img src="https://github.com/mlnjsh.png" width="80px;" alt="Milan Amrut Joshi"/><br />
        <sub><b>Milan Amrut Joshi</b></sub>
      </a><br />
      <sub>Project Author</sub>
    </td>
    <td align="center">
      <a href="https://github.com/yt-dlp">
        <img src="https://github.com/yt-dlp.png" width="80px;" alt="yt-dlp Team"/><br />
        <sub><b>yt-dlp Team</b></sub>
      </a><br />
      <sub>Video extraction and processing</sub>
    </td>
    <td align="center">
      <a href="https://github.com/openai">
        <img src="https://github.com/openai.png" width="80px;" alt="OpenAI"/><br />
        <sub><b>OpenAI</b></sub>
      </a><br />
      <sub>GPT & DALL-E for content generation</sub>
    </td>
  </tr>
</table>
