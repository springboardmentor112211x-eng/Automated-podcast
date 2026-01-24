"""Test script for audio analysis module"""

from src.audio_analysis.analyzer import (
    get_audio_info,
    detect_silence,
    get_volume_over_time,
    extract_clip,
    format_duration
)

# Path to your audio file
AUDIO_PATH = r"C:\Users\navpr\OneDrive\Desktop\INFOSYS INTERNSHIP\AUDIO.mpeg"

print("=" * 50)
print("AUDIO FILE INFORMATION")
print("=" * 50)

info = get_audio_info(AUDIO_PATH)
print(f"Duration: {info['duration_formatted']}")
print(f"Duration (seconds): {info['duration_seconds']:.2f}")
print(f"Channels: {info['channels']}")
print(f"Sample Rate: {info['sample_rate']} Hz")
print(f"Format: {info['format']}")

print("\n" + "=" * 50)
print("DETECTING SILENCE (may take a moment...)")
print("=" * 50)

silences = detect_silence(AUDIO_PATH, min_silence_ms=2000, silence_thresh_db=-40)
print(f"Found {len(silences)} silent portions (>2 seconds)")

if silences[:5]:
    print("\nFirst 5 silences:")
    for start, end in silences[:5]:
        print(f"  {format_duration(start/1000)} - {format_duration(end/1000)}")

print("\n" + "=" * 50)
print("VOLUME ANALYSIS (first 30 seconds)")
print("=" * 50)

volumes = get_volume_over_time(AUDIO_PATH, chunk_ms=5000)[:6]  # First 30 seconds
for vol in volumes:
    bar = "█" * max(0, int((vol['volume_dbfs'] + 50) / 2))
    print(f"  {format_duration(vol['time_sec'])}: {vol['volume_dbfs']:.1f} dB  {bar}")

print("\n" + "=" * 50)
print("EXTRACTING 10-SECOND CLIP (0:00 - 0:10)")
print("=" * 50)

clip_path = extract_clip(AUDIO_PATH, 0, 10, "test_clip.wav")
print(f"Clip saved to: {clip_path}")

print("\n✓ Audio analysis complete!")
