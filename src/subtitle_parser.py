"""
Subtitle parser for SRT files
"""

from pathlib import Path
from typing import List, Optional

from .config import Config
from .models import SubtitleSegment
from .exceptions import SubtitleExtractionError


class SubtitleParser:
    """Parser for subtitle files"""
    
    @staticmethod
    def parse_srt_file(srt_file: Path) -> List[SubtitleSegment]:
        """Parse SRT file into SubtitleSegment list"""
        try:
            content = SubtitleParser._read_srt_file(srt_file)
            blocks = content.strip().split(Config.SRT_BLOCK_DELIMITER)
            subtitles = []
            
            for block in blocks:
                subtitle = SubtitleParser._parse_srt_block(block.strip())
                if subtitle:
                    subtitles.append(subtitle)
            
            return sorted(subtitles, key=lambda x: x.start_time)
            
        except Exception as e:
            raise SubtitleExtractionError(f"Failed to parse SRT file {srt_file}: {e}")
    
    @staticmethod
    def _read_srt_file(srt_file: Path) -> str:
        """Read SRT file with proper encoding handling"""
        try:
            with open(srt_file, 'r', encoding=Config.ENCODING_UTF8_SIG) as f:
                return f.read()
        except UnicodeDecodeError:
            with open(srt_file, 'r', encoding=Config.ENCODING_UTF8) as f:
                return f.read()
    
    @staticmethod
    def _parse_srt_block(block: str) -> Optional[SubtitleSegment]:
        """Parse a single SRT block"""
        lines = block.split('\n')
        if len(lines) < Config.MIN_SRT_LINES:
            return None
        
        timing_line = lines[1]
        if Config.SRT_TIME_DELIMITER not in timing_line:
            return None
        
        try:
            start_str, end_str = timing_line.split(Config.SRT_TIME_DELIMITER)
            start_time = SubtitleParser._parse_srt_time(start_str.strip())
            end_time = SubtitleParser._parse_srt_time(end_str.strip())
            text = ' '.join(lines[2:])
            
            return SubtitleSegment(start_time, end_time, text)
            
        except (ValueError, IndexError) as e:
            raise SubtitleExtractionError(f"Invalid SRT block format: {e}")
    
    @staticmethod
    def _parse_srt_time(time_str: str) -> float:
        """Convert SRT time format to seconds"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        
        if len(parts) != 3:
            raise ValueError(f"Invalid time format: {time_str}")
        
        try:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            
            return (hours * Config.SECONDS_PER_HOUR + 
                    minutes * Config.SECONDS_PER_MINUTE + 
                    seconds)
        except ValueError as e:
            raise ValueError(f"Invalid time components in {time_str}: {e}")