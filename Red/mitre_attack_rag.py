"""
MITRE ATT&CK RAG System

This module provides a comprehensive RAG system for validating LLM-generated 
MITRE ATT&CK tactic/technique labels against the official MITRE ATT&CK database.

Main functionality:
- Parse MITRE ATT&CK enterprise JSON data
- Create embeddings for tactics and techniques using transformer models
- Cache embeddings for efficient reuse
- Compare LLM reasoning with MITRE descriptions using semantic similarity
- Parse log files to extract LLM thinking processes and labels
- Validate LLM labels against MITRE knowledge base
- Generate detailed analysis reports with recommendations

"""

import json
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Tuple, Optional
import os
import pickle
from pathlib import Path
from dataclasses import dataclass


@dataclass
class MitreEntry:
    """Data class for MITRE ATT&CK entries (tactics or techniques)"""
    id: str
    name: str
    description: str
    type: str  # 'tactic' or 'technique'
    external_id: Optional[str] = None
    
class MitreAttackRAG:
    """RAG system for MITRE ATT&CK database comparison and validation"""
    
    def __init__(self, enterprise_attack_path: str = None):
        """Initialize the MITRE ATT&CK RAG system"""
        # Setup file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.rag_data_dir = os.path.join(script_dir, "RagData")
        self.enterprise_attack_path = enterprise_attack_path or os.path.join(self.rag_data_dir, "enterprise-attack.json")
        
        # Model configuration
        self.model_name = "BAAI/bge-m3"
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Setup paths
        Path(self.rag_data_dir).mkdir(parents=True, exist_ok=True)
        self._setup_embedding_paths()
        
        # Data storage
        self.tactics: List[MitreEntry] = []
        self.techniques: List[MitreEntry] = []
        self.tactic_embeddings: Optional[np.ndarray] = None
        self.technique_embeddings: Optional[np.ndarray] = None
        
        # Model components (initialized only when needed)
        self.tokenizer = None
        self.model = None
        
        # Early check and load embeddings (model initialized only if needed)
        self._smart_load_embeddings()
    
    def _setup_embedding_paths(self):
        """Setup file paths for cached embeddings"""
        self.tactic_embeddings_path = os.path.join(self.rag_data_dir, "enterprise_tactics_embeddings.pkl")
        self.technique_embeddings_path = os.path.join(self.rag_data_dir, "enterprise_techniques_embeddings.pkl")
        self.tactics_data_path = os.path.join(self.rag_data_dir, "enterprise_tactics_data.pkl")
        self.techniques_data_path = os.path.join(self.rag_data_dir, "enterprise_techniques_data.pkl")
    
    def _initialize_model(self):
        """Initialize the transformer model for embeddings (only when needed)"""
        if self.tokenizer is None or self.model is None:
            print(f"🔄 Initializing {self.model_name} on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
            print("✅ Model initialized successfully!")
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded before using it"""
        if self.tokenizer is None or self.model is None:
            self._initialize_model()
    
    def _average_pool(self, last_hidden_states, attention_mask):
        """Pool transformer output to single vector per document using average pooling"""
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
        return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
    
    def _create_embedding(self, texts: List[str], batch_size: int = 16) -> np.ndarray:
        """Create embeddings for a list of texts using batched processing"""
        if not texts:
            return np.array([])
        
        # Ensure model is loaded before creating embeddings
        self._ensure_model_loaded()
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        print(f"Creating embeddings for {len(texts)} texts in {total_batches} batches...")
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_dict = self.tokenizer(
                batch_texts, padding=True, truncation=True, 
                max_length=512, return_tensors='pt'
            )
            batch_dict = {k: v.to(self.device) for k, v in batch_dict.items()}
            
            with torch.no_grad():
                outputs = self.model(**batch_dict)
                embeddings = self._average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
                embeddings = F.normalize(embeddings, p=2, dim=1)
            
            all_embeddings.append(embeddings.cpu().numpy())
        
        result = np.vstack(all_embeddings) if all_embeddings else np.array([])
        print(f"Completed embedding creation: {result.shape}")
        return result
    
    def _load_mitre_data(self, max_tactics: int = None, max_techniques: int = None):
        """Parse MITRE ATT&CK enterprise JSON file to extract tactics and techniques"""
        print("Loading MITRE ATT&CK enterprise data...")
        
        with open(self.enterprise_attack_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tactic_count = technique_count = 0
        
        for obj in data.get('objects', []):
            if obj.get('type') == 'x-mitre-tactic' and (max_tactics is None or tactic_count < max_tactics):
                self._parse_entry(obj, 'tactic')
                tactic_count += 1
            elif obj.get('type') == 'attack-pattern' and (max_techniques is None or technique_count < max_techniques):
                self._parse_entry(obj, 'technique')
                technique_count += 1
            
            if max_tactics and max_techniques and tactic_count >= max_tactics and technique_count >= max_techniques:
                break
        
        print(f"Loaded {len(self.tactics)} tactics and {len(self.techniques)} techniques")
    
    def _parse_entry(self, obj: Dict, entry_type: str):
        """Parse a single MITRE entry (tactic or technique)"""
        external_id = self._extract_external_id(obj)
        entry = MitreEntry(
            id=obj['id'],
            name=obj['name'],
            description=obj['description'],
            type=entry_type,
            external_id=external_id
        )
        
        if entry_type == 'tactic':
            self.tactics.append(entry)
        else:
            self.techniques.append(entry)
    
    def _extract_external_id(self, obj: Dict) -> Optional[str]:
        """Extract external ID (e.g., TA0001, T1055) from MITRE object"""
        for ref in obj.get('external_references', []):
            if ref.get('source_name') == 'mitre-attack':
                return ref.get('external_id')
        return None
    
    def _create_embeddings(self):
        """Create embeddings for all loaded tactics and techniques"""
        print("Creating embeddings for MITRE ATT&CK data...")
        
        if self.tactics:
            print(f"Processing {len(self.tactics)} tactics...")
            tactic_texts = [f"{t.name}: {t.description}" for t in self.tactics]
            self.tactic_embeddings = self._create_embedding(tactic_texts)
        
        if self.techniques:
            print(f"Processing {len(self.techniques)} techniques...")
            technique_texts = [f"{t.name}: {t.description}" for t in self.techniques]
            self.technique_embeddings = self._create_embedding(technique_texts)
        
        print("Embedding creation completed!")
    
    def _similarity_search(self, query_text: str, embeddings: np.ndarray, 
                          entries: List[MitreEntry], top_k: int = 5) -> List[Tuple[MitreEntry, float]]:
        """Perform semantic similarity search using cosine similarity"""
        query_embedding = self._create_embedding([query_text])
        similarities = np.dot(embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(entries[idx], float(similarities[idx])) for idx in top_indices]
    
    def compare_llm_thinking_with_mitre(self, thinking_process: str, 
                                       llm_tactic: str, llm_technique: str, 
                                       top_k: int = 3) -> Dict:
        """Main RAG validation function: compare LLM reasoning with MITRE knowledge"""
        results = {
            'llm_labels': {'tactic': llm_tactic, 'technique': llm_technique},
            'thinking_process': thinking_process,
            'rag_analysis': {
                'similar_tactics': [],
                'similar_techniques': [],
                'tactic_validation': {'match_found': False, 'confidence': 0.0, 'recommended_tactic': None},
                'technique_validation': {'match_found': False, 'confidence': 0.0, 'recommended_technique': None}
            }
        }
        
        # Validate tactics
        if self.tactic_embeddings is not None and len(self.tactics) > 0:
            results['rag_analysis'] = self._validate_entries(
                thinking_process, llm_tactic, top_k, results['rag_analysis'], 
                self.tactic_embeddings, self.tactics, 'tactic'
            )
        
        # Validate techniques
        if self.technique_embeddings is not None and len(self.techniques) > 0:
            results['rag_analysis'] = self._validate_entries(
                thinking_process, llm_technique, top_k, results['rag_analysis'],
                self.technique_embeddings, self.techniques, 'technique'
            )
        
        return results
    
    def _validate_entries(self, thinking_process: str, llm_label: str, top_k: int, 
                         rag_analysis: Dict, embeddings: np.ndarray, entries: List[MitreEntry], 
                         entry_type: str) -> Dict:
        """Validate LLM label against MITRE entries using semantic similarity"""
        similar_entries = self._similarity_search(thinking_process, embeddings, entries, top_k)
        
        # Store similar entries with truncated descriptions
        key_similar = f'similar_{entry_type}s'
        key_validation = f'{entry_type}_validation'
        
        for entry, similarity in similar_entries:
            description = entry.description[:200] + "..." if len(entry.description) > 200 else entry.description
            rag_analysis[key_similar].append({
                'name': entry.name,
                'external_id': entry.external_id,
                'description': description,
                'similarity_score': similarity
            })
        
        # Validate LLM label
        if similar_entries:
            best_entry, best_similarity = similar_entries[0]
            rag_analysis[key_validation]['confidence'] = best_similarity
            rag_analysis[key_validation][f'recommended_{entry_type}'] = best_entry.name
            
            # Check fuzzy match
            for entry, _ in similar_entries:
                if self._fuzzy_match(llm_label, entry.name):
                    rag_analysis[key_validation]['match_found'] = True
                    break
        
        return rag_analysis
    
    def _fuzzy_match(self, llm_label: str, mitre_name: str) -> bool:
        """Perform fuzzy matching between LLM label and MITRE name"""
        llm_lower = llm_label.lower()
        mitre_lower = mitre_name.lower()
        return llm_lower in mitre_lower or mitre_lower in llm_lower
    
    # Smart cache management with early check
    def _smart_load_embeddings(self):
        """Smart loading: check cache first, only initialize model if needed"""
        if self._has_valid_cache():
            print("✅ Found valid cached embeddings - loading instantly (no model needed)!")
            self._load_from_cache()
        else:
            print("❌ No valid cache found")
            print("⚠️  Need to create embeddings - this will take several minutes...")
            print("🔄 Initializing model and processing MITRE data...")
            self._initialize_model()
            self._load_mitre_data()
            self._create_embeddings()
            self._save_to_cache()
    
    def _has_valid_cache(self) -> bool:
        """Check if valid cached embeddings exist"""
        required_files = [
            self.tactic_embeddings_path, self.technique_embeddings_path,
            self.tactics_data_path, self.techniques_data_path
        ]
        
        # Check if all cache files exist
        if not all(os.path.exists(f) for f in required_files):
            return False
        
        # Check if source file is newer than cache
        if os.path.exists(self.enterprise_attack_path):
            source_mtime = os.path.getmtime(self.enterprise_attack_path)
            cache_mtime = min(os.path.getmtime(f) for f in required_files)
            return source_mtime <= cache_mtime
        
        return True
    
    def _load_from_cache(self):
        """Load embeddings and data from cache files"""
        with open(self.tactics_data_path, 'rb') as f:
            self.tactics = pickle.load(f)
        with open(self.tactic_embeddings_path, 'rb') as f:
            self.tactic_embeddings = pickle.load(f)
        with open(self.techniques_data_path, 'rb') as f:
            self.techniques = pickle.load(f)
        with open(self.technique_embeddings_path, 'rb') as f:
            self.technique_embeddings = pickle.load(f)
        print(f"📊 Loaded: {len(self.tactics)} tactics, {len(self.techniques)} techniques")
    
    def _save_to_cache(self):
        """Save embeddings and data to cache files"""
        print("💾 Saving embeddings to cache...")
        with open(self.tactics_data_path, 'wb') as f:
            pickle.dump(self.tactics, f)
        with open(self.tactic_embeddings_path, 'wb') as f:
            pickle.dump(self.tactic_embeddings, f)
        with open(self.techniques_data_path, 'wb') as f:
            pickle.dump(self.techniques, f)
        with open(self.technique_embeddings_path, 'wb') as f:
            pickle.dump(self.technique_embeddings, f)
        print("✅ Cache saved successfully!")
    
    # Utility functions
    def create_test_embeddings(self, max_tactics: int = 5, max_techniques: int = 20):
        """Create embeddings with a small subset for testing"""
        print("🧪 Creating TEST embeddings (small subset)...")
        
        # Ensure model is loaded for test embedding creation
        self._ensure_model_loaded()
        
        # Clear existing data and create subset
        self.tactics = []
        self.techniques = []
        self._load_mitre_data(max_tactics, max_techniques)
        self._create_embeddings()
        print(f"✅ Test embeddings ready: {len(self.tactics)} tactics, {len(self.techniques)} techniques")
    
    def clear_enterprise_embeddings(self):
        """Clear all cached embedding files"""
        files = [self.tactic_embeddings_path, self.technique_embeddings_path, 
                self.tactics_data_path, self.techniques_data_path]
        removed_count = 0
        for f in files:
            if os.path.exists(f):
                os.remove(f)
                removed_count += 1
        print(f"🗑️  Cleared {removed_count} cache files" if removed_count else "No cache files found")
    
    def get_technique_by_id(self, external_id: str) -> Optional[MitreEntry]:
        """Get technique by external ID (e.g., T1055.011)"""
        return next((t for t in self.techniques if t.external_id == external_id), None)


# Convenience functions
def create_mitre_rag() -> MitreAttackRAG:
    """Create and return a MitreAttackRAG instance"""
    return MitreAttackRAG()


def parse_log_file_for_rag_analysis(log_file_path: str, session_index: int = 0) -> List[Dict]:
    """Parse log file to extract LLM thinking process and MITRE labels for RAG analysis"""
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        if not log_data or len(log_data) <= session_index:
            print(f"No data found for session index {session_index}")
            return []
        
        session_logs = log_data[session_index]
        rag_data = []
        
        for i in range(len(session_logs) - 1):
            current_iteration = session_logs[i]
            next_iteration = session_logs[i + 1]
            
            thinking_process = _extract_thinking_process(current_iteration)
            tactic, technique = _extract_mitre_labels(next_iteration)
            
            if thinking_process and tactic and technique:
                rag_data.append({
                    'iteration_pair': f"{i} -> {i+1}",
                    'thinking_process': thinking_process,
                    'llm_tactic': tactic,
                    'llm_technique': technique,
                    'source_iteration': i,
                    'target_iteration': i + 1
                })
        
        print(f"Extracted {len(rag_data)} valid entries for RAG analysis")
        return rag_data
        
    except Exception as e:
        print(f"Error parsing log file: {e}")
        return []


def _extract_thinking_process(iteration: Dict) -> Optional[str]:
    """Extract thinking process from an iteration's LLM response"""
    if (iteration.get('llm_response') and iteration['llm_response'].get('message')):
        return iteration['llm_response']['message']
    return None


def _extract_mitre_labels(iteration: Dict) -> Tuple[Optional[str], Optional[str]]:
    """Extract tactic and technique labels from an iteration's MITRE attack method"""
    mitre_method = iteration.get('mitre_attack_method', {})
    
    tactic = mitre_method.get('tactic_used')
    technique_raw = mitre_method.get('technique_used')
    
    # Clean up technique formatting
    technique = None
    if technique_raw:
        technique = technique_raw.split(':', 1)[1].strip() if ':' in technique_raw else technique_raw
    
    return tactic, technique

def analyze_log_session_with_rag(log_file_path: str, session_index: int = 0, 
                                rag_system: Optional['MitreAttackRAG'] = None) -> Dict:
    """Analyze a complete log session using RAG validation"""
    if rag_system is None:
        print("Initializing MITRE RAG system...")
        rag_system = MitreAttackRAG()
    
    rag_data = parse_log_file_for_rag_analysis(log_file_path, session_index)
    if not rag_data:
        return {'error': 'No valid data found for RAG analysis'}
    
    analysis_results = {
        'session_index': session_index,
        'total_entries': len(rag_data),
        'entries': [],
        'summary': {
            'tactic_matches': 0, 'technique_matches': 0,
            'high_confidence_tactics': 0, 'high_confidence_techniques': 0,
            'avg_tactic_confidence': 0.0, 'avg_technique_confidence': 0.0
        }
    }
    
    tactic_confidences = []
    technique_confidences = []
    
    print(f"Analyzing {len(rag_data)} entries with RAG...")
    
    for i, entry in enumerate(rag_data):
        rag_results = rag_system.compare_llm_thinking_with_mitre(
            entry['thinking_process'], entry['llm_tactic'], entry['llm_technique']
        )
        
        tactic_validation = rag_results['rag_analysis']['tactic_validation']
        technique_validation = rag_results['rag_analysis']['technique_validation']
        
        # Update statistics
        if tactic_validation['match_found']:
            analysis_results['summary']['tactic_matches'] += 1
        if technique_validation['match_found']:
            analysis_results['summary']['technique_matches'] += 1
        if tactic_validation['confidence'] > 0.8:
            analysis_results['summary']['high_confidence_tactics'] += 1
        if technique_validation['confidence'] > 0.8:
            analysis_results['summary']['high_confidence_techniques'] += 1
        
        tactic_confidences.append(tactic_validation['confidence'])
        technique_confidences.append(technique_validation['confidence'])
        
        analysis_results['entries'].append({
            'iteration_pair': entry['iteration_pair'],
            'llm_labels': {'tactic': entry['llm_tactic'], 'technique': entry['llm_technique']},
            'rag_validation': {
                'tactic_match': tactic_validation['match_found'],
                'tactic_confidence': tactic_validation['confidence'],
                'recommended_tactic': tactic_validation['recommended_tactic'],
                'technique_match': technique_validation['match_found'],
                'technique_confidence': technique_validation['confidence'],
                'recommended_technique': technique_validation['recommended_technique']
            }
        })
    
    # Calculate averages
    if tactic_confidences:
        analysis_results['summary']['avg_tactic_confidence'] = sum(tactic_confidences) / len(tactic_confidences)
    if technique_confidences:
        analysis_results['summary']['avg_technique_confidence'] = sum(technique_confidences) / len(technique_confidences)
    
    return analysis_results


def print_rag_analysis_summary(analysis_results: Dict):
    """Print a formatted summary of RAG analysis results"""
    if 'error' in analysis_results:
        print(f"Error: {analysis_results['error']}")
        return
    
    summary = analysis_results['summary']
    total = analysis_results['total_entries']
    
    print(f"\n{'='*60}")
    print(f"RAG ANALYSIS SUMMARY - Session {analysis_results['session_index']}")
    print(f"{'='*60}")
    print(f"Total entries: {total}")
    print(f"Tactic matches: {summary['tactic_matches']}/{total} ({summary['tactic_matches']/total*100:.1f}%)")
    print(f"Technique matches: {summary['technique_matches']}/{total} ({summary['technique_matches']/total*100:.1f}%)")
    print(f"High confidence tactics (>0.8): {summary['high_confidence_tactics']}/{total}")
    print(f"High confidence techniques (>0.8): {summary['high_confidence_techniques']}/{total}")
    print(f"Average tactic confidence: {summary['avg_tactic_confidence']:.3f}")
    print(f"Average technique confidence: {summary['avg_technique_confidence']:.3f}")
    
    print(f"\nDETAILED RESULTS:")
    for entry in analysis_results['entries']:
        rag = entry['rag_validation']
        tactic_status = "✅" if rag['tactic_match'] else "❌"
        technique_status = "✅" if rag['technique_match'] else "❌"
        
        print(f"\nIteration {entry['iteration_pair']}:")
        print(f"  LLM: {entry['llm_labels']['tactic']} / {entry['llm_labels']['technique']}")
        print(f"  Tactic {tactic_status}: {rag['tactic_confidence']:.3f}")
        print(f"  Technique {technique_status}: {rag['technique_confidence']:.3f}")
        if not rag['tactic_match'] and rag['recommended_tactic']:
            print(f"    RAG suggests tactic: {rag['recommended_tactic']}")
        if not rag['technique_match'] and rag['recommended_technique']:
            print(f"    RAG suggests technique: {rag['recommended_technique']}")


def analyze_session_and_save(session_id: int, log_file_name: str = "attack_1.json") -> str:
    """Main function to analyze a specific session and save results"""
    print(f"=== MITRE ATT&CK RAG Analysis for Session {session_id} ===\n")
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    log_file_path = os.path.join(project_root, "logs", "full_logs", "2025-06-24T13:37:01","hp_config_1", log_file_name)
    analysis_dir = os.path.join(project_root, "logs", "label_analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Validate inputs
    if not os.path.exists(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")
    
    with open(log_file_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    if session_id >= len(log_data):
        raise ValueError(f"Session {session_id} not found. Available: 0-{len(log_data)-1}")
    
    print(f"Analyzing session {session_id} from {log_file_name}")
    
    # Initialize and run analysis
    rag = create_mitre_rag()
    rag_data = parse_log_file_for_rag_analysis(log_file_path, session_id)
    
    if not rag_data:
        print("No valid data found")
        return None
    
    # Track statistics
    analysis_results = {
        "session_id": session_id,
        "log_file": log_file_name,
        "analysis_timestamp": os.popen('date').read().strip(),
        "total_entries": len(rag_data),
        "entries": [],
        "summary": {}
    }
    
    tactic_matches = technique_matches = 0
    tactic_confidences = technique_confidences = []
    
    # Process each entry
    for i, entry in enumerate(rag_data):
        rag_results = rag.compare_llm_thinking_with_mitre(
            entry['thinking_process'], entry['llm_tactic'], entry['llm_technique']
        )
        
        tactic_val = rag_results['rag_analysis']['tactic_validation']
        technique_val = rag_results['rag_analysis']['technique_validation']
        
        if tactic_val['match_found']:
            tactic_matches += 1
        if technique_val['match_found']:
            technique_matches += 1
        
        tactic_confidences.append(tactic_val['confidence'])
        technique_confidences.append(technique_val['confidence'])
        
        analysis_results["entries"].append({
            "entry_index": i,
            "iteration_pair": entry['iteration_pair'],
            "llm_tactic": entry['llm_tactic'],
            "llm_technique": entry['llm_technique'],
            "thinking_process": entry['thinking_process'],
            "tactic_validation": tactic_val,
            "technique_validation": technique_val,
            "tactic_match": tactic_val['match_found'],
            "technique_match": technique_val['match_found']
        })
    
    # Calculate summary
    total_entries = len(rag_data)
    analysis_results["summary"] = {
        "total_entries": total_entries,
        "tactic_matches": tactic_matches,
        "technique_matches": technique_matches,
        "tactic_match_rate": tactic_matches / total_entries if total_entries > 0 else 0,
        "technique_match_rate": technique_matches / total_entries if total_entries > 0 else 0,
        "average_tactic_confidence": sum(tactic_confidences) / len(tactic_confidences) if tactic_confidences else 0,
        "average_technique_confidence": sum(technique_confidences) / len(technique_confidences) if technique_confidences else 0
    }
    
    # Print and save results
    print(f"\nSUMMARY:")
    print(f"  Entries: {total_entries}")
    print(f"  Tactic matches: {tactic_matches}/{total_entries} ({tactic_matches/total_entries*100:.1f}%)")
    print(f"  Technique matches: {technique_matches}/{total_entries} ({technique_matches/total_entries*100:.1f}%)")
    
    results_path = os.path.join(analysis_dir, f"rag_analysis_session_{session_id}.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved to: {results_path}")
    return results_path

# Example usage
if __name__ == "__main__":
    try:
        analyze_session_and_save(session_id=0)
    except Exception as e:
        print(f"Error: {e}")
