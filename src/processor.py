"""
Main video processing logic
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List

from tqdm import tqdm

from .config import Config
from .exceptions import VideoProcessingError, SubtitleExtractionError, ValidationError
from .ffmpeg_wrapper import FFmpegWrapper
from .models import SubtitleSegment, VideoSegment
from .subtitle_parser import SubtitleParser


class VideoSpeedProcessor:
    """Main class for processing videos with dynamic speed"""

    def __init__(self, input_file: str, output_file: str,
                 speed_no_subtitle: float = Config.DEFAULT_SPEED_NO_SUBTITLE,
                 speed_with_subtitle: float = Config.DEFAULT_SPEED_WITH_SUBTITLE,
                 subtitle_buffer: float = Config.DEFAULT_SUBTITLE_BUFFER):
        """
        Initialize processor

        Args:
            input_file: Path to input video file (MKV)
            output_file: Path to output video file
            speed_no_subtitle: Speed when no subtitle present
            speed_with_subtitle: Speed when subtitle present
            subtitle_buffer: Time buffer before/after subtitle (seconds)
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.speed_no_subtitle = speed_no_subtitle
        self.speed_with_subtitle = speed_with_subtitle
        self.subtitle_buffer = subtitle_buffer
        
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Validate input parameters"""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        if not FFmpegWrapper.is_installed():
            raise RuntimeError("FFmpeg not installed. Please install FFmpeg first.")
        
        if self.speed_no_subtitle <= 0 or self.speed_with_subtitle <= 0:
            raise ValidationError("Speed values must be greater than 0")
        
        if self.subtitle_buffer < 0:
            raise ValidationError("Subtitle buffer cannot be negative")

    def _extract_subtitles(self) -> List[SubtitleSegment]:
        """Extract subtitles from video file"""
        print("Extracting subtitles from video...")
        
        try:
            video_info = FFmpegWrapper.get_video_info(self.input_file)
            subtitle_streams = self._find_subtitle_streams(video_info['streams'])
            
            if not subtitle_streams:
                print("No subtitles found in video")
                return []
            
            subtitle_index = subtitle_streams[0]['index']
            
            with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            try:
                FFmpegWrapper.extract_subtitle_to_srt(self.input_file, subtitle_index, tmp_path)
                subtitles = SubtitleParser.parse_srt_file(tmp_path)
                print(f"Successfully extracted {len(subtitles)} subtitles")
                return subtitles
            finally:
                tmp_path.unlink(missing_ok=True)
                
        except Exception as e:
            raise SubtitleExtractionError(f"Failed to extract subtitles: {e}")
    
    def _find_subtitle_streams(self, streams: List[dict]) -> List[dict]:
        """Find subtitle streams in video"""
        return [s for s in streams if s.get('codec_type') == 'subtitle']

    def _get_video_duration(self) -> float:
        """Get video duration in seconds"""
        try:
            video_info = FFmpegWrapper.get_video_info(self.input_file)
            return float(video_info['format']['duration'])
        except Exception as e:
            raise VideoProcessingError(f"Failed to get video duration: {e}")

    def _create_video_segments(self, subtitles: List[SubtitleSegment],
                               video_duration: float) -> List[VideoSegment]:
        """Create video segments with appropriate speeds"""
        segments = []
        current_time = 0.0

        for subtitle in subtitles:
            sub_start = self._calculate_subtitle_start(subtitle.start_time)
            sub_end = self._calculate_subtitle_end(subtitle.end_time, video_duration)
            
            # Add segment before subtitle if there's a gap
            if current_time < sub_start:
                segments.append(self._create_non_subtitle_segment(current_time, sub_start))
            
            # Add subtitle segment
            segments.append(self._create_subtitle_segment(sub_start, sub_end))
            current_time = sub_end

        if current_time < video_duration:
            segments.append(self._create_non_subtitle_segment(current_time, video_duration))

        return segments
    
    def _calculate_subtitle_start(self, subtitle_start: float) -> float:
        """Calculate subtitle segment start time with buffer"""
        return max(0, subtitle_start - self.subtitle_buffer)
    
    def _calculate_subtitle_end(self, subtitle_end: float, video_duration: float) -> float:
        """Calculate subtitle segment end time with buffer"""
        return min(video_duration, subtitle_end + self.subtitle_buffer)
    
    def _create_non_subtitle_segment(self, start: float, end: float) -> VideoSegment:
        """Create a video segment without subtitles"""
        return VideoSegment(start, end, self.speed_no_subtitle, False)
    
    def _create_subtitle_segment(self, start: float, end: float) -> VideoSegment:
        """Create a video segment with subtitles"""
        return VideoSegment(start, end, self.speed_with_subtitle, True)

    def _process_video(self, segments: List[VideoSegment]) -> None:
        """Process video with defined segments"""
        print("\\nProcessing video...")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            segment_files = self._process_segments(segments, temp_path)
            
            print("\\nConcatenating segments...")
            self._concat_segments(segment_files)
    
    def _process_segments(self, segments: List[VideoSegment], temp_path: Path) -> List[Path]:
        """Process individual video segments"""
        segment_files = []
        
        for i, segment in enumerate(tqdm(segments, desc="Processing segments")):
            output_segment = temp_path / Config.SEGMENT_FILENAME_FORMAT.format(i)
            self._process_single_segment(segment, output_segment)
            segment_files.append(output_segment)
        
        return segment_files
    
    def _process_single_segment(self, segment: VideoSegment, output_file: Path) -> None:
        """Process a single video segment"""
        FFmpegWrapper.process_video_segment(
            self.input_file, output_file, segment.start_time, 
            segment.duration, segment.speed, segment.has_subtitle
        )
    
    def _concat_segments(self, segment_files: List[Path]) -> None:
        """Concatenate all segments into single file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=Config.CONCAT_FILE_SUFFIX, delete=False) as f:
            self._write_concat_file(f, segment_files)
            list_file = f.name
        
        try:
            FFmpegWrapper.concatenate_videos(segment_files, self.output_file, list_file)
        finally:
            os.unlink(list_file)
    
    def _write_concat_file(self, file_handle, segment_files: List[Path]) -> None:
        """Write file list for FFmpeg concat"""
        for segment in segment_files:
            file_handle.write(f"file '{segment}'\\n")

    def process(self) -> None:
        """Main processing function"""
        self._print_configuration()
        
        try:
            subtitles = self._extract_subtitles()
            video_duration = self._get_video_duration()
            
            self._print_video_info(video_duration)
            
            segments = self._create_video_segments(subtitles, video_duration)
            self._print_segment_info(segments, video_duration)
            
            self._process_video(segments)
            
            print(f"\\nCompleted! Video saved to: {self.output_file}")
            
        except Exception as e:
            print(f"\\nError: {e}")
            sys.exit(1)
    
    def _print_configuration(self) -> None:
        """Print processing configuration"""
        print("Smart Video Speed Controller")
        print(f"Input: {self.input_file}")
        print(f"Output: {self.output_file}")
        print(f"Speed without subtitles: {self.speed_no_subtitle}x")
        print(f"Speed with subtitles: {self.speed_with_subtitle}x")
        print(f"Subtitle buffer: {self.subtitle_buffer}s\\n")
    
    def _print_video_info(self, video_duration: float) -> None:
        """Print video information"""
        print(f"Video duration: {video_duration:.1f} seconds")
    
    def _print_segment_info(self, segments: List[VideoSegment], video_duration: float) -> None:
        """Print segment processing information"""
        print(f"Total segments: {len(segments)}")
        
        output_duration = sum(seg.output_duration for seg in segments)
        time_saved_percent = (1 - output_duration / video_duration) * 100
        
        print(f"Estimated output duration: {output_duration:.1f} seconds")
        print(f"Time saved: {time_saved_percent:.1f}%")