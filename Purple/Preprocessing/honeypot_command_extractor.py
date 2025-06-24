# %%
import json
import os
from Red.model import DataLogObject, LabledCommandObject
from sentence_transformers import SentenceTransformer, util

log_id = '00'  # Example log ID, can be changed as needed

def word_similarity(model, query, embeded_canidates):
    """
    Calculate the similarity of a word to a list of words using SentenceTransformer.
    Returns the most similar word from the list.
    """
    
    # Encode the input word and the list of words
    word_embedding = model.encode(query, convert_to_tensor=True)
    
    # Compute cosine similarities
    similarities = util.pytorch_cos_sim(word_embedding, embeded_canidates)[0]
    
    # Get the index of the most similar word
    most_similar_index = similarities.argmax().item()


    if similarities[most_similar_index].item() < 0.5:
        print(f"Warning: Low similarity ({similarities[most_similar_index].item()}) for '{query}'")
        return "Other"
    
    return most_similar_index

def extract_honeypot_commands(full_logs, session_id):
    """
    Extract commands from honeypot logs and associate them with MITRE ATT&CK tactics and techniques.
    This function processes the beelzebub_response entries to find actual commands executed on the honeypot.
    """
    
    labeled_commands = []

    # moved embeddings outside the loop to avoid recomputing them for each log entry
    avilable_mitre_tactics = [
        "Reconnaissance", "Resource Development", "Initial Access",
        "Execution", "Persistence", "Privilege Escalation", "Defense Evasion",
        "Credential Access", "Discovery", "Lateral Movement", "Collection",
        "Command and Control", "Exfiltration", "Impact"
    ]
    # for word embedding
    model = SentenceTransformer('all-MiniLM-L6-v2')
    canidates_embedded = model.encode(avilable_mitre_tactics, convert_to_tensor=True)

    
    for attack_session in full_logs:
        for log_entry in attack_session:
            # Handle both dict and object formats
            if isinstance(log_entry, dict):
                log_dict = log_entry
            else:
                log_dict = log_entry.__dict__
            
            # Skip entries without beelzebub responses
            if not log_dict.get('beelzebub_response'):
                continue
            
            llm_response = log_dict.get('llm_response', {})
            if not llm_response or not isinstance(llm_response, dict):
                continue
            llm_response_arguments = llm_response.get('arguments', {})
            if not llm_response_arguments or not isinstance(llm_response_arguments, dict):
                continue

            tactic = llm_response_arguments.get('tactic_used', None)
            tactic_index = word_similarity(model, tactic, canidates_embedded) if tactic else "Other"
            tactic = avilable_mitre_tactics[tactic_index] if isinstance(tactic_index, int) else "Other"

            technique = llm_response_arguments.get('technique_used', None)
            
            # Process each beelzebub response, Claud created this
            for response in log_dict['beelzebub_response']:
                if not isinstance(response, dict) or 'event' not in response:
                    continue
                
                event = response['event']
                
                # Extract different types of commands based on protocol
                command = None
                protocol = event.get('Protocol', '')
                
                if protocol == 'SSH':
                    # For SSH, look for actual commands in the Command field
                    # SSH login attempts are stored in Password field
                    ssh_command = event.get('Command', '').strip()
                    if ssh_command and ssh_command not in ['', '\r\n\r\n']:
                        command = ssh_command
                    # Also capture SSH login attempts as commands
                    elif event.get('User') and event.get('Password'):
                        # This is a login attempt
                        user = event.get('User')
                        password_info = event.get('Password', '')
                        command = f"ssh_login_attempt:{user}:{password_info}"
                
                elif protocol == 'HTTP':
                    # For HTTP, combine method and URI
                    method = event.get('HTTPMethod', '')
                    uri = event.get('RequestURI', '')
                    if method and uri:
                        command = f"{method} {uri}"
                    elif event.get('Command'):
                        command = event.get('Command', '').strip()
                
                elif protocol == 'TCP':
                    # For TCP, use the Command field
                    tcp_command = event.get('Command', '').strip()
                    if tcp_command:
                        command = tcp_command
                
                # If we found a command, create a labeled command object
                if command and command.strip():
                    # Clean up the command
                    command = command.replace('\r\n', '\\n').replace('\r', '\\r').replace('\n', '\\n')
                    
                    # Use default values if MITRE info is missing
                    if not tactic or not technique:
                        tactic = tactic or "Unknown"
                        technique = technique or "Unknown"
                    
                    
                    labeled_command = LabledCommandObject(
                        command=command,
                        tactic=tactic,
                        technique=technique
                    )
                    
                    # Add additional metadata
                    labeled_command.protocol = event.get('Protocol', '') 
                    labeled_command.timestamp = event.get('DateTime', '')
                    labeled_command.source_ip = event.get('SourceIp', '')
                    labeled_command.source_port = event.get('SourcePort', '')
                    labeled_command.description = event.get('Description', '')
                    labeled_command.user = event.get('User', '')
                    labeled_command.event_id = event.get('ID', '')

                command = event.get('Command', '').strip()
                command = command.replace('\r\n', '\\n').replace('\r', '\\r').replace('\n', '\\n')                    
                labeled_command.command = event.get('Command', '') # can be removed to put together full commands
                labeled_commands.append(labeled_command)
    
    return labeled_commands


def save_honeypot_labels(labeled_commands, session_id):
    """
    Save the labeled commands to a JSON file.
    """
    if not os.path.exists('logs/labels'):
        os.makedirs('logs/labels')
    
    # Convert to dict format for JSON serialization
    commands_data = []
    for cmd in labeled_commands:
        cmd_dict = cmd.to_dict()
        # Add the additional metadata if it exists
        if hasattr(cmd, 'protocol'):
            cmd_dict['protocol'] = cmd.protocol
        if hasattr(cmd, 'timestamp'):
            cmd_dict['timestamp'] = cmd.timestamp
        if hasattr(cmd, 'source_ip'):
            cmd_dict['source_ip'] = cmd.source_ip
        if hasattr(cmd, 'source_port'):
            cmd_dict['source_port'] = cmd.source_port
        if hasattr(cmd, 'description'):
            cmd_dict['description'] = cmd.description
        if hasattr(cmd, 'user'):
            cmd_dict['user'] = cmd.user
        if hasattr(cmd, 'event_id'):
            cmd_dict['event_id'] = cmd.event_id
        
        commands_data.append(cmd_dict)
    
    output_file = f'logs/labels/labels_{session_id}.json'
    
    with open(output_file, 'w') as f:
        json.dump(commands_data, f, indent=4)
    
    print(f"Honeypot labels saved to {output_file}")
    print(f"Total commands extracted: {len(labeled_commands)}")
    
    return output_file


def process_test_logs(log_id):
    """
    Process the test logs and create labeled commands.
    """
    try:
        with open(f'logs/full_logs/full_logs_{log_id}.json', 'r') as f:
            full_logs = json.load(f)
        
        # Extract commands
        labeled_commands = extract_honeypot_commands(full_logs, log_id)
        
        # Save to file
        output_file = save_honeypot_labels(labeled_commands, log_id)
        
        # Print summary
        print("\n=== COMMAND EXTRACTION SUMMARY ===")
        print(f"Total commands found: {len(labeled_commands)}")
        
        # Group by protocol
        protocols = {}
        tactics = {}
        for cmd in labeled_commands:
            protocol = getattr(cmd, 'protocol', 'Unknown')
            protocols[protocol] = protocols.get(protocol, 0) + 1
            tactics[cmd.tactic] = tactics.get(cmd.tactic, 0) + 1
        
        print("\nCommands by protocol:")
        for protocol, count in protocols.items():
            print(f"  {protocol}: {count}")
        
        print("\nCommands by tactic:")
        for tactic, count in tactics.items():
            print(f"  {tactic}: {count}")
        
        # Show some examples
        print(f"\nFirst 5 commands:")
        for i, cmd in enumerate(labeled_commands[:5]):
            print(f"  {i+1}. [{getattr(cmd, 'protocol', 'Unknown')}] {cmd.command[:100]}...")
            print(f"     Tactic: {cmd.tactic}, Technique: {cmd.technique}")
        
        return labeled_commands, output_file
        
    except FileNotFoundError:
        print(f"Error: logs/full_logs/full_logs_{log_id}.json not found")
        return [], None
    except Exception as e:
        print(f"Error processing logs: {e}")
        return [], None


if __name__ == "__main__":
    process_test_logs(log_id)

# %%
