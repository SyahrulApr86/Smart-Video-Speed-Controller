"""
FFmpeg wrapper for video processing operations
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any

from .config import Config
from .exceptions import VideoProcessingError, FFmpegError


class FFmpegWrapper:
    """Wrapper for FFmpeg operations"""
    
    @staticmethod
    def is_installed() -> bool:
        """Check if FFmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
    
    @staticmethod
    def get_video_info(input_file: Path) -> Dict[str, Any]:
        """Get video information using ffprobe"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', str(input_file)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Failed to read video info: {e.stderr}")
        except json.JSONDecodeError as e:
            raise VideoProcessingError(f"Failed to parse video info: {e}")
    
    @staticmethod
    def extract_subtitle_to_srt(input_file: Path, subtitle_index: int, output_file: Path) -> None:
        """Extract subtitle stream to SRT file"""
        cmd = [
            'ffmpeg', '-i', str(input_file),
            '-map', f'0:{subtitle_index}',
            '-c:s', Config.SUBTITLE_CODEC,
            str(output_file), '-y'
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise FFmpegError(f"Failed to extract subtitles: {e.stderr}")
    
    @staticmethod
    def process_video_segment(input_file: Path, output_file: Path, start_time: float, 
                            duration: float, speed: float, has_subtitle: bool = False) -> None:
        """Process a single video segment with speed adjustment"""
        cmd = [
            'ffmpeg', '-i', str(input_file),
            '-ss', str(start_time),
            '-t', str(duration),
            '-filter_complex',
            f"[0:v]setpts={1 / speed}*PTS[v];[0:a]atempo={speed}[a]",
            '-map', '[v]', '-map', '[a]',
            '-c:v', Config.VIDEO_CODEC, '-preset', Config.VIDEO_PRESET,
            '-c:a', Config.AUDIO_CODEC,
            str(output_file), '-y'
        ]
        
        if has_subtitle:
            cmd.extend(['-c:s', 'copy'])
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Failed to process segment {output_file}: {e.stderr}")
    
    @staticmethod
    def concatenate_videos(segment_files: list[Path], output_file: Path, list_file: str) -> None:
        """Concatenate video segments using FFmpeg"""
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            str(output_file), '-y'
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(f"Failed to concatenate segments: {e.stderr}")