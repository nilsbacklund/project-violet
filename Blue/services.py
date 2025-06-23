from typing import Tuple, List, Optional
from abc import ABC

# All this file does is specify the structure of the Beelzebub service configuration files
# These are run through ChatGPT to generate a JSON schema that can validate newly generated config files

class LLMPlugin:
    """
    Represents a configuration for integrating a large language model (LLM) into honeypot services.

    Attributes:
        llmProvider (str): The LLM provider name (e.g., 'openai').
        llmModel (str): The specific model to use (e.g., 'gpt-4o-mini').
        openAISecretKey (str): API key for authentication with the LLM provider.
        prompt (str): Base prompt to initialize the LLM conversation.
    """
    llmProvider: str = "openai"
    llmModel: str = "gpt-4o-mini"
    openAISecretKey: str = "placeholder"
    prompt: str

    def __init__(self, prompt: str):
        """Initialize the LLM plugin with a custom prompt."""
        self.prompt = prompt


class CommandHTTP:
    """
    Defines a rule for handling incoming HTTP requests in the honeypot.

    Attributes:
        regex (str): A regular expression to match request paths or payloads.
        handler (str): The response body or handler name for matched requests.
        headers (Tuple[str, ...]): A tuple of HTTP header strings to include in the response.
        statusCode (int): HTTP status code to return (e.g., 200, 404, 401).
    """
    regex: str
    handler: str
    headers: Tuple[str, ...]
    statusCode: int

    def __init__(
        self,
        regex: str,
        handler: str,
        headers: Tuple[str, ...],
        statusCode: int
    ):
        """Initialize an HTTP command with matching and response details."""
        self.regex = regex
        self.handler = handler
        self.headers = headers
        self.statusCode = statusCode


class CommandSSH:
    """
    Defines a rule for handling SSH commands in the honeypot.

    Attributes:
        regex (str): A regular expression to match an incoming SSH command.
        handler (str): The text or action to respond with when the regex matches.
        plugin (Optional[str]): Optional name of a plugin (e.g., 'LLMHoneypot') to process the command.
    """
    regex: str
    handler: str
    plugin: Optional[str]

    def __init__(
        self,
        regex: str,
        handler: str,
        plugin: Optional[str]
    ):
        """Initialize an SSH command with matching, response, and optional plugin."""
        self.regex = regex
        self.handler = handler
        self.plugin = plugin

class Service(ABC):
    """
    Abstract base class for all honeypot services.

    Attributes:
        apiVersion (str): API version of the configuration schema. Defaults to 'v1'.
        protocol (str): Communication protocol ('http', 'ssh', or 'tcp').
        address (str): Network address and port to listen on (e.g., ':80', ':22').
        description (str): Human-readable description of the service.
        cve_tags (List[str]): List of CVE identifiers relevant to explots that target this service.
        cve_description (str): A description of the vulnerabilities that are exploited in this service.
    """
    apiVersion: str = "v1"
    protocol: str
    address: str
    description: str
    cve_tags: List[str]
    cve_description: str

class ServiceHTTP(Service):
    """
    Configuration for an HTTP honeypot service.

    Attributes:
        protocol (str): Always 'http' for HTTP services.
        commands (List[CommandHTTP]): List of HTTP command rules.
        plugin (Optional[LLMPlugin]): Optional LLM plugin for dynamic responses.
    """
    protocol: str = "http"
    commands: List[CommandHTTP]
    plugin: Optional[LLMPlugin]

    def __init__(
        self,
        address: str,
        description: str,
        commands: List[CommandHTTP],
        plugin: Optional[LLMPlugin]
    ):
        """Initialize the HTTP service with its address, description, commands, and optional plugin."""
        self.address = address
        self.description = description
        self.commands = commands
        self.plugin = plugin


class ServiceSSH(Service):
    """
    Configuration for an SSH honeypot service.

    Attributes:
        protocol (str): Always 'ssh' for SSH services.
        commands (List[CommandSSH]): List of SSH command rules.
        passwordRegex (str): Regex for accepted or logged passwords.
        deadlineTimeoutSeconds (int): Timeout in seconds before session terminates.
        serverName (str): Fake server name reported to clients (e.g., 'ubuntu').
        plugin (Optional[LLMPlugin]): Optional LLM plugin for dynamic SSH interaction.
    """
    protocol: str = "ssh"
    commands: List[CommandSSH]
    passwordRegex: str
    deadlineTimeoutSeconds: int
    serverName: str
    plugin: Optional[LLMPlugin]

    def __init__(
        self,
        address: str,
        description: str,
        commands: List[CommandSSH],
        passwordRegex: str,
        deadlineTimeoutSeconds: int,
        serverName: str,
        plugin: Optional[LLMPlugin]
    ):
        """Initialize the SSH service with its address, commands, authentication rules, and optional plugin."""
        self.address = address
        self.description = description
        self.commands = commands
        self.passwordRegex = passwordRegex
        self.deadlineTimeoutSeconds = deadlineTimeoutSeconds
        self.serverName = serverName
        self.plugin = plugin


class ServiceTCP(Service):
    """
    Configuration for a simple TCP honeypot service.

    Attributes:
        protocol (str): Always 'tcp' for TCP services.
        banner (str): Text banner sent to clients upon connection.
        deadlineTimeoutSeconds (int): Timeout in seconds before closing the connection.
        plugin (Optional[LLMPlugin]): Optional LLM plugin for dynamic TCP interaction.
    """
    protocol: str = "tcp"
    banner: str
    deadlineTimeoutSeconds: int
    plugin: Optional[LLMPlugin]

    def __init__(
        self,
        address: str,
        description: str,
        banner: str,
        deadlineTimeoutSeconds: int,
        plugin: Optional[LLMPlugin]
    ):
        """Initialize the TCP service with its address, banner, and timeout settings."""
        self.address = address
        self.description = description
        self.banner = banner
        self.deadlineTimeoutSeconds = deadlineTimeoutSeconds
        self.plugin = plugin

class Services:
    """
    Top-level container for a set of honeypot service configurations.

    Attributes:
        id (str): Unique identifier for this configuration bundle.
        services (List[Service]): List of individual service definitions 
            (instances of ServiceHTTP, ServiceSSH, or ServiceTCP).
        description (str): Human-readable summary of what this bundle represents.
        timestamp (str): ISO 8601 timestamp indicating when this configuration 
            was created or last updated (e.g., '2025-06-12T14:30:00Z').
    """
    id: str
    services: List[Service]
    description: str
    timestamp: str  # ISO 8601 (e.g., '2025-06-12T14:30:00Z')

    def __init__(
        self,
        id: str,
        services: List[Service],
        description: str,
        timestamp: str,
    ):
        """Initialize the top-level services configuration."""
        self.id = id
        self.services = services
        self.description = description
        self.timestamp = timestamp