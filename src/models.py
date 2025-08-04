"""
Data models for Smart Video Speed Controller
"""

from dataclasses import dataclass


@dataclass
class SubtitleSegment:
    """Subtitle segment representation"""
    start_time: float
    end_time: float
    text: str
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time


@dataclass
class VideoSegment:
    """Video segment with specific speed"""
    start_time: float
    end_time: float
    speed: float
    has_subtitle: bool
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds"""
        return self.end_time - self.start_time
    
    @property
    def output_duration(self) -> float:
        """Get output duration after speed adjustment"""
        return self.duration / self.speed