#!/usr/bin/env python3
"""
Llama Stack Agent Chatbot with All Tools

A comprehensive chatbot application using Llama Stack Agent with essential tools:
- Web search capabilities (builtin::websearch)
- RAG functionality (builtin::rag) 
- OpenShift/Kubernetes operations (mcp::openshift)

Author: AI Assistant
Usage: python llama_agent_chatbot.py
"""

import os
import sys
import logging
import json
import ssl
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from termcolor import cprint

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LlamaStackChatbot:
    """
    A comprehensive chatbot using Llama Stack Agent with all available tools
    """
    
    def __init__(self):
        """Initialize the chatbot with all available tools"""
        self.base_url = os.getenv("REMOTE_BASE_URL", "http://localhost:8321")
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "granite32-8b")
        self.session_id = None
        self.agent = None
        self.client = None
        
        # Configure sampling parameters
        temperature = float(os.getenv("TEMPERATURE", 0.0))
        if temperature > 0.0:
            top_p = float(os.getenv("TOP_P", 0.95))
            self.sampling_params = {
                "strategy": {"type": "top_p", "temperature": temperature, "top_p": top_p},
                "max_tokens": int(os.getenv("MAX_TOKENS", 4096)),
            }
        else:
            self.sampling_params = {
                "strategy": {"type": "greedy"},
                "max_tokens": int(os.getenv("MAX_TOKENS", 4096)),
            }
        
        # Force streaming to False for better response handling
        self.stream = False
        
        # Initialize client and agent
        self._setup_client()
        self._setup_agent()
        
    def _setup_client(self):
        """Setup the Llama Stack client with SSL and timeout handling"""
        try:
            # Get configuration from environment
            api_token = os.getenv("LLAMA_STACK_API_TOKEN")
            timeout = int(os.getenv("LLAMA_STACK_TIMEOUT", "30"))
            skip_ssl_verify = os.getenv("SKIP_SSL_VERIFY", "False").lower() == "true"
            
            # Configure HTTP client for SSL handling
            if skip_ssl_verify:
                # Create HTTP client that skips SSL verification
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                http_client = httpx.Client(
                    verify=False,
                    timeout=timeout
                )
                logger.warning("SSL verification disabled - not recommended for production")
            else:
                http_client = None
            
            # Prepare provider data for various tools
            provider_data = {}
            
            # Tavily Search API key for web search
            tavily_api_key = os.getenv("TAVILY_SEARCH_API_KEY")
            if tavily_api_key:
                provider_data["tavily_search_api_key"] = tavily_api_key
            
            # Brave Search API key
            brave_api_key = os.getenv("BRAVE_SEARCH_API_KEY") 
            if brave_api_key:
                provider_data["brave_search_api_key"] = brave_api_key
                
            # OpenAI API key for LLM-as-judge and other features
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                provider_data["openai_api_key"] = openai_api_key
            
            # Create the client with robust configuration
            client_kwargs = {
                "base_url": self.base_url,
                "timeout": timeout
            }
            
            if api_token:
                client_kwargs["api_key"] = api_token
                
            if http_client:
                client_kwargs["http_client"] = http_client
                
            if provider_data:
                client_kwargs["provider_data"] = provider_data
            
            self.client = LlamaStackClient(**client_kwargs)
            
            logger.info(f"Connected to Llama Stack server at {self.base_url}")
            if api_token:
                logger.info("Using API token for authentication")
            if skip_ssl_verify:
                logger.info("SSL verification disabled")
            
        except Exception as e:
            logger.error(f"Failed to setup client: {e}")
            logger.error(f"Base URL: {self.base_url}")
            logger.error(f"Timeout: {timeout}")
            raise
    
    def _get_available_tools(self) -> List[str]:
        """Get all available tools from the server"""
        try:
            # Get registered tools and toolgroups
            # registered_tools = self.client.tools.list()
            # registered_toolgroups = [t.toolgroup_id for t in registered_tools]
            # logger.debug(f"Initially registered toolgroups: {registered_toolgroups}")
            
            # All possible tools that could be available
            all_possible_tools = [
                "builtin::websearch",
                "builtin::rag",
                "mcp::openshift"
            ]
            
            # # Get list of available tools (no registration needed - server already configured)
            # all_tool_identifiers = [t.identifier for t in registered_tools]
            # logger.info(f"Available toolgroups: {set(registered_toolgroups)}")
            # logger.info(f"All available tool identifiers: {all_tool_identifiers}")
            
            # # Check for Kubernetes/OpenShift tools
            # kubernetes_tools = [
            #     tool for tool in all_tool_identifiers 
            #     if any(keyword in tool for keyword in ['pods', 'namespaces', 'projects', 'configuration'])
            # ]
            
            # # Build list of available tools using toolgroups that are already configured
            # available_tools = []
            
            # # Add builtin tools that are available  
            # if "builtin::websearch" in registered_toolgroups:
            #     available_tools.append("builtin::websearch")
            # if "builtin::rag" in registered_toolgroups:
            #     available_tools.append("builtin::rag")
            
            # # Add individual Kubernetes tools that are available (already configured on server)
            # if kubernetes_tools:
            #     logger.info(f"Found Kubernetes tools: {kubernetes_tools}")
            #     # Add the most essential tools for the user's query  
            #     essential_k8s_tools = [
            #         'namespaces_list', 'pods_list_in_namespace', 'pods_list', 'projects_list'
            #     ]
            #     for tool in essential_k8s_tools:
            #         if tool in all_tool_identifiers:
            #             available_tools.append(tool)
            #             logger.info(f"Added individual Kubernetes tool: {tool}")
            
            # # If no tools are available, at least try to use websearch
            # if not available_tools:
            #     # Check if any builtin tools are available
            #     builtin_tools = [t.toolgroup_id for t in registered_tools if t.toolgroup_id.startswith("builtin::")]
            #     if builtin_tools:
            #         available_tools = builtin_tools[:3]  # Limit to 3 tools
            #     else:
            #         available_tools = ["builtin::websearch"]  # Fallback
            
            logger.info(f"Available tools: {all_possible_tools}")
            return all_possible_tools
            
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            # Return basic tools as fallback
            fallback_tools = ["builtin::websearch"]
            logger.info(f"Using fallback tools: {fallback_tools}")
            return fallback_tools
    
    def _setup_agent(self):
        """Setup the Llama Stack agent with all available tools"""
        try:
            # Get all available tools
            tools = self._get_available_tools()
            
            # Use all available tools (server already configured)
            logger.info(f"Using tools configured on server: {tools}")
            
            # Create dynamic instructions based on available tools
            tool_descriptions = []
            
            # Check what Kubernetes tools we have
            kubernetes_tools_available = [tool for tool in tools if any(keyword in tool for keyword in ['pods', 'namespaces', 'projects'])]
            has_kubernetes_access = len(kubernetes_tools_available) > 0
            
            for tool in tools:
                if tool == "builtin::websearch":
                    tool_descriptions.append("- Web Search: Use builtin::websearch for searching current information on the internet")
                elif tool == "builtin::rag":
                    tool_descriptions.append("- RAG (Retrieval Augmented Generation): Use builtin::rag for document retrieval and knowledge base queries")
                elif tool in kubernetes_tools_available:
                    # Add description for individual Kubernetes tools
                    if tool == "namespaces_list":
                        tool_descriptions.append("- namespaces_list: List all namespaces in the cluster")
                    elif tool == "projects_list":
                        tool_descriptions.append("- projects_list: List all OpenShift projects")
                    elif tool == "pods_list":
                        tool_descriptions.append("- pods_list: List all pods in the cluster")
                    elif tool == "pods_list_in_namespace":
                        tool_descriptions.append("- pods_list_in_namespace: List pods in a specific namespace")
            
            if has_kubernetes_access:
                tool_descriptions.insert(-len(kubernetes_tools_available), "- Kubernetes/OpenShift Operations: Direct cluster access tools:")
            
            # Build usage instructions based on available tools
            usage_instructions = []
            usage_instructions.append("1. Always analyze the user's query to determine which tools would be most helpful")
            usage_instructions.append("2. Use multiple tools when necessary to provide comprehensive answers")
            
            if has_kubernetes_access:
                usage_instructions.append("3. For Kubernetes/OpenShift queries, you have DIRECT ACCESS to the cluster! Available tools:")
                if "pods_list_in_namespace" in tools:
                    usage_instructions.append("   - For the user's query about openshift-gitops namespace: Use 'pods_list_in_namespace' with namespace 'openshift-gitops'")
                if "namespaces_list" in tools:
                    usage_instructions.append("   - If that namespace doesn't exist, use 'namespaces_list' to show available namespaces")
                if "projects_list" in tools:
                    usage_instructions.append("   - Use 'projects_list' to list OpenShift projects")
                if "pods_list" in tools:
                    usage_instructions.append("   - Use 'pods_list' for cluster-wide pod listing")
            else:
                usage_instructions.append("3. For Kubernetes/OpenShift queries, since direct cluster access is not available, use web search to find current documentation and best practices")
            
            if "builtin::websearch" in tools:
                usage_instructions.append("4. When searching for current information, use builtin::websearch")
            if "builtin::rag" in tools:
                usage_instructions.append("5. For document retrieval and knowledge base queries, use builtin::rag")
            
            usage_instructions.append("6. Be thorough and provide detailed, helpful responses")
            usage_instructions.append("7. If a tool fails or is unavailable, try alternative approaches or inform the user")
            
            if has_kubernetes_access:
                usage_instructions.append("8. IMPORTANT: You have full access to the Kubernetes/OpenShift cluster. Use this responsibly and provide accurate, real-time cluster information.")
                if "pods_list_in_namespace" in tools and "namespaces_list" in tools:
                    usage_instructions.append("9. For the specific query about openshift-gitops pods: Try 'pods_list_in_namespace' first, then 'namespaces_list' as fallback.")
            
            instructions = f"""You are an advanced AI assistant with access to multiple tools and capabilities.

Your available tools include:
{chr(10).join(tool_descriptions)}

Instructions for tool usage:
{chr(10).join(usage_instructions)}

Your goal is to be as helpful as possible while leveraging all available tools effectively."""

            self.agent = Agent(
                client=self.client,
                model=self.model_id,
                instructions=instructions,
                tools=tools,
                sampling_params=self.sampling_params,
                max_infer_iters=5  # Allow multiple tool calls
            )
            
            logger.info(f"Agent initialized with model: {self.model_id}")
            logger.info(f"Tools configured: {tools}")
            
        except Exception as e:
            logger.error(f"Failed to setup agent: {e}")
            raise
    
    def create_session(self, session_name: str = None) -> str:
        """Create a new agent session"""
        if not session_name:
            session_name = f"chatbot-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            self.session_id = self.agent.create_session(session_name)
            logger.info(f"Created session: {self.session_id}")
            return self.session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def chat(self, message: str) -> str:
        """Send a message to the agent and get response"""
        if not self.session_id:
            self.create_session()
        
        try:
            response = self.agent.create_turn(
                messages=[{
                    "role": "user",
                    "content": message
                }],
                session_id=self.session_id,
                stream=self.stream
            )
            
            logger.debug(f"Response type: {type(response)}")
            logger.debug(f"Response has __iter__: {hasattr(response, '__iter__')}")
            
            # Handle different response types
            if hasattr(response, '__iter__') and not isinstance(response, (str, bytes)):
                # If it's a generator/iterator, collect all content
                logger.debug("Handling streaming/iterator response")
                full_response = ""
                for chunk in response:
                    logger.debug(f"Chunk type: {type(chunk)}, content: {chunk}")
                    if hasattr(chunk, 'content') and chunk.content:
                        if isinstance(chunk.content, list) and len(chunk.content) > 0:
                            for content_item in chunk.content:
                                if hasattr(content_item, 'text'):
                                    full_response += content_item.text
                                else:
                                    full_response += str(content_item)
                        else:
                            full_response += str(chunk.content)
                    else:
                        full_response += str(chunk)
                return full_response.strip() if full_response else "No response received"
            
            # Extract the text content from the response for non-streaming
            if hasattr(response, 'content') and response.content:
                if isinstance(response.content, list) and len(response.content) > 0:
                    return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
                elif isinstance(response.content, str):
                    return response.content
                else:
                    return str(response.content)
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        cprint("\n" + "="*80, "cyan")
        cprint("🤖 Llama Stack Agent Chatbot with All Tools", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")
        cprint("\nConnected to Llama Stack server and initialized with all available tools.", "green")
        cprint("Type 'quit', 'exit', or 'bye' to end the conversation.", "yellow")
        cprint("Type 'help' to see available commands.", "yellow")
        cprint("-"*80 + "\n", "cyan")
        
        # Create a session for this chat
        self.create_session()
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    cprint("\n👋 Goodbye! Thanks for chatting with the Llama Stack Agent!", "cyan")
                    break
                
                # Handle help command
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Show thinking indicator
                cprint("\n🤔 Agent is thinking...", "yellow")
                
                # Get response from agent
                response = self.chat(user_input)
                
                # Display response
                cprint(f"\n🤖 Agent: {response}", "green")
                cprint("-"*80, "cyan")
                
            except KeyboardInterrupt:
                cprint("\n\n👋 Goodbye! Thanks for chatting with the Llama Stack Agent!", "cyan")
                break
            except Exception as e:
                logger.error(f"Error in interactive chat: {e}")
                cprint(f"\n❌ An error occurred: {e}", "red")
    
    def _show_help(self):
        """Show help information"""
        cprint("\n📚 Available Commands:", "cyan", attrs=['bold'])
        cprint("- Type any question or request to chat with the agent", "white")
        cprint("- 'help' - Show this help message", "white") 
        cprint("- 'quit', 'exit', 'bye', 'q' - End the conversation", "white")
        cprint("\n🛠️ Available Tools:", "cyan", attrs=['bold'])
        cprint("- Web Search: Ask about current events, latest information", "white")
        cprint("- Kubernetes/OpenShift: Ask about pods, namespaces, cluster operations", "white")
        cprint("- RAG: Ask questions that need document retrieval", "white")
        
    def test_kubernetes_query(self):
        """Test the specific Kubernetes query requested by the user"""
        test_query = "Can you list the pods in the openshift-gitops namespace? If you cannot access that namespace, try to list namespaces or check your current Kubernetes configuration."
        
        cprint("\n" + "="*80, "cyan")
        cprint("🧪 Testing Kubernetes Query", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")
        cprint(f"\n📝 Query: {test_query}", "blue")
        cprint("\n🤔 Agent is processing...", "yellow")
        
        # Create session and get response
        self.create_session("kubernetes-test")
        response = self.chat(test_query)
        
        cprint(f"\n🤖 Agent Response:", "green", attrs=['bold'])
        cprint(f"{response}", "green")
        cprint("\n" + "="*80, "cyan")

def main():
    """Main function to run the chatbot"""
    print("🚀 Starting Llama Stack Agent Chatbot...")
    
    try:
        # Initialize chatbot
        chatbot = LlamaStackChatbot()
        
        # Check command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == "--test-kubernetes":
            # Run the specific test query
            chatbot.test_kubernetes_query()
        else:
            # Start interactive chat
            chatbot.interactive_chat()
            
    except KeyboardInterrupt:
        cprint("\n\n👋 Goodbye!", "cyan")
    except Exception as e:
        logger.error(f"Failed to start chatbot: {e}")
        cprint(f"\n❌ Failed to start chatbot: {e}", "red")
        sys.exit(1)

if __name__ == "__main__":
    main()
