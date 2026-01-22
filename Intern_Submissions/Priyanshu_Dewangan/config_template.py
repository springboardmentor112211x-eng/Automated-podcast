"""
Configuration Template for Podcast Insights AI
Customize these settings to match your needs
"""

# ============================================================
# AUDIO PROCESSING SETTINGS
# ============================================================

AUDIO_CONFIG = {
    # Sample rate for audio processing (Hz)
    "sample_rate": 16000,
    
    # Supported audio formats
    "supported_formats": ["mp3", "wav", "m4a", "flac"],
    
    # Max file size in MB
    "max_file_size_mb": 500,
    
    # Audio preprocessing options
    "normalize": True,
    "trim_silence": True,
    "silence_threshold_db": 40,
}

# ============================================================
# TRANSCRIPTION SETTINGS (WHISPER)
# ============================================================

TRANSCRIPTION_CONFIG = {
    # Model size: tiny, base, small, medium, large
    # Larger = more accurate but slower
    "model_size": "base",
    
    # Language (auto-detect if None)
    "language": "en",
    
    # Show transcription progress
    "verbose": False,
    
    # Use GPU if available
    "use_gpu": True,
}

# ============================================================
# TEXT PROCESSING SETTINGS
# ============================================================

TEXT_CONFIG = {
    # Filler words to remove
    "filler_words": [
        "um", "uh", "hmm", "like", "you know", 
        "i mean", "basically", "essentially"
    ],
    
    # Min/max sentence length
    "min_sentence_length": 5,
    "max_sentence_length": 500,
    
    # Remove these words before segmentation
    "stop_words": ["the", "a", "an", "and", "or", "but"],
}

# ============================================================
# SEGMENTATION SETTINGS
# ============================================================

SEGMENTATION_CONFIG = {
    # Embedding model for topic detection
    "embedding_model": "all-MiniLM-L6-v2",
    
    # Window size for similarity calculation
    "window_size": 4,
    
    # Prominence threshold for peak detection
    # Lower = more segments, Higher = fewer segments
    "prominence": 0.02,
    
    # Min distance between segments
    "min_distance": 20,
    
    # Fallback: if auto-segmentation fails, use equal chunks
    "fallback_num_chunks": 5,
}

# ============================================================
# SUMMARIZATION SETTINGS
# ============================================================

SUMMARIZATION_CONFIG = {
    # Extractive (TextRank) settings
    "extractive": {
        "ratio": 0.40,  # Keep 40% of original
        "min_sentences": 5,
    },
    
    # Abstractive (BART) settings
    "abstractive": {
        "model": "knkarthick/MEETING_SUMMARY",
        "max_length": 150,
        "min_length": 40,
        "batch_size": 1,
    },
    
    # Title generation (Headline)
    "title_generation": {
        "model": "Michau/t5-base-en-generate-headline",
        "max_new_tokens": 32,
        "min_length": 4,
    },
}

# ============================================================
# Q&A / RAG SETTINGS
# ============================================================

QA_CONFIG = {
    # QA Model
    "model": "google/flan-t5-base",  # or flan-t5-large for better quality
    
    # ChromaDB settings
    "database_path": "./podcast_knowledge_base",
    "collection_name": "podcast_segments",
    "similarity_metric": "cosine",
    
    # Search settings
    "num_search_results": 1,  # Top N chapters to retrieve
    "relevance_threshold": 0.0,  # Min similarity score (0-1)
    
    # Generation settings
    "max_new_tokens": 100,
    "temperature": 0.7,  # 0 = deterministic, 1 = creative
    "do_sample": False,  # Deterministic output
}

# ============================================================
# VALIDATION SETTINGS
# ============================================================

VALIDATION_CONFIG = {
    # Confidence thresholds
    "high_confidence_threshold": 80,  # Auto-approve
    "low_confidence_threshold": 60,   # Require validation
    
    # Validation prompts
    "require_validation": True,
    
    # Auto-save corrections
    "auto_save_corrections": True,
    
    # Audit log settings
    "audit_log_file": "human_audit_log.json",
    "backup_audit_log": True,
}

# ============================================================
# STREAMLIT UI SETTINGS
# ============================================================

UI_CONFIG = {
    # Page config
    "page_title": "Podcast Insights AI",
    "page_icon": "🎙️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
    
    # Processing timeout (seconds)
    "processing_timeout": 900,  # 15 minutes
    
    # Display settings
    "show_timestamps": True,
    "show_confidence_colors": True,
    "enable_dark_mode": True,
    
    # Output directory
    "output_dir": "./podcast_output",
    "temp_dir": "./temp",
}

# ============================================================
# PERFORMANCE SETTINGS
# ============================================================

PERFORMANCE_CONFIG = {
    # CPU threads
    "num_threads": 4,
    
    # Batch processing
    "batch_size": 32,  # For embeddings
    
    # Caching
    "enable_cache": True,
    "cache_ttl": 3600,  # 1 hour
    
    # Memory optimization
    "use_memory_map": False,
    "chunk_size": 1024,
}

# ============================================================
# SECURITY SETTINGS
# ============================================================

SECURITY_CONFIG = {
    # Prompt injection detection
    "enable_injection_detection": True,
    
    # Injection patterns
    "injection_patterns": [
        r"ignore previous instructions",
        r"system override",
        r"delete all data",
        r"you are not",
    ],
    
    # Input sanitization
    "sanitize_input": True,
    "max_query_length": 500,
    
    # File upload restrictions
    "allowed_extensions": ["mp3", "wav", "m4a", "flac"],
    "max_file_size_mb": 500,
}

# ============================================================
# LOGGING SETTINGS
# ============================================================

LOGGING_CONFIG = {
    # Log level: DEBUG, INFO, WARNING, ERROR
    "level": "INFO",
    
    # Log file
    "file": "podcast_insights.log",
    
    # Log format
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    
    # Keep logs for N days
    "retention_days": 30,
}

# ============================================================
# API SETTINGS (for FastAPI backend)
# ============================================================

API_CONFIG = {
    # Server settings
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4,
    
    # CORS settings
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    
    # Rate limiting
    "rate_limit_requests": 100,
    "rate_limit_period": 3600,  # per hour
    
    # Job cleanup
    "cleanup_completed_jobs": True,
    "job_retention_hours": 24,
}

# ============================================================
# EXAMPLES
# ============================================================

"""
HOW TO USE THESE SETTINGS:

1. In audio_processor.py:
   from config import AUDIO_CONFIG, TRANSCRIPTION_CONFIG
   self.sample_rate = AUDIO_CONFIG["sample_rate"]
   model = whisper.load_model(TRANSCRIPTION_CONFIG["model_size"])

2. In rag_system.py:
   from config import QA_CONFIG, VALIDATION_CONFIG
   self.db_path = QA_CONFIG["database_path"]
   confidence_threshold = VALIDATION_CONFIG["low_confidence_threshold"]

3. In app.py:
   from config import UI_CONFIG, VALIDATION_CONFIG
   st.set_page_config(
       title=UI_CONFIG["page_title"],
       icon=UI_CONFIG["page_icon"],
       layout=UI_CONFIG["layout"]
   )

4. Environment override:
   # Set environment variable to use different config
   # export CONFIG_PROFILE=production
   # or CONFIG_PROFILE=development
"""

# ============================================================
# PROFILES (for different use cases)
# ============================================================

PROFILES = {
    "default": {
        "whisper_model": "base",
        "num_summary_sentences": 5,
        "confidence_threshold": 60,
    },
    
    "fast": {  # Prioritize speed
        "whisper_model": "tiny",
        "num_summary_sentences": 3,
        "confidence_threshold": 70,
    },
    
    "accurate": {  # Prioritize accuracy
        "whisper_model": "large",
        "num_summary_sentences": 8,
        "confidence_threshold": 50,
    },
    
    "production": {  # For production deployment
        "whisper_model": "base",
        "enable_cache": True,
        "enable_monitoring": True,
        "enable_logging": True,
    },
}

# ============================================================
# HOW TO CUSTOMIZE
# ============================================================

"""
COMMON CUSTOMIZATIONS:

1. For faster processing (at cost of accuracy):
   TRANSCRIPTION_CONFIG["model_size"] = "tiny"
   SEGMENTATION_CONFIG["prominence"] = 0.05
   SUMMARIZATION_CONFIG["extractive"]["ratio"] = 0.30

2. For better accuracy (at cost of speed):
   TRANSCRIPTION_CONFIG["model_size"] = "large"
   SEGMENTATION_CONFIG["prominence"] = 0.01
   SUMMARIZATION_CONFIG["extractive"]["ratio"] = 0.50

3. For more chapters:
   SEGMENTATION_CONFIG["prominence"] = 0.01  # Lower = more segments

4. For fewer chapters:
   SEGMENTATION_CONFIG["prominence"] = 0.05  # Higher = fewer segments

5. For stricter validation:
   VALIDATION_CONFIG["low_confidence_threshold"] = 80

6. For automatic validation:
   VALIDATION_CONFIG["low_confidence_threshold"] = 0
"""
