#!/usr/bin/env python3
"""
Llama Stack Agent Chatbot - Simplified Version
"""

import os
import ssl
import httpx
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

class LlamaStackChatbot:
    def __init__(self):
        self.base_url = os.getenv("REMOTE_BASE_URL", "http://localhost:8321")
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "granite32-8b")
        self.session_id = None
        
        # Basic sampling parameters
        self.sampling_params = {
            "strategy": {"type": "greedy"},
            "max_tokens": 4096
        }
        
        # Setup client with SSL and auth
        self._setup_client()
        
        # Setup agent
        self.agent = Agent(
            client=self.client,
            model=self.model_id,
            instructions="You are a helpful AI assistant with access to web search, RAG, and OpenShift/Kubernetes tools.",
            tools=["builtin::websearch", "builtin::rag", "mcp::openshift"],
            sampling_params=self.sampling_params
        )
    
    def _setup_client(self):
        """Setup client with essential SSL and auth configuration"""
        # Get essential config
        skip_ssl_verify = os.getenv("SKIP_SSL_VERIFY", "False").lower() == "true"
        timeout = int(os.getenv("LLAMA_STACK_TIMEOUT", "30"))
        
        # Prepare client config
        client_kwargs = {
            "base_url": self.base_url,
            "timeout": timeout
        }
        
        # Handle SSL if needed
        if skip_ssl_verify:
            http_client = httpx.Client(verify=False, timeout=timeout)
            client_kwargs["http_client"] = http_client
        
        # # Add provider data for tools
        # provider_data = {}
        # if os.getenv("TAVILY_SEARCH_API_KEY"):
        #     provider_data["tavily_search_api_key"] = os.getenv("TAVILY_SEARCH_API_KEY")
        # if os.getenv("BRAVE_SEARCH_API_KEY"):
        #     provider_data["brave_search_api_key"] = os.getenv("BRAVE_SEARCH_API_KEY")
        # if os.getenv("OPENAI_API_KEY"):
        #     provider_data["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        
        # if provider_data:
        #     client_kwargs["provider_data"] = provider_data
        
        self.client = LlamaStackClient(**client_kwargs)
    
    def create_session(self):
        """Create a new agent session"""
        self.session_id = self.agent.create_session("chatbot-session")
    
    def chat(self, message: str):
        """Send a message to the agent and get response"""
        try:
            if not self.session_id:
                self.create_session()
            
            response = self.agent.create_turn(
                messages=[{"role": "user", "content": message}],
                session_id=self.session_id,
                stream=False
            )

            print(response.output_message.content)
            
           
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None
    
def main():
    """Main function to run a single query"""
    try:
        chatbot = LlamaStackChatbot()
        chatbot.create_session()
        
        # Test query
        query = "List pods in the openshift-gitops namespace and explain what each does"
        print(f"Query: {query}")
        chatbot.chat(query)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()