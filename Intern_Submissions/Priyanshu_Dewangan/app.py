"""
Podcast Summarizer Streamlit Application
Comprehensive UI for podcast processing, summarization, and Q&A
"""

import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import tempfile
from pathlib import Path
import time

# Import custom modules
from audio_processor import AudioProcessor
from rag_system import RAGSystem
from utils import load_audit_log, save_audit_log

# ============================================================
# PAGE CONFIG & SESSION STATE
# ============================================================

st.set_page_config(
    page_title="Podcast Insights AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None
if "rag_system" not in st.session_state:
    st.session_state.rag_system = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "pending_validation" not in st.session_state:
    st.session_state.pending_validation = None
if "current_validation" not in st.session_state:
    st.session_state.current_validation = None

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown("# 🎙️ Podcast Insights AI")
st.sidebar.markdown("---")
st.sidebar.markdown("""
### How to Use:
1. **Upload** your podcast audio file
2. **Wait** for processing (transcription, summarization)
3. **View** chapters with timestamps and summaries
4. **Ask** questions about your podcast
5. **Track** your query history and validations
""")

st.sidebar.markdown("---")
st.sidebar.markdown("""
### Supported Formats:
- MP3, WAV, M4A, FLAC
- Duration: 30 min - 3+ hours
- Max file size: 500MB
""")

# ============================================================
# MAIN TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📊 Transcript & Summary", "💬 Q&A Chat", "📈 Query History"])

# ============================================================
# TAB 1: UPLOAD
# ============================================================

with tab1:
    st.header("📤 Upload Your Podcast")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### Instructions:
        1. **Select** a podcast audio file from your device
        2. **Ensure** the audio is clear and in a supported format
        3. **Click** "Process Podcast" to start
        4. **Wait** for processing to complete (this may take 5-15 minutes for long podcasts)
        
        ### What Happens:
        - 🎤 Audio transcription via Whisper
        - 📝 Text cleaning and preprocessing
        - 🏷️ Automatic topic segmentation
        - ✂️ Extractive + Abstractive summarization (Hybrid)
        - 🗃️ Indexing for intelligent Q&A
        """)
    
    with col2:
        st.info("💡 **Pro Tip:** Longer, clearer podcasts work best!", icon="ℹ️")
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["mp3", "wav", "m4a", "flac"],
        key="audio_uploader"
    )
    
    if uploaded_file is not None:
        st.session_state.audio_file = uploaded_file
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.metric("File Size", f"{file_size_mb:.2f} MB")
        
        with col2:
            st.metric("Format", uploaded_file.name.split(".")[-1].upper())
        
        with col3:
            st.metric("Status", "✅ Ready")
        
        st.markdown("---")
        
        # Process button
        if st.button("🚀 Process Podcast", use_container_width=True, type="primary"):
            with st.spinner("⏳ Processing your podcast... This may take a few minutes"):
                try:
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        temp_audio_path = tmp_file.name
                    
                    # Initialize processor
                    processor = AudioProcessor(output_dir="./podcast_output")
                    
                    # Process audio
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🎤 Transcribing audio...")
                    progress_bar.progress(20)
                    
                    transcript_data = processor.process_audio(temp_audio_path)
                    
                    status_text.text("📝 Cleaning transcript...")
                    progress_bar.progress(40)
                    
                    status_text.text("🏷️ Segmenting topics...")
                    progress_bar.progress(60)
                    
                    summaries_data = processor.generate_summaries(transcript_data)
                    
                    status_text.text("✂️ Creating hybrid summaries...")
                    progress_bar.progress(80)
                    
                    status_text.text("🗃️ Indexing for Q&A...")
                    progress_bar.progress(90)
                    
                    # Initialize RAG system
                    rag_system = RAGSystem()
                    rag_system.index_documents(summaries_data)
                    
                    # Store in session state
                    st.session_state.processed_data = {
                        "transcript": transcript_data,
                        "summaries": summaries_data,
                        "chapters": summaries_data,
                        "duration": transcript_data.get("duration", "Unknown"),
                        "upload_time": datetime.now().isoformat(),
                        "filename": uploaded_file.name
                    }
                    st.session_state.rag_system = rag_system
                    st.session_state.processing_complete = True
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Processing complete!")
                    time.sleep(1)
                    
                    # Clean up
                    os.unlink(temp_audio_path)
                    
                    st.success("✅ Podcast processed successfully! Go to 'Transcript & Summary' tab.")
                    
                except Exception as e:
                    st.error(f"❌ Error processing audio: {str(e)}")
                    st.info("💡 Please ensure your audio file is valid and try again.")
    
    else:
        st.info("👆 Upload an audio file to get started!")

# ============================================================
# TAB 2: TRANSCRIPT & SUMMARY
# ============================================================

with tab2:
    st.header("📊 Transcript & Summary")
    
    if not st.session_state.processing_complete:
        st.warning("⚠️ Please upload and process a podcast first (Upload tab)")
    else:
        data = st.session_state.processed_data
        
        # Header info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 Podcast", data["filename"])
        with col2:
            st.metric("⏱️ Duration", data["duration"])
        with col3:
            chapters_count = len(data["chapters"])
            st.metric("📑 Chapters", chapters_count)
        with col4:
            st.metric("📅 Processed", datetime.fromisoformat(data["upload_time"]).strftime("%Y-%m-%d %H:%M"))
        
        st.markdown("---")
        
        # Download full transcript button
        col1, col2 = st.columns([3, 1])
        
        with col2:
            full_transcript = "\n\n".join([
                f"=== {ch.get('title', f'Chapter {i+1}')} ===\n{ch.get('original_text', '')}"
                for i, ch in enumerate(data["chapters"])
            ])
            
            st.download_button(
                label="📥 Download Full Transcript",
                data=full_transcript,
                file_name="podcast_transcript.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Display chapters
        st.subheader("📑 Chapters with Hybrid Summaries")
        
        for i, chapter in enumerate(data["chapters"]):
            with st.expander(f"Chapter {i+1}: {chapter.get('title', 'Untitled')} (Click to expand)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Title:** {chapter.get('title', 'N/A')}")
                    if "start_time" in chapter:
                        st.markdown(f"**Timestamp:** {chapter.get('start_time', 'N/A')}")
                
                with col2:
                    words_original = len(chapter.get("original_text", "").split())
                    words_summary = len(chapter.get("final_summary", "").split())
                    compression = (1 - words_summary/words_original) * 100 if words_original > 0 else 0
                    st.metric("Compression", f"{compression:.0f}%")
                
                st.markdown("---")
                
                st.markdown("#### 📌 Hybrid Summary (AI-Generated)")
                st.info(chapter.get("final_summary", "No summary available"))
                
                if st.checkbox(f"Show original text for Chapter {i+1}", key=f"show_orig_{i}"):
                    st.markdown("#### 📜 Original Transcript")
                    st.text_area(
                        "Original text:",
                        value=chapter.get("original_text", "N/A"),
                        height=200,
                        disabled=True,
                        key=f"orig_text_{i}"
                    )

# ============================================================
# VALIDATION CALLBACK FUNCTION
# ============================================================

def log_validation_response():
    """Callback to log human validation responses"""
    if hasattr(st.session_state, 'pending_validation') and st.session_state.pending_validation:
        validation_data = st.session_state.pending_validation
        is_correct = st.session_state.get('current_validation', None)
        
        if is_correct:
            if is_correct == "Yes ✅":
                validation_status = "HUMAN_VERIFIED"
            elif is_correct == "No ❌":
                validation_status = "HUMAN_CORRECTED"
            else:
                return
            
            audit_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": validation_data["query"],
                "answer": validation_data["answer"],
                "confidence": validation_data["confidence"],
                "source_chapter": validation_data["source_chapter"],
                "status": validation_status,
                "human_correction": ""
            }
            
            audit_log = load_audit_log()
            audit_log.append(audit_entry)
            save_audit_log(audit_log)
            
            st.session_state.pending_validation = None

# ============================================================
# TAB 3: Q&A CHAT
# ============================================================

with tab3:
    st.header("💬 Q&A Chat with Your Podcast")
    
    if not st.session_state.processing_complete:
        st.warning("⚠️ Please upload and process a podcast first (Upload tab)")
    else:
        st.markdown("""
        Ask any question about your podcast and get intelligent answers with confidence scores!
        """)
        
        # Query input
        query = st.text_input(
            "🔍 Ask a question about your podcast:",
            placeholder="e.g., What was the main topic discussed?",
            key="qa_query"
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submit_button = st.button("🚀 Search", use_container_width=True, type="primary")
        
        if submit_button and query:
            with st.spinner("🔍 Searching podcast..."):
                try:
                    rag_system = st.session_state.rag_system
                    
                    # Get answer from RAG system
                    result = rag_system.answer_question(query)
                    
                    # Display results
                    if result["found"]:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            confidence = result["confidence"]
                            
                            # Color-code confidence
                            if confidence >= 80:
                                col1.metric("Confidence", f"{confidence:.1f}%", delta="High", delta_color="off")
                                confidence_color = "🟢"
                            elif confidence >= 60:
                                col1.metric("Confidence", f"{confidence:.1f}%", delta="Medium", delta_color="off")
                                confidence_color = "🟡"
                            else:
                                col1.metric("Confidence", f"{confidence:.1f}%", delta="Low", delta_color="off")
                                confidence_color = "🔴"
                        
                        with col2:
                            st.metric("📖 Source", result["source_chapter"])
                        
                        with col3:
                            st.metric("Chapter #", result["chapter_id"])
                        
                        st.markdown("---")
                        
                        # Store current result in session state
                        st.session_state.last_query_result = {
                            "query": query,
                            "answer": result["answer"],
                            "confidence": confidence,
                            "source_chapter": result["source_chapter"]
                        }
                        
                        # Store query info for validation callback
                        st.session_state.pending_validation = {
                            "query": query,
                            "answer": result["answer"],
                            "confidence": f"{confidence:.1f}%",
                            "source_chapter": result["source_chapter"]
                        }
                        
                        # Handle low confidence with human validation
                        if confidence < 60:
                            st.warning(f"{confidence_color} Low Confidence Answer ({confidence:.1f}%) - Human Validation Required")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                is_correct = st.radio(
                                    "Is this answer correct?",
                                    ["Yes ✅", "No ❌"],
                                    index=None,
                                    key="current_validation",
                                    on_change=log_validation_response
                                )
                            
                            if is_correct == "Yes ✅":
                                st.success("✅ Answer accepted and logged!")
                                validation_status = "HUMAN_VERIFIED"
                            elif is_correct == "No ❌":
                                st.error("❌ Answer rejected")
                                correct_answer = st.text_area(
                                    "Please provide the correct answer:",
                                    key=f"correct_answer_{query}"
                                )
                                if correct_answer:
                                    st.info("✓ Correction noted and logged!")
                                    validation_status = "HUMAN_CORRECTED"
                                    result["answer"] = correct_answer
                            else:
                                st.info("⏸️ Please select Yes or No to proceed")
                                validation_status = "PENDING"
                        else:
                            st.success(f"{confidence_color} High Confidence Answer - Auto Approved")
                            validation_status = "AUTO_APPROVED"
                        
                        st.markdown("---")
                        st.subheader("🤖 Answer")
                        st.info(result["answer"])
                        
                        # Log to audit
                        if validation_status != "PENDING":
                            audit_entry = {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "query": query,
                                "answer": result["answer"],
                                "confidence": f"{confidence:.1f}%",
                                "source_chapter": result["source_chapter"],
                                "status": validation_status,
                                "human_correction": result.get("human_correction", "")
                            }
                            
                            # Save to audit log
                            audit_log = load_audit_log()
                            audit_log.append(audit_entry)
                            save_audit_log(audit_log)
                    
                    else:
                        st.error("❌ I cannot answer this question based on the podcast content.")
                        st.info("💡 Try asking about topics that were discussed in the podcast.")
                        
                        # Log failed query
                        audit_entry = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "query": query,
                            "answer": "No answer found",
                            "confidence": "0%",
                            "source_chapter": "N/A",
                            "status": "NO_ANSWER_FOUND",
                            "human_correction": ""
                        }
                        audit_log = load_audit_log()
                        audit_log.append(audit_entry)
                        save_audit_log(audit_log)
                
                except Exception as e:
                    st.error(f"❌ Error processing query: {str(e)}")
        
        elif submit_button:
            st.warning("⚠️ Please enter a question first!")

# ============================================================
# TAB 4: QUERY HISTORY
# ============================================================

with tab4:
    st.header("📈 Query History & Validation Records")
    
    audit_log = load_audit_log()
    
    if not audit_log:
        st.info("No queries yet. Start by asking questions in the Q&A Chat tab!")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Queries", len(audit_log))
        
        with col2:
            auto_approved = sum(1 for log in audit_log if log.get("status") == "AUTO_APPROVED")
            st.metric("Auto Approved", auto_approved)
        
        with col3:
            human_verified = sum(1 for log in audit_log if log.get("status") == "HUMAN_VERIFIED")
            st.metric("Human Verified", human_verified)
        
        with col4:
            human_corrected = sum(1 for log in audit_log if log.get("status") == "HUMAN_CORRECTED")
            st.metric("Human Corrected", human_corrected)
        
        st.markdown("---")
        
        # Detailed table
        st.subheader("Detailed Query Records")
        
        # Convert to DataFrame
        if audit_log:
            df = pd.DataFrame(audit_log)
            
            # Normalize column names to lowercase
            df.columns = df.columns.str.lower()
            
            # Ensure timestamp column exists
            if "timestamp" not in df.columns:
                df["timestamp"] = pd.Timestamp.now()
            else:
                df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            
            df = df.sort_values("timestamp", ascending=False)
            
            # Color-code status column
            def status_color(status):
                colors = {
                    "AUTO_APPROVED": "✅",
                    "HUMAN_VERIFIED": "✅",
                    "HUMAN_CORRECTED": "⚠️",
                    "NO_ANSWER_FOUND": "❌",
                    "PENDING": "⏸️"
                }
                return colors.get(str(status), "❓")
            
            # Ensure status column exists
            if "status" not in df.columns:
                df["status"] = "UNKNOWN"
            
            df["status_display"] = df["status"].apply(lambda x: f"{status_color(x)} {x}")
            
            # Display table - only show available columns
            available_cols = []
            col_mapping = {}
            
            if "timestamp" in df.columns:
                available_cols.append("timestamp")
                col_mapping["timestamp"] = "Time"
            if "query" in df.columns:
                available_cols.append("query")
                col_mapping["query"] = "Question"
            if "confidence" in df.columns:
                available_cols.append("confidence")
                col_mapping["confidence"] = "Score"
            if "source_chapter" in df.columns:
                available_cols.append("source_chapter")
                col_mapping["source_chapter"] = "Chapter"
            
            available_cols.append("status_display")
            col_mapping["status_display"] = "Validation"
            
            st.dataframe(
                df[available_cols].rename(columns=col_mapping),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Export option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Query History (CSV)",
                data=csv,
                file_name="query_history.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("📭 No query history yet. Ask questions in the Q&A Chat tab to build history.")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>🎙️ <strong>Podcast Insights AI</strong> | Powered by Whisper + Transformers + ChromaDB</p>
    <p style='font-size: 0.8em; color: gray;'>Built with Streamlit | Open Source</p>
</div>
""", unsafe_allow_html=True)
