"""
RAG (Retrieval-Augmented Generation) System
Handles Q&A with confidence scoring and validation
"""

import chromadb
from transformers import pipeline
import re
import numpy as np

class RAGSystem:
    """RAG system for Q&A with confidence scoring"""
    
    def __init__(self, db_path="./podcast_knowledge_base", model_name="google/flan-t5-base"):
        self.db_path = db_path
        self.model_name = model_name
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = None
        
        # Load QA model
        self.qa_pipeline = pipeline("text2text-generation", model=model_name)
        
        # Security patterns
        self.injection_patterns = [
            r"ignore previous instructions",
            r"system override",
            r"delete all data",
            r"you are not"
        ]
    
    def index_documents(self, summaries_data):
        """Index documents in vector database"""
        # Create fresh collection (no deletion attempt to avoid schema issues)
        collection_name = "podcast_segments"
        
        try:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                get_or_create=True
            )
        except Exception as e:
            print(f"⚠️ Collection creation issue: {e}, creating with fresh client...")
            # Reinitialize client and try again
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                get_or_create=True
            )
        
        # Index documents with minimal metadata
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(summaries_data):
            # Index the hybrid summary instead of raw text
            documents.append(item['final_summary'])
            # Use only simple string metadata to avoid schema issues
            metadatas.append({
                "idx": str(i),
                "title": str(item['title'])[:100]  # Limit string length
            })
            ids.append(f"segment_{i}")
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✓ Indexed {len(documents)} chapters")
        except Exception as e:
            print(f"⚠️ Error during indexing: {e}")
            # Last resort: add without metadata
            try:
                self.collection.add(
                    documents=documents,
                    ids=ids
                )
                print(f"✓ Indexed {len(documents)} chapters (without metadata)")
            except Exception as e2:
                print(f"❌ Critical error during indexing: {e2}")
                raise
        
    
    def answer_question(self, question, threshold=0.3):
        """
        Answer question with confidence scoring
        Returns: {found, answer, confidence, source_chapter, chapter_id}
        """
        # Security check
        is_safe, msg = self._check_safety(question)
        if not is_safe:
            return {
                "found": False,
                "answer": "❌ Invalid request detected",
                "confidence": 0,
                "source_chapter": "N/A",
                "chapter_id": "N/A"
            }
        
        # Retrieve relevant context
        if not self.collection:
            return {
                "found": False,
                "answer": "Database not initialized",
                "confidence": 0,
                "source_chapter": "N/A",
                "chapter_id": "N/A"
            }
        
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=1,
                include=["distances", "metadatas", "documents"]
            )
            
            if not results['documents'] or not results['documents'][0]:
                return {
                    "found": False,
                    "answer": "I cannot answer this question based on the podcast.",
                    "confidence": 0,
                    "source_chapter": "N/A",
                    "chapter_id": "N/A"
                }
            
            # Extract data
            distance = results['distances'][0][0]
            metadata = results['metadatas'][0][0] if results['metadatas'] and results['metadatas'][0] else {}
            document = results['documents'][0][0] if results['documents'] and results['documents'][0] else ""
            
            # Debug: print metadata
            print(f"DEBUG: Retrieved metadata: {metadata}")
            print(f"DEBUG: Document length: {len(document) if document else 0}")
            
            # Convert distance to confidence (0 = perfect match, 1 = no match)
            confidence = max(0, (1.0 - distance) * 100)
            
            # Use document text and metadata title
            source_text = document[:300] if len(document) > 300 else document
            chapter_idx = metadata.get('idx', 'N/A')
            # Convert 0-based index to 1-based chapter number for display
            if chapter_idx != 'N/A':
                chapter_number = str(int(chapter_idx) + 1)
            else:
                chapter_number = 'N/A'
            chapter_title = metadata.get('title', f"Chapter {chapter_number}")
            chapter_id = chapter_number
            
            # Generate answer
            safe_prompt = self._format_safe_prompt(question, source_text)
            
            full_response = self.qa_pipeline(
                safe_prompt,
                max_new_tokens=200,
                do_sample=False
            )[0]['generated_text']
            
            # Extract just the answer part (after "Answer:")
            if "Answer:" in full_response:
                answer = full_response.split("Answer:")[-1].strip()
            else:
                answer = full_response.strip()
            
            # Clean up answer
            answer = answer.strip()
            if not answer:
                answer = "Unable to generate answer"
            
            # Check if model refused - be more lenient
            refusal_phrases = ["i cannot answer", "i cannot provide", "i don't have", "no information"]
            is_refusal = any(phrase in answer.lower() for phrase in refusal_phrases)
            
            # If confidence is low but we got an answer, still return it
            # Only reject if model explicitly refused
            if is_refusal and confidence < 30:
                return {
                    "found": False,
                    "answer": "I cannot answer this question based on the podcast content.",
                    "confidence": confidence,
                    "source_chapter": chapter_title,
                    "chapter_id": chapter_id
                }
            
            # If confidence is reasonable, return the answer even if partial
            if confidence < 20:
                return {
                    "found": False,
                    "answer": "Could not find relevant information in the podcast for this question.",
                    "confidence": confidence,
                    "source_chapter": chapter_title,
                    "chapter_id": chapter_id
                }
            
            return {
                "found": True,
                "answer": answer,
                "confidence": confidence,
                "source_chapter": chapter_title,
                "chapter_id": chapter_id,
                "human_correction": ""
            }
        
        except Exception as e:
            return {
                "found": False,
                "answer": f"Error processing query: {str(e)}",
                "confidence": 0,
                "source_chapter": "N/A",
                "chapter_id": "N/A"
            }
    
    def _check_safety(self, query):
        """Check for prompt injection attempts"""
        query_lower = query.lower()
        for pattern in self.injection_patterns:
            if re.search(pattern, query_lower):
                return False, f"Injection pattern detected: {pattern}"
        return True, "Safe"
    
    def _format_safe_prompt(self, question, context):
        """Format a safe prompt with context"""
        return f"""Based on this podcast content:
{context}

Question: {question}
Answer:"""
