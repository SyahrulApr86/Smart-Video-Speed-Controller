"""
Command line interface for Smart Video Speed Controller
"""

import argparse
import sys

from .config import Config
from .exceptions import ValidationError
from .processor import VideoSpeedProcessor


class ArgumentParser:
    """Command line argument parser"""
    
    @staticmethod
    def create_parser() -> argparse.ArgumentParser:
        """Create and configure argument parser"""
        parser = argparse.ArgumentParser(
            description="Smart Video Speed Controller - Dynamically speed up video based on subtitles"
        )
        
        parser.add_argument('input', help='Input video file (MKV)')
        parser.add_argument('output', help='Output video file')
        parser.add_argument(
            '--speed-no-sub',
            type=float,
            default=Config.DEFAULT_SPEED_NO_SUBTITLE,
            help=f'Speed when no subtitle present (default: {Config.DEFAULT_SPEED_NO_SUBTITLE})'
        )
        parser.add_argument(
            '--speed-with-sub',
            type=float,
            default=Config.DEFAULT_SPEED_WITH_SUBTITLE,
            help=f'Speed when subtitle present (default: {Config.DEFAULT_SPEED_WITH_SUBTITLE})'
        )
        parser.add_argument(
            '--buffer',
            type=float,
            default=Config.DEFAULT_SUBTITLE_BUFFER,
            help=f'Time buffer before/after subtitle in seconds (default: {Config.DEFAULT_SUBTITLE_BUFFER})'
        )
        
        return parser
    
    @staticmethod
    def validate_arguments(args) -> None:
        """Validate command line arguments"""
        if args.speed_no_sub <= 0 or args.speed_with_sub <= 0:
            raise ValidationError("Speed must be greater than 0")
        
        if args.buffer < 0:
            raise ValidationError("Buffer cannot be negative")


def main() -> None:
    """Main CLI entry point"""
    try:
        parser = ArgumentParser.create_parser()
        args = parser.parse_args()
        
        ArgumentParser.validate_arguments(args)
        
        processor = VideoSpeedProcessor(
            args.input,
            args.output,
            args.speed_no_sub,
            args.speed_with_sub,
            args.buffer
        )
        
        processor.process()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)