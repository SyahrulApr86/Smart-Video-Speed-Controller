"""
Custom exceptions for Smart Video Speed Controller
"""


class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    pass


class SubtitleExtractionError(Exception):
    """Custom exception for subtitle extraction errors"""
    pass


class FFmpegError(Exception):
    """Custom exception for FFmpeg related errors"""
    pass


class ValidationError(Exception):
    """Custom exception for input validation errors"""
    pass