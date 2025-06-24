from enum import Enum

class LLMHost(str, Enum):
    """Enumeration of supported LLM hosts. API keys must be in the .env file or ollama must be running."""
    OPENAI = "openai"
    # ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OLLAMA_NO_FC = "ollama_no_fc"

class LLMModel(str, Enum):
    """Enumeration LLM models."""
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1 = "gpt-4.1"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_1_MINI = "gpt-4.1-mini"
    O4_MINI = "o4-mini"
    OLLAMA_LLAMA32_3b = "llama3.2:3b"
    OLLAMA_DEEPSEEK_R1_1b = "deepseek-r1:1.5b"

class LLMConfig:
    """Configuration for the LLM host and model."""
    def __init__(self, host: LLMHost, model: LLMModel):
        self.host = host
        self.model = model

class ResponseObject:
    """Object to hold the response from the LLM."""
    def __init__(self, message: str, function: str = None, arguments: dict = None):
        self.message = message
        self.function = function
        self.arguments = arguments
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cached_tokens = 0

    def __repr__(self):
        return f"ResponseObject(message={self.message}, function={self.function}, arguments={self.arguments})"
    
    def to_dict(self):
        return {
            'message': self.message,
            'function': self.function,
            'arguments': self.arguments
        }

class MitreMethodUsed():
    """Object to hold the MITRE ATT&CK method used in the attack."""
    def __init__(self):
        self.tactic_used = None
        self.technique_used = None

    def __repr__(self):
        return f"MethodUsed(tactic={self.tactic_used}, technique={self.technique_used})"
    
    def to_dict(self):
        return {
            'tactic_used': self.tactic_used,
            'technique_used': self.technique_used
        }

class DataLogObject():
    """Object to hold the data log for each iteration of the attack."""
    def __init__(self, iteration):
        self.iteration = iteration
        self.attack_success = False
        self.llm_response = None
        self.tool_response = None
        self.mitre_attack_method = MitreMethodUsed()
        self.beelzebub_response = []
    
    def to_dict(self):
        return {
            'iteration': self.iteration,
            'llm_response': self.llm_response.to_dict() if self.llm_response else None,
            'tool_response': self.tool_response,
            'mitre_attack_method': self.mitre_attack_method.to_dict() if self.mitre_attack_method else None,
            'beelzebub_response': self.beelzebub_response
        }


class LabledCommandObject():
    """Object to hold a command with its associated MITRE ATT&CK tactic and technique."""
    def __init__(self, command: str, tactic: str, technique: str, protocol: str = None, 
                 source_ip: str = None, source_port: str = None, description: str = None,
                 http_method: str = None, request_uri: str = None, datetime: str = None,
                 event_id: str = None):
        self.command = command
        self.tactic = tactic
        self.technique = technique
        self.protocol = protocol
        self.source_ip = source_ip
        self.source_port = source_port
        self.description = description
        self.http_method = http_method
        self.request_uri = request_uri
        self.datetime = datetime
        self.event_id = event_id

    def to_dict(self):
        return {
            'command': self.command,
            'tactic': self.tactic,
            'technique': self.technique,
            'protocol': self.protocol,
            'source_ip': self.source_ip,
            'source_port': self.source_port,
            'description': self.description,
            'http_method': self.http_method,
            'request_uri': self.request_uri,
            'datetime': self.datetime,
            'event_id': self.event_id
        }
    