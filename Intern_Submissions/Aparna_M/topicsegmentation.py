from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class TopicSegmenter:
    def __init__(self, group_size=3, threshold=0.6): 
        self.group_size = group_size
        self.threshold = threshold
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')

    def segment(self, sentences, sentence_times):
        
        chunks = [" ".join(sentences[i:i+self.group_size]) for i in range(0, len(sentences), self.group_size)]
        chunk_start_times = [sentence_times[i] for i in range(0, len(sentence_times), self.group_size)]
        
        if len(chunks) < 2:
            return [chunks], [chunk_start_times[0]]

        embeddings = self.embed_model.encode(chunks)
        similarities = [cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0] for i in range(len(embeddings)-1)]

        segments, segment_times, start = [], [], 0
        
        
        min_chunks = 3 

        for i, sim in enumerate(similarities):
            
            if sim < self.threshold and (i + 1 - start) >= min_chunks:
                segments.append(chunks[start:i+1])
                segment_times.append(chunk_start_times[start])
                start = i+1
        
       
        if start < len(chunks):
            segments.append(chunks[start:])
            segment_times.append(chunk_start_times[start])
            
        return segments, segment_times