from typing import Tuple, List, Optional, Literal, Union
from abc import ABC

# All this file only specifies the structure of the Beelzebub service configuration files
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

    def __init__(self, prompt: str):
        """
        Initialize the LLM plugin with a custom prompt.

        Args:
            prompt (str): The initial system prompt for the LLM to use.
        """
        self.llmProvider = "openai"        # Provider of the LLM
        self.llmModel = "gpt-4o-mini"      # Model variant to use
        self.openAISecretKey = "placeholder"  # Placeholder for secret key
        self.prompt = prompt                # Base conversation prompt

class Command(ABC):
    """
    Base class for command rules in honeypot services.

    Attributes:
        regex (str): The regex pattern to match incoming commands.
        handler (str): The name of the handler function to invoke.
        plugin (Optional[str]): Plugin name to handle command (e.g., 'LLMHoneypot').
    """
    def __init__(
        self,
        regex: str,
        handler: str,
        plugin: Optional[Literal["LLMHoneypot"]]
    ):
        """
        Initialize a generic command rule.

        Args:
            regex (str): Regular expression for matching the command.
            handler (str): Function or script that will process the command.
            plugin (Optional[str]): Optional plugin identifier for dynamic handling.
        """
        self.regex = regex                # Pattern to match
        self.handler = handler            # Handler to execute
        self.plugin = plugin              # Optional dynamic plugin

class CommandHTTP(Command):
    """
    HTTP-specific command rule.

    Attributes:
        headers (Tuple[str, ...]): HTTP headers to include in the response.
        statusCode (int): HTTP status code to return.
    """

    def __init__(
        self,
        regex: str,
        handler: str,
        headers: Tuple[str, ...],
        statusCode: int
    ):
        """
        Initialize the HTTP command rule.

        Args:
            regex (str): Regex to match the HTTP path or method.
            handler (str): Handler function for matched requests.
            headers (Tuple[str, ...]): Response headers.
            statusCode (int): HTTP status code for the response.
        """
        self.headers = headers            # Response headers tuple
        self.statusCode = statusCode      # HTTP status to return
        super().__init__(regex, handler, None)

class CommandHTTPwithLLM(Command):
    """
    HTTP command rule with integrated LLM handling.

    Attributes:
        headers (Tuple[str, ...]): HTTP headers to include in the response.
        statusCode (int): HTTP status code to return.
    """

    def __init__(
        self,
        headers: Tuple[str, ...],
        statusCode: int
    ):
        """
        Initialize the HTTP command rule that uses the LLM plugin.

        Args:
            headers (Tuple[str, ...]): Response headers.
            statusCode (int): HTTP status code.
        """
        self.headers = headers            # LLM response headers
        self.statusCode = statusCode      # LLM response status
        super().__init__("^.*$", "", "LLMHoneypot")

class CommandSSH(Command):
    """
    SSH-specific command rule.

    Attributes:
        regex (str): Regex pattern for matching SSH commands.
        handler (str): Handler name to process SSH command.
    """

    def __init__(
        self,
        regex: str,
        handler: str
    ):
        """
        Initialize the SSH command rule.

        Args:
            regex (str): Regex pattern for SSH command matching.
            handler (str): Handler function to process SSH command.
        """
        super().__init__(regex, handler, None)

class CommandSSHwithLLM(Command):
    """
    SSH command rule with integrated LLM handling.
    """
    def __init__(
        self,
    ):
        """
        Initialize the SSH command rule that uses the LLM plugin.
        """
        super().__init__("^(.+)$", "", "LLMHoneypot")

class Service(ABC):
    """
    Abstract base class for all honeypot services.

    Attributes:
        apiVersion (str): API version of the configuration schema.
        protocol (str): Communication protocol ('http' or 'ssh').
        address (str): Network address and port (e.g., ':80', ':22').
        description (str): Human-readable service description.
        cve_tags (List[str]): Relevant CVE identifiers.
        cve_description (str): Description of vulnerabilities.
    """

    def __init__(
        self,
        protocol: str,
        address: str,
        description: str,
        cve_tags: List[str],
        cve_description: str
    ):
        """
        Initialize core service properties.

        Args:
            protocol (str): Protocol name.
            address (str): Service listening address and port.
            description (str): Short, human-readable description.
            cve_tags (List[str]): CVE tags for tracking exploits.
            cve_description (str): Details of the exploited vulnerabilities.
        """
        self.apiVersion = "v1"         # Schema version
        self.protocol = protocol         # Service protocol
        self.address = address           # Listen address
        self.description = description   # Service description
        self.cve_tags = cve_tags         # List of CVEs
        self.cve_description = cve_description  # CVE details

class ServiceHTTP(Service):
    """
    Configuration for an HTTP honeypot service.

    Attributes:
        commands (List[Union[CommandHTTP, CommandHTTPwithLLM]]): HTTP rules.
        plugin (LLMPlugin): Plugin for dynamic LLM responses.
    """

    def __init__(
        self,
        address: str,
        description: str,
        cve_tags: List[str],
        cve_description: str,
        commands: List[Union[CommandHTTP, CommandHTTPwithLLM]],
        plugin: LLMPlugin
    ):
        """
        Initialize HTTP service with its address, commands, and LLM plugin.

        Args:
            address (str): Service listening address (e.g., ':80').
            description (str): Human-readable description of service.
            cve_tags (List[str]): CVEs this service is vulnerable to.
            cve_description (str): Descriptive text of vulnerabilities.
            commands (List[...]): HTTP command rules.
            plugin (LLMPlugin): LLM plugin instance for dynamic handling.
        """
        self.commands = commands         # HTTP command list
        self.plugin = plugin             # LLM plugin for responses
        super().__init__("http", address, description, cve_tags, cve_description)

class ServiceSSH(Service):
    """
    Configuration for an SSH honeypot service.

    Attributes:
        commands (List[Union[CommandSSH, CommandSSHwithLLM]]): SSH rules.
        passwordRegex (str): Regex for accepted or logged passwords.
        serverName (str): Fake server name shown to clients.
        plugin (LLMPlugin): Plugin for dynamic SSH interaction.
    """

    def __init__(
        self,
        address: str,
        description: str,
        cve_tags: List[str],
        cve_description: str,
        commands: List[Union[CommandSSH, CommandSSHwithLLM]],
        passwordRegex: str,
        serverName: str,
        plugin: LLMPlugin
    ):
        """
        Initialize SSH service with its address, commands, auth rules, and LLM plugin.

        Args:
            address (str): Listening address (e.g., ':22').
            description (str): Human-readable description of the SSH service.
            cve_tags (List[str]): Vulnerability CVEs.
            cve_description (str): Description of SSH CVEs.
            commands (List[...]): SSH command rules.
            passwordRegex (str): Regex for password matching/logging.
            serverName (str): Faked server name for clients.
            plugin (LLMPlugin): LLM plugin for dynamic SSH replies.
        """
        self.commands = commands         # SSH command list
        self.passwordRegex = passwordRegex  # Password regex rule
        self.serverName = serverName     # Fake SSH server banner
        self.plugin = plugin             # LLM plugin for SSH
        super().__init__("ssh", address, description, cve_tags, cve_description)

class Services:
    """
    Container for a set of honeypot service configurations.

    Attributes:
        id (str): Unique identifier for this config bundle.
        services (List[Service]): List of configured services.
        description (str): Summary of what this bundle represents.
        timestamp (str): ISO 8601 timestamp of last update.
    """
    id: str
    services: List[Service]
    description: str
    timestamp: str  # ISO 8601 format

    def __init__(
        self,
        id: str,
        services: List[Service],
        description: str,
        timestamp: str,
    ):
        """
        Initialize the top-level services configuration.

        Args:
            id (str): UUID or unique name for this bundle.
            services (List[Service]): Instances of ServiceHTTP/SSH.
            description (str): Human-readable bundle summary.
            timestamp (str): Creation/update time in ISO format.
        """
        self.id = id                     # Configuration bundle ID
        self.services = services         # List of Service instances
        self.description = description   # Bundle description
        self.timestamp = timestamp       # Last update timestamp
