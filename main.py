#!/usr/bin/env python3
"""
Smart Video Speed Controller
Speed up video segments without subtitles while maintaining normal speed during subtitle segments.
"""

import os
import sys
import json
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
import argparse
from tqdm import tqdm


@dataclass
class SubtitleSegment:
    """Subtitle segment representation"""
    start_time: float
    end_time: float
    text: str


@dataclass
class VideoSegment:
    """Video segment with specific speed"""
    start_time: float
    end_time: float
    speed: float
    has_subtitle: bool


class VideoSpeedProcessor:
    """Main class for processing videos with dynamic speed"""

    def __init__(self, input_file: str, output_file: str,
                 speed_no_subtitle: float = 2.0,
                 speed_with_subtitle: float = 1.0,
                 subtitle_buffer: float = 0.5):
        """
        Initialize processor

        Args:
            input_file: Path to input video file (MKV)
            output_file: Path to output video file
            speed_no_subtitle: Speed when no subtitle present (default: 2x)
            speed_with_subtitle: Speed when subtitle present (default: 1x)
            subtitle_buffer: Time buffer before/after subtitle (seconds)
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.speed_no_subtitle = speed_no_subtitle
        self.speed_with_subtitle = speed_with_subtitle
        self.subtitle_buffer = subtitle_buffer

        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not installed. Please install FFmpeg first.")

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(['ffmpeg', '-version'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False

    def _extract_subtitles(self) -> List[SubtitleSegment]:
        """Extract subtitles from MKV file"""
        print("Extracting subtitles from video...")

        # Gunakan ffprobe untuk mendapatkan info stream
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', str(self.input_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("Failed to read video info")

        streams = json.loads(result.stdout)['streams']

        subtitle_streams = [s for s in streams if s.get('codec_type') == 'subtitle']

        if not subtitle_streams:
            print("No subtitles found in video")
            return []

        # Use first subtitle stream
        subtitle_index = subtitle_streams[0]['index']

        # Extract subtitle to temporary file
        with tempfile.NamedTemporaryFile(suffix='.srt', delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [
            'ffmpeg', '-i', str(self.input_file),
            '-map', f'0:{subtitle_index}',
            '-c:s', 'srt', tmp_path, '-y'
        ]

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            os.unlink(tmp_path)
            raise RuntimeError("Failed to extract subtitles")

        subtitles = self._parse_srt(tmp_path)
        os.unlink(tmp_path)

        print(f"Successfully extracted {len(subtitles)} subtitles")
        return subtitles

    def _parse_srt(self, srt_file: str) -> List[SubtitleSegment]:
        """Parse SRT file into SubtitleSegment list"""
        subtitles = []

        with open(srt_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        # Split by double newline
        blocks = content.strip().split('\n\n')

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                timing_line = lines[1]
                start_str, end_str = timing_line.split(' --> ')

                start_time = self._parse_time(start_str.strip())
                end_time = self._parse_time(end_str.strip())

                text = ' '.join(lines[2:])

                subtitles.append(SubtitleSegment(start_time, end_time, text))

        return sorted(subtitles, key=lambda x: x.start_time)

    def _parse_time(self, time_str: str) -> float:
        """Convert SRT time format to seconds"""
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')

        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    def _get_video_duration(self) -> float:
        """Get video duration in seconds"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', str(self.input_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError("Failed to get video duration")

        format_info = json.loads(result.stdout)['format']
        return float(format_info['duration'])

    def _create_video_segments(self, subtitles: List[SubtitleSegment],
                               video_duration: float) -> List[VideoSegment]:
        """Create video segments with appropriate speeds"""
        segments = []
        current_time = 0.0

        for subtitle in subtitles:
            sub_start = max(0, subtitle.start_time - self.subtitle_buffer)
            sub_end = min(video_duration, subtitle.end_time + self.subtitle_buffer)

            if current_time < sub_start:
                segments.append(VideoSegment(
                    current_time, sub_start,
                    self.speed_no_subtitle, False
                ))

            segments.append(VideoSegment(
                sub_start, sub_end,
                self.speed_with_subtitle, True
            ))

            current_time = sub_end
        if current_time < video_duration:
            segments.append(VideoSegment(
                current_time, video_duration,
                self.speed_no_subtitle, False
            ))

        return segments

    def _process_video(self, segments: List[VideoSegment]):
        """Process video with defined segments"""
        print("\nProcessing video...")

        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            segment_files = []

            for i, segment in enumerate(tqdm(segments, desc="Processing segments")):
                output_segment = temp_path / f"segment_{i:04d}.mkv"

                duration = segment.end_time - segment.start_time
                cmd = [
                    'ffmpeg', '-i', str(self.input_file),
                    '-ss', str(segment.start_time),
                    '-t', str(duration),
                    '-filter_complex',
                    f"[0:v]setpts={1 / segment.speed}*PTS[v];[0:a]atempo={segment.speed}[a]",
                    '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-c:a', 'aac',
                    str(output_segment), '-y'
                ]

                if segment.has_subtitle:
                    cmd.extend(['-c:s', 'copy'])

                subprocess.run(cmd, capture_output=True)
                segment_files.append(output_segment)

            print("\nConcatenating segments...")
            self._concat_segments(segment_files)

    def _concat_segments(self, segment_files: List[Path]):
        """Concatenate all segments into single file"""
        # Create file list for ffmpeg concat
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for segment in segment_files:
                f.write(f"file '{segment}'\n")
            list_file = f.name

        # FFmpeg concat
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            str(self.output_file), '-y'
        ]

        result = subprocess.run(cmd, capture_output=True)
        os.unlink(list_file)

        if result.returncode != 0:
            raise RuntimeError("Failed to concatenate video segments")

    def process(self):
        """Main processing function"""
        print(f"Smart Video Speed Controller")
        print(f"Input: {self.input_file}")
        print(f"Output: {self.output_file}")
        print(f"Speed without subtitles: {self.speed_no_subtitle}x")
        print(f"Speed with subtitles: {self.speed_with_subtitle}x")
        print(f"Subtitle buffer: {self.subtitle_buffer}s\n")

        try:
            subtitles = self._extract_subtitles()

            video_duration = self._get_video_duration()
            print(f"Video duration: {video_duration:.1f} seconds")

            segments = self._create_video_segments(subtitles, video_duration)
            print(f"Total segments: {len(segments)}")

            output_duration = sum(
                (seg.end_time - seg.start_time) / seg.speed
                for seg in segments
            )
            print(f"Estimated output duration: {output_duration:.1f} seconds")
            print(f"Time saved: {(1 - output_duration / video_duration) * 100:.1f}%")

            self._process_video(segments)

            print(f"\nCompleted! Video saved to: {self.output_file}")

        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Smart Video Speed Controller - Dynamically speed up video based on subtitles"
    )

    parser.add_argument('input', help='Input video file (MKV)')
    parser.add_argument('output', help='Output video file')
    parser.add_argument(
        '--speed-no-sub',
        type=float,
        default=2.0,
        help='Speed when no subtitle present (default: 2.0)'
    )
    parser.add_argument(
        '--speed-with-sub',
        type=float,
        default=1.0,
        help='Speed when subtitle present (default: 1.0)'
    )
    parser.add_argument(
        '--buffer',
        type=float,
        default=0.5,
        help='Time buffer before/after subtitle in seconds (default: 0.5)'
    )

    args = parser.parse_args()

    if args.speed_no_sub <= 0 or args.speed_with_sub <= 0:
        print("Error: Speed must be greater than 0")
        sys.exit(1)

    if args.buffer < 0:
        print("Error: Buffer cannot be negative")
        sys.exit(1)
    processor = VideoSpeedProcessor(
        args.input,
        args.output,
        args.speed_no_sub,
        args.speed_with_sub,
        args.buffer
    )

    processor.process()


if __name__ == "__main__":
    main()