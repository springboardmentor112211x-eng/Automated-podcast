"""
Podcast Transcription & Segmentation CLI Tool
Usage: python cli.py <command> [options]
"""

import argparse
import sys
import os


def cmd_transcribe(args):
    """Transcribe audio file"""
    from src.transcription.transcriber import transcribe_audio
    from src.segmentation.segmenter import create_transcript_with_timestamps
    
    print(f"Transcribing: {args.audio}")
    print(f"Model: {args.model}")
    print("Please wait...\n")
    
    result = transcribe_audio(args.audio, model_size=args.model, translate=args.translate)
    segments = result.get("segments", [])
    
    if args.timestamps:
        output = create_transcript_with_timestamps(segments)
    else:
        output = result.get("text", "")
    
    # Save to file or print
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Transcript saved to: {args.output}")
    else:
        print("=" * 50)
        print("TRANSCRIPT:")
        print("=" * 50)
        print(output)


def cmd_analyze(args):
    """Analyze audio file"""
    from src.audio_analysis.analyzer import get_audio_info, detect_silence, format_duration
    
    print(f"Analyzing: {args.audio}\n")
    
    info = get_audio_info(args.audio)
    print("AUDIO INFO:")
    print(f"  Duration: {info['duration_formatted']}")
    print(f"  Channels: {info['channels']}")
    print(f"  Sample Rate: {info['sample_rate']} Hz")
    print(f"  Format: {info['format']}")
    
    if args.silence:
        print("\nDETECTING SILENCE...")
        silences = detect_silence(args.audio)
        print(f"  Found {len(silences)} silent portions")
        for start, end in silences[:5]:
            print(f"    {format_duration(start/1000)} - {format_duration(end/1000)}")


def cmd_extract(args):
    """Extract clip from audio"""
    from src.audio_analysis.analyzer import extract_clip
    
    print(f"Extracting clip from {args.audio}")
    print(f"  Start: {args.start}s")
    print(f"  End: {args.end}s")
    
    output = extract_clip(args.audio, args.start, args.end, args.output)
    print(f"  Saved to: {output}")


def cmd_segment(args):
    """Transcribe and segment audio"""
    from src.transcription.transcriber import transcribe_audio
    from src.segmentation.segmenter import segment_by_time, format_timestamp
    
    print(f"Transcribing and segmenting: {args.audio}")
    print(f"Chunk duration: {args.duration} seconds")
    print("Please wait...\n")
    
    result = transcribe_audio(args.audio, model_size=args.model)
    segments = result.get("segments", [])
    chunks = segment_by_time(segments, chunk_duration=args.duration)
    
    output_lines = []
    for i, chunk in enumerate(chunks, 1):
        header = f"--- Chunk {i} ({format_timestamp(chunk['start'])} - {format_timestamp(chunk['end'])}) ---"
        output_lines.append(header)
        output_lines.append(chunk['text'])
        output_lines.append("")
    
    output = "\n".join(output_lines)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Segments saved to: {args.output}")
    else:
        print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Podcast Transcription & Segmentation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Transcribe command
    p_trans = subparsers.add_parser("transcribe", help="Transcribe audio to text")
    p_trans.add_argument("audio", help="Path to audio file")
    p_trans.add_argument("-m", "--model", default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model size")
    p_trans.add_argument("-o", "--output", help="Save transcript to file")
    p_trans.add_argument("-t", "--timestamps", action="store_true", help="Include timestamps")
    p_trans.add_argument("--translate", action="store_true", help="Translate to English")
    
    # Analyze command
    p_analyze = subparsers.add_parser("analyze", help="Analyze audio file")
    p_analyze.add_argument("audio", help="Path to audio file")
    p_analyze.add_argument("-s", "--silence", action="store_true", help="Detect silence")
    
    # Extract command
    p_extract = subparsers.add_parser("extract", help="Extract clip from audio")
    p_extract.add_argument("audio", help="Path to audio file")
    p_extract.add_argument("--start", type=float, required=True, help="Start time in seconds")
    p_extract.add_argument("--end", type=float, required=True, help="End time in seconds")
    p_extract.add_argument("-o", "--output", required=True, help="Output file path")
    
    # Segment command
    p_seg = subparsers.add_parser("segment", help="Transcribe and segment by time")
    p_seg.add_argument("audio", help="Path to audio file")
    p_seg.add_argument("-d", "--duration", type=float, default=60, help="Chunk duration in seconds")
    p_seg.add_argument("-m", "--model", default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model size")
    p_seg.add_argument("-o", "--output", help="Save segments to file")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    commands = {
        "transcribe": cmd_transcribe,
        "analyze": cmd_analyze,
        "extract": cmd_extract,
        "segment": cmd_segment,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
