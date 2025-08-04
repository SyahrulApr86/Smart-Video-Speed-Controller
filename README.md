# Smart Video Speed Controller

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FFmpeg Required](https://img.shields.io/badge/FFmpeg-Required-red.svg)](https://ffmpeg.org/)

A Python application that intelligently adjusts video playback speed based on subtitle presence. Speed up video segments without subtitles while maintaining normal speed during subtitle segments for optimal viewing experience.

## Features

- Automatically detects subtitle segments and adjusts playback speed accordingly
- Customize speed multipliers for segments with and without subtitles
- Add time buffer before and after subtitles for smooth transitions

## How It Works

1. **Subtitle Extraction**: Extracts embedded subtitles from MKV files
2. **Segment Analysis**: Analyzes video timeline to identify subtitle and non-subtitle segments
3. **Speed Processing**: Applies different speed multipliers to each segment
4. **Concatenation**: Merges all processed segments into final output video

## Requirements

### System Dependencies
- **Python 3.8+**
- **FFmpeg** (must be installed and available in PATH)

### Python Dependencies
- `tqdm` - Progress bar display
- Standard library modules (no additional packages required)

## Installation

### 1. Install FFmpeg

#### Windows
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

#### macOS
```bash
# Using Homebrew
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Clone Repository
```bash
git clone https://github.com/SyahrulApr86/Smart-Video-Speed-Controller.git
cd smart-video-speed-controller
```

### 3. Install Python Dependencies
```bash
pip install tqdm
```

## Usage

### Basic Usage
```bash
python main.py input.mkv output.mkv
```

### Advanced Usage with Custom Settings
```bash
python main.py input.mkv output.mkv --speed-no-sub 2.5 --speed-with-sub 1.0 --buffer 0.3
```

### Command Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `input` | string | - | Input video file path (MKV format) |
| `output` | string | - | Output video file path |
| `--speed-no-sub` | float | 2.0 | Speed multiplier for segments without subtitles |
| `--speed-with-sub` | float | 1.0 | Speed multiplier for segments with subtitles |
| `--buffer` | float | 0.5 | Time buffer (seconds) before/after subtitle segments |

### Examples

#### Speed up non-subtitle segments by 2x
```bash
python main.py anime_episode.mkv anime_episode_fast.mkv
```

#### Aggressive speedup (3x) with minimal buffer
```bash
python main.py lecture.mkv lecture_fast.mkv --speed-no-sub 3.0 --buffer 0.2
```

#### Custom speeds for both segments
```bash
python main.py movie.mkv movie_processed.mkv --speed-no-sub 1.5 --speed-with-sub 0.9
```

## Project Structure

```
smart-video-speed-controller/
├── main.py                 # Application entry point
├── src/
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration constants
│   ├── exceptions.py      # Custom exception classes
│   ├── models.py          # Data models (SubtitleSegment, VideoSegment)
│   ├── ffmpeg_wrapper.py  # FFmpeg operations wrapper
│   ├── subtitle_parser.py # SRT subtitle parsing logic
│   ├── processor.py       # Main video processing engine
│   └── cli.py             # Command-line interface
├── README.md              # Project documentation
└── CLAUDE.md              # Development guidance
```

## Technical Details

### Supported Formats
- **Input**: MKV files with embedded subtitles
- **Output**: MKV format with optimized encoding
- **Subtitles**: SRT format (extracted automatically)

### Processing Pipeline
1. **Validation**: Input file existence and FFmpeg availability
2. **Subtitle Extraction**: Extract embedded subtitles using FFmpeg
3. **Timeline Analysis**: Create speed-adjusted segments based on subtitle timing
4. **Video Processing**: Apply speed changes using FFmpeg filters
5. **Concatenation**: Merge segments into final output

### Performance Considerations
- Uses temporary directory for segment processing
- Optimized FFmpeg settings for quality/speed balance
- Automatic cleanup of intermediate files
- Progress tracking for long operations

## Output Information

The application provides detailed processing information:

```
Smart Video Speed Controller
Input: input.mkv
Output: output.mkv
Speed without subtitles: 2.0x
Speed with subtitles: 1.0x
Subtitle buffer: 0.5s

Extracting subtitles from video...
Successfully extracted 245 subtitles
Video duration: 1440.2 seconds
Total segments: 152
Estimated output duration: 1088.4 seconds
Time saved: 24.4%

Processing video...
Processing segments: 100%|██████████| 152/152

Concatenating segments...
Completed! Video saved to: output.mkv
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

