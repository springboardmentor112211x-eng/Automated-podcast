"""
Speaker diarization is intentionally disabled.
The original implementation is preserved below as comments for reference only.
"""

# import torch
# from pyannote.audio import Pipeline
#
# _PIPELINE = None
#
#
# def _load_pipeline():
#     global _PIPELINE
#     if _PIPELINE:
#         return _PIPELINE
#
#     if hasattr(torch.serialization, "add_safe_globals"):
#         from torch.torch_version import TorchVersion
#         import pyannote.audio.core.task as task
#         torch.serialization.add_safe_globals([
#             TorchVersion,
#             task.Specifications,
#             task.Problem,
#             task.Resolution
#         ])
#
#     _PIPELINE = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization-3.1"
#     )
#     return _PIPELINE
#
#
# def diarize(audio_path, max_speakers=2):
#     pipeline = _load_pipeline()
#
#     diarization = pipeline(
#         audio_path,
#         min_speakers=1,
#         max_speakers=max_speakers
#     )
#
#     segments = []
#     for turn, _, speaker in diarization.itertracks(yield_label=True):
#         if turn.end - turn.start < 0.7:
#             continue
#         segments.append({
#             "start": float(turn.start),
#             "end": float(turn.end),
#             "speaker": speaker
#         })
#
#     segments = smooth_segments(segments)
#     return {
#         "segments": segments,
#         "speaker_count": len(set(s["speaker"] for s in segments))
#     }
#
#
# def smooth_segments(segments, max_gap=0.5):
#     if not segments:
#         return []
#
#     merged = [segments[0]]
#     for seg in segments[1:]:
#         prev = merged[-1]
#         if (
#             seg["speaker"] == prev["speaker"]
#             and seg["start"] - prev["end"] <= max_gap
#         ):
#             prev["end"] = seg["end"]
#         else:
#             merged.append(seg)
#     return merged


def diarize(*args, **kwargs):
    """Disabled placeholder to prevent accidental use."""
    raise RuntimeError("Speaker diarization is disabled in this build. See comments for reference implementation.")


def smooth_segments(*args, **kwargs):
    """Disabled placeholder to prevent accidental use."""
    raise RuntimeError("Speaker diarization is disabled in this build. See comments for reference implementation.")