"""
MITRE ATT&CK RAG System - Simplified Version

Validates LLM-generated MITRE ATT&CK labels against the official database using semantic similarity.
Main function: analyze_session_and_save(session_id) - analyzes a session and saves results.
"""

import json
import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Optional
import os
import pickle
from dataclasses import dataclass


@dataclass
class MitreEntry:
    """MITRE ATT&CK entry (tactic or technique)"""
    id: str
    name: str
    description: str
    type: str  # 'tactic' or 'technique'
    external_id: Optional[str] = None


class MitreAttackRAG:
    """RAG system for MITRE ATT&CK validation"""
    
    def __init__(self):
        # Setup paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.rag_data_dir = os.path.join(script_dir, "RagData")
        self.enterprise_attack_path = os.path.join(self.rag_data_dir, "enterprise-attack.json")
        
        # Model setup
        self.model_name = "BAAI/bge-m3"
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Initialize
        os.makedirs(self.rag_data_dir, exist_ok=True)
        self._init_model()
        self.tactics: List[MitreEntry] = []
        self.techniques: List[MitreEntry] = []
        self.tactic_embeddings: Optional[np.ndarray] = None
        self.technique_embeddings: Optional[np.ndarray] = None
        
        # Load or create embeddings
        self._load_or_create_embeddings()
    
    def _init_model(self):
        """Initialize transformer model"""
        print(f"Loading {self.model_name}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.model.eval()
    
    def _create_embedding(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for texts"""
        if not texts:
            return np.array([])
        
        # Tokenize and embed
        inputs = self.tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Average pooling
            embeddings = outputs.last_hidden_state.masked_fill(~inputs['attention_mask'][..., None].bool(), 0.0)
            embeddings = embeddings.sum(dim=1) / inputs['attention_mask'].sum(dim=1)[..., None]
            embeddings = F.normalize(embeddings, p=2, dim=1)
        
        return embeddings.cpu().numpy()
    
    def _load_mitre_data(self):
        """Load MITRE ATT&CK data"""
        print("Loading MITRE data...")
        with open(self.enterprise_attack_path, 'r') as f:
            data = json.load(f)
        
        for obj in data.get('objects', []):
            # Skip objects without required fields
            if not obj.get('name') or not obj.get('description'):
                continue
                
            external_id = None
            for ref in obj.get('external_references', []):
                if ref.get('source_name') == 'mitre-attack':
                    external_id = ref.get('external_id')
                    break
            
            entry = MitreEntry(
                id=obj.get('id', ''),
                name=obj['name'], 
                description=obj['description'],
                type='tactic' if obj.get('type') == 'x-mitre-tactic' else 'technique',
                external_id=external_id
            )
            
            if obj.get('type') == 'x-mitre-tactic':
                self.tactics.append(entry)
            elif obj.get('type') == 'attack-pattern':
                self.techniques.append(entry)
        
        print(f"Loaded {len(self.tactics)} tactics, {len(self.techniques)} techniques")
    
    def _create_all_embeddings(self):
        """Create embeddings for all MITRE data"""
        print("Creating embeddings...")
        
        if self.tactics:
            tactic_texts = [f"{t.name}: {t.description}" for t in self.tactics]
            self.tactic_embeddings = self._create_embedding(tactic_texts)
        
        if self.techniques:
            technique_texts = [f"{t.name}: {t.description}" for t in self.techniques]
            self.technique_embeddings = self._create_embedding(technique_texts)
    
    def _load_or_create_embeddings(self):
        """Load cached embeddings or create new ones"""
        cache_files = [
            os.path.join(self.rag_data_dir, "tactics.pkl"),
            os.path.join(self.rag_data_dir, "techniques.pkl"),
            os.path.join(self.rag_data_dir, "tactic_embeddings.pkl"),
            os.path.join(self.rag_data_dir, "technique_embeddings.pkl")
        ]
        
        if all(os.path.exists(f) for f in cache_files):
            print("Loading cached embeddings...")
            with open(cache_files[0], 'rb') as f:
                self.tactics = pickle.load(f)
            with open(cache_files[1], 'rb') as f:
                self.techniques = pickle.load(f)
            with open(cache_files[2], 'rb') as f:
                self.tactic_embeddings = pickle.load(f)
            with open(cache_files[3], 'rb') as f:
                self.technique_embeddings = pickle.load(f)
            print(f"Loaded {len(self.tactics)} tactics, {len(self.techniques)} techniques")
        else:
            print("Creating new embeddings...")
            self._load_mitre_data()
            self._create_all_embeddings()
            
            # Save cache
            with open(cache_files[0], 'wb') as f:
                pickle.dump(self.tactics, f)
            with open(cache_files[1], 'wb') as f:
                pickle.dump(self.techniques, f)
            with open(cache_files[2], 'wb') as f:
                pickle.dump(self.tactic_embeddings, f)
            with open(cache_files[3], 'wb') as f:
                pickle.dump(self.technique_embeddings, f)
            print("Embeddings cached")
    
    def validate_labels(self, thinking_process: str, llm_tactic: str, llm_technique: str) -> Dict:
        """Main validation function - compare LLM labels with MITRE knowledge"""
        results = {
            'tactic_validation': {'match_found': False, 'confidence': 0.0, 'recommended': None},
            'technique_validation': {'match_found': False, 'confidence': 0.0, 'recommended': None}
        }
        
        # Validate tactic
        if self.tactic_embeddings is not None and len(self.tactics) > 0:
            query_emb = self._create_embedding([thinking_process])
            similarities = np.dot(self.tactic_embeddings, query_emb.T).flatten()
            best_idx = np.argmax(similarities)
            best_tactic = self.tactics[best_idx]
            
            results['tactic_validation']['confidence'] = float(similarities[best_idx])
            results['tactic_validation']['recommended'] = best_tactic.name
            
            # Check if LLM tactic matches (fuzzy)
            if (llm_tactic.lower() in best_tactic.name.lower() or 
                best_tactic.name.lower() in llm_tactic.lower()):
                results['tactic_validation']['match_found'] = True
        
        # Validate technique  
        if self.technique_embeddings is not None and len(self.techniques) > 0:
            query_emb = self._create_embedding([thinking_process])
            similarities = np.dot(self.technique_embeddings, query_emb.T).flatten()
            best_idx = np.argmax(similarities)
            best_technique = self.techniques[best_idx]
            
            results['technique_validation']['confidence'] = float(similarities[best_idx])
            results['technique_validation']['recommended'] = best_technique.name
            
            # Check if LLM technique matches (fuzzy)
            if (llm_technique.lower() in best_technique.name.lower() or 
                best_technique.name.lower() in llm_technique.lower()):
                results['technique_validation']['match_found'] = True
        
        return results


def parse_log_file(log_file_path: str, session_index: int = 0) -> List[Dict]:
    """Extract LLM thinking process and MITRE labels from log file"""
    try:
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)
        
        if session_index >= len(log_data):
            return []
        
        session_logs = log_data[session_index]
        entries = []
        
        for i in range(len(session_logs) - 1):
            current = session_logs[i]
            next_iter = session_logs[i + 1]
            
            # Extract thinking process
            thinking = None
            if current.get('llm_response', {}).get('message'):
                thinking = current['llm_response']['message']
            
            # Extract MITRE labels
            tactic = None
            technique = None
            mitre_method = next_iter.get('mitre_attack_method', {})
            
            if mitre_method.get('tactic_used'):
                tactic = mitre_method['tactic_used']
            
            if mitre_method.get('technique_used'):
                technique_raw = mitre_method['technique_used']
                if ':' in technique_raw:
                    technique = technique_raw.split(':', 1)[1].strip()
                else:
                    technique = technique_raw
            
            if thinking and tactic and technique:
                entries.append({
                    'iteration_pair': f"{i}->{i+1}",
                    'thinking_process': thinking,
                    'llm_tactic': tactic,
                    'llm_technique': technique
                })
        
        return entries
    except Exception as e:
        print(f"Error parsing log: {e}")
        return []


def analyze_session_and_save(session_id: int, log_file_name: str = "attack_1.json") -> str:
    """
    Main function: Analyze a session and save results to logs/label_analysis/
    
    Args:
        session_id: Session index to analyze (0-based)
        log_file_name: Log file name in logs/full_logs/
        
    Returns:
        Path to saved analysis file
    """
    print(f"=== MITRE RAG Analysis - Session {session_id} ===")
    
    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    log_file_path = os.path.join(project_root, "logs", "full_logs", "2025-06-24T13:37:01","hp_config_1", log_file_name)
    analysis_dir = os.path.join(project_root, "logs", "label_analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Validate inputs
    if not os.path.exists(log_file_path):
        raise FileNotFoundError(f"Log file not found: {log_file_path}")
    
    with open(log_file_path, 'r') as f:
        log_data = json.load(f)
    
    if session_id >= len(log_data):
        raise ValueError(f"Session {session_id} not found. Available: 0-{len(log_data)-1}")
    
    print(f"Found {len(log_data)} sessions in {log_file_name}")
    
    # Initialize RAG system and parse log
    rag = MitreAttackRAG()
    entries = parse_log_file(log_file_path, session_id)
    
    if not entries:
        print("No valid entries found")
        return None
    
    print(f"Analyzing {len(entries)} entries...")
    
    # Analyze each entry
    results = []
    tactic_matches = 0
    technique_matches = 0
    tactic_confidences = []
    technique_confidences = []
    
    for i, entry in enumerate(entries):
        print(f"  {i+1}/{len(entries)}: {entry['iteration_pair']}")
        
        validation = rag.validate_labels(
            entry['thinking_process'],
            entry['llm_tactic'],
            entry['llm_technique']
        )
        
        # Track stats
        if validation['tactic_validation']['match_found']:
            tactic_matches += 1
        if validation['technique_validation']['match_found']:
            technique_matches += 1
        
        tactic_confidences.append(validation['tactic_validation']['confidence'])
        technique_confidences.append(validation['technique_validation']['confidence'])
        
        # Store result
        results.append({
            'iteration_pair': entry['iteration_pair'],
            'llm_tactic': entry['llm_tactic'],
            'llm_technique': entry['llm_technique'],
            'tactic_match': validation['tactic_validation']['match_found'],
            'tactic_confidence': validation['tactic_validation']['confidence'],
            'tactic_recommended': validation['tactic_validation']['recommended'],
            'technique_match': validation['technique_validation']['match_found'],
            'technique_confidence': validation['technique_validation']['confidence'],
            'technique_recommended': validation['technique_validation']['recommended']
        })
        
        # Show progress
        t_status = "✅" if validation['tactic_validation']['match_found'] else "❌"
        tech_status = "✅" if validation['technique_validation']['match_found'] else "❌"
        print(f"    {t_status} Tactic: {entry['llm_tactic']} ({validation['tactic_validation']['confidence']:.3f})")
        print(f"    {tech_status} Technique: {entry['llm_technique']} ({validation['technique_validation']['confidence']:.3f})")
    
    # Summary stats
    total = len(entries)
    avg_tactic_conf = sum(tactic_confidences) / total if total > 0 else 0
    avg_technique_conf = sum(technique_confidences) / total if total > 0 else 0
    
    summary = {
        'session_id': session_id,
        'total_entries': total,
        'tactic_matches': tactic_matches,
        'technique_matches': technique_matches,
        'tactic_match_rate': tactic_matches / total if total > 0 else 0,
        'technique_match_rate': technique_matches / total if total > 0 else 0,
        'avg_tactic_confidence': avg_tactic_conf,
        'avg_technique_confidence': avg_technique_conf,
        'entries': results
    }
    
    # Print summary
    print(f"\n SUMMARY:")
    print(f"   Entries: {total}")
    print(f"   Tactic matches: {tactic_matches}/{total} ({tactic_matches/total*100:.1f}%)")
    print(f"   Technique matches: {technique_matches}/{total} ({technique_matches/total*100:.1f}%)")
    print(f"   Avg tactic confidence: {avg_tactic_conf:.3f}")
    print(f"   Avg technique confidence: {avg_technique_conf:.3f}")
    
    # Save results
    output_file = f"rag_analysis_session_{session_id}.json"
    output_path = os.path.join(analysis_dir, output_file)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n Results saved: {output_path}")
    return output_path


if __name__ == "__main__":
    # Analyze session 0
    try:
        analyze_session_and_save(session_id=0)
    except Exception as e:
        print(f" Error: {e}")
