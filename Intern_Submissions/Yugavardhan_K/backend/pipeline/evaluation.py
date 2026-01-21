import jiwer
from typing import Dict, List, Optional, Any
import numpy as np

def calculate_asr_metrics(reference: List[str], hypothesis: List[str]) -> Dict[str, float]:
    """
    Calculate ASR accuracy metrics
    
    Args:
        reference: Ground truth transcripts
        hypothesis: Model-generated transcripts
    
    Returns:
        Dictionary with WER, CER, and accuracy metrics
    """
    # Combine all segments
    ref_text = " ".join(reference)
    hyp_text = " ".join(hypothesis)
    
    # Word Error Rate (WER)
    wer = jiwer.wer(ref_text, hyp_text)
    
    # Character Error Rate (CER)
    cer = jiwer.cer(ref_text, hyp_text)
    
    # Word Accuracy
    word_accuracy = 1.0 - wer
    
    # Match Error Rate (MER)
    mer = jiwer.mer(ref_text, hyp_text)
    
    # Word Information Lost (WIL)
    wil = jiwer.wil(ref_text, hyp_text)
    
    return {
        "wer": round(wer * 100, 2),  # Convert to percentage
        "cer": round(cer * 100, 2),
        "word_accuracy": round(word_accuracy * 100, 2),
        "mer": round(mer * 100, 2),
        "wil": round(wil * 100, 2)
    }


def calculate_topic_segmentation_metrics(
    predicted_boundaries: List[int],
    ground_truth_boundaries: List[int],
    tolerance: int = 3
) -> Dict[str, float]:
    """
    Evaluate topic segmentation quality
    
    Args:
        predicted_boundaries: Predicted segment boundaries (sentence indices)
        ground_truth_boundaries: Actual segment boundaries
        tolerance: Window size for matching boundaries
    
    Returns:
        Precision, Recall, F1 score
    """
    true_positives = 0
    
    for pred_boundary in predicted_boundaries:
        for gt_boundary in ground_truth_boundaries:
            if abs(pred_boundary - gt_boundary) <= tolerance:
                true_positives += 1
                break
    
    precision = true_positives / len(predicted_boundaries) if predicted_boundaries else 0
    recall = true_positives / len(ground_truth_boundaries) if ground_truth_boundaries else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2)
    }


def calculate_summarization_metrics(
    reference_summaries: List[str],
    generated_summaries: List[str]
) -> Dict[str, float]:
    """
    Evaluate summary quality using ROUGE scores
    Requires: pip install rouge-score
    """
    from rouge_score import rouge_scorer
    
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    
    rouge1_scores = []
    rouge2_scores = []
    rougeL_scores = []
    
    for ref, gen in zip(reference_summaries, generated_summaries):
        scores = scorer.score(ref, gen)
        rouge1_scores.append(scores['rouge1'].fmeasure)
        rouge2_scores.append(scores['rouge2'].fmeasure)
        rougeL_scores.append(scores['rougeL'].fmeasure)
    
    return {
        "rouge1_f1": round(float(np.mean(rouge1_scores)) * 100, 2),
        "rouge2_f1": round(float(np.mean(rouge2_scores)) * 100, 2),
        "rougeL_f1": round(float(np.mean(rougeL_scores)) * 100, 2)
    }


def evaluate_pipeline_performance(
    transcript: List[Dict],
    topics: List[Dict],
    ground_truth_transcript: Optional[List[str]] = None,
    ground_truth_topics: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Comprehensive pipeline evaluation
    
    Returns:
        Complete metrics dictionary
    """
    metrics: Dict[str, Any] = {
        "transcript_segments": len(transcript),
        "topics_identified": len(topics),
        "avg_segment_length": 0,
        "avg_topic_duration": 0,
        "coverage": 0
    }
    
    # Basic statistics
    if transcript:
        segment_lengths = [seg.get("end", 0) - seg.get("start", 0) for seg in transcript]
        metrics["avg_segment_length"] = int(round(np.mean(segment_lengths), 2))
    
    if topics:
        topic_durations = [t.get("end_time", 0) - t.get("start_time", 0) for t in topics]
        metrics["avg_topic_duration"] = int(round(np.mean(topic_durations), 2))
        
        # Calculate coverage (how much of audio is covered by topics)
        total_audio_time = max([seg.get("end", 0) for seg in transcript]) if transcript else 0
        total_topic_time = sum(topic_durations)
        metrics["coverage"] = int(round((total_topic_time / total_audio_time * 100), 2)) if total_audio_time > 0 else 0
    
    # ASR Metrics (if ground truth available)
    if ground_truth_transcript:
        hypothesis = [seg.get("text", "") for seg in transcript]
        asr_metrics = calculate_asr_metrics(ground_truth_transcript, hypothesis)
        metrics.update(asr_metrics)
    
    # Topic Segmentation Metrics (if ground truth available)
    if ground_truth_topics:
        pred_boundaries = [i for i, _ in enumerate(topics)]
        gt_boundaries = [i for i, _ in enumerate(ground_truth_topics)]
        seg_metrics = calculate_topic_segmentation_metrics(pred_boundaries, gt_boundaries)
        metrics["topic_segmentation"] = seg_metrics
    
    return metrics