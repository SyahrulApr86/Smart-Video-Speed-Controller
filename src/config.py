"""
Configuration constants for Smart Video Speed Controller
"""


class Config:
    """Application configuration constants"""
    
    # Default speed settings
    DEFAULT_SPEED_NO_SUBTITLE = 2.0
    DEFAULT_SPEED_WITH_SUBTITLE = 1.0
    DEFAULT_SUBTITLE_BUFFER = 0.5
    
    # FFmpeg settings
    VIDEO_CODEC = 'libx264'
    AUDIO_CODEC = 'aac'
    VIDEO_PRESET = 'fast'
    SUBTITLE_CODEC = 'srt'
    
    # File encoding
    ENCODING_UTF8_SIG = 'utf-8-sig'
    ENCODING_UTF8 = 'utf-8'
    
    # SRT parsing constants
    SRT_TIME_DELIMITER = ' --> '
    SRT_BLOCK_DELIMITER = '\n\n'
    MIN_SRT_LINES = 3
    
    # Time conversion constants
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_MINUTE = 60
    
    # File naming
    SEGMENT_FILENAME_FORMAT = 'segment_{:04d}.mkv'
    CONCAT_FILE_SUFFIX = '.txt'