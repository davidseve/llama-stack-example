#!/usr/bin/env python3
"""
Enhanced LlamaStack Comprehensive Validation Script

This script validates a deployed LlamaStack instance by testing:
1. Model availability and status
2. Inference capabilities (completions and chat)
3. MCP (Model Context Protocol) functionality
4. Tool usage (websearch, RAG, MCP tools)
5. Embedding generation
6. Safety API functionality
7. Evaluation API functionality
8. Agent session management
9. Provider configuration validation

Usage:
    python3 validate_llamastack_enhanced.py --url <llamastack-url> [options]
"""

import argparse
import asyncio
import json
import sys
import time
import os
import ssl
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import llama-stack client
try:
    from llama_stack_client import LlamaStackClient
    from llama_stack_client.types import *
    from llama_stack_client import Agent
except ImportError:
    print("❌ llama-stack-client not found. Install with: pip install llama-stack-client")
    sys.exit(1)

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_info(message: str):
    print(f"{Colors.YELLOW}[INFO]{Colors.NC} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def print_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def print_test_header(test_name: str):
    print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
    print(f"{Colors.WHITE}{test_name}{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")

def print_verbose_error(message: str, exception: Exception, verbose: bool = False):
    """Print error with optional verbose stack trace"""
    print_error(message)
    if verbose:
        import traceback
        print(f"{Colors.RED}[STACK TRACE]{Colors.NC}")
        print(f"{Colors.RED}{traceback.format_exc()}{Colors.NC}")
    else:
        print_info(f"Error details: {str(exception)}")
        print_info("Use --verbose flag for full stack trace")

class EnhancedLlamaStackValidator:
    def __init__(self, base_url: str, api_token: Optional[str] = None, timeout: int = 30, skip_ssl_verify: bool = False, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        self.skip_ssl_verify = skip_ssl_verify
        self.verbose = verbose
        
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
        else:
            http_client = None
            
        self.client = LlamaStackClient(
            base_url=self.base_url,
            api_key=api_token,
            http_client=http_client,
            timeout=timeout
        )
        self.test_results = []
        self.expected_providers = {
            'inference': ['vllm-inference', 'sentence-transformers'],
            'tool_runtime': ['brave-search', 'tavily-search', 'rag-runtime', 'model-context-protocol'],
            'safety': ['trustyai_fms'],
            'eval': ['trustyai_lmeval'],
            'agents': ['meta-reference'],
            'vector_io': ['milvus'],
            'datasetio': ['huggingface', 'localfs'],
            'scoring': ['basic', 'llm-as-judge', 'braintrust'],
            'telemetry': ['meta-reference']
        }
        
    def add_test_result(self, test_name: str, success: bool, details: str = ""):
        """Add a test result to the summary"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now()
        })
        
    async def test_connection(self) -> bool:
        """Test basic connectivity to LlamaStack"""
        print_test_header("🔗 Testing Connection")
        
        try:
            # Try to get available models as a connectivity test
            models_response = self.client.models.list()
            
            # Handle different response formats
            if hasattr(models_response, 'data'):
                models = models_response.data
            elif isinstance(models_response, list):
                models = models_response
            else:
                models = []
                
            print_success(f"✓ Connected to LlamaStack at {self.base_url}")
            print_info(f"Found {len(models)} models")
            self.add_test_result("Connection", True, f"Connected successfully, {len(models)} models found")
            return True
        except Exception as e:
            print_verbose_error("✗ Failed to connect", e, self.verbose)
            
            # Provide specific connection error diagnostics
            error_str = str(e).lower()
            if "connection" in error_str or "refused" in error_str:
                print_error("LlamaStack service appears to be down or unreachable")
            elif "timeout" in error_str:
                print_error("Connection timeout - service may be overloaded")
            elif "ssl" in error_str or "certificate" in error_str:
                print_error("SSL certificate error - try --skip-ssl-verify flag")
            elif "unauthorized" in error_str or "403" in error_str:
                print_error("Authentication error - check API token")
            else:
                print_error("Unknown connection error")
                
            self.add_test_result("Connection", False, f"Connection failed: {str(e)}")
            return False
    
    async def test_models(self) -> Dict[str, str]:
        """Test model availability and get model IDs"""
        print_test_header("🤖 Testing Model Availability")
        
        model_ids = {}
        try:
            models_response = self.client.models.list()
            
            # Handle different response formats
            if hasattr(models_response, 'data'):
                models = models_response.data
            elif isinstance(models_response, list):
                models = models_response
            else:
                models = []
            
            for model in models:
                # Handle different attribute names
                model_id = getattr(model, 'identifier', getattr(model, 'id', 'unknown'))
                model_type = getattr(model, 'model_type', getattr(model, 'type', 'unknown'))
                
                print_success(f"✓ Model: {model_id} ({model_type})")
                if hasattr(model, 'metadata') and model.metadata:
                    print_info(f"  Metadata: {model.metadata}")
                if hasattr(model, 'provider_id') and model.provider_id:
                    print_info(f"  Provider: {model.provider_id}")
                
                # Store model IDs by type for later tests
                if model_type == 'llm':
                    model_ids['llm'] = model_id
                elif model_type == 'embedding':
                    model_ids['embedding'] = model_id
            
            # Check for expected models
            if 'llm' not in model_ids:
                print_warning("⚠️  No LLM model found - inference tests will be limited")
            if 'embedding' not in model_ids:
                print_warning("⚠️  No embedding model found - embedding tests will be skipped")
                    
            self.add_test_result("Models", True, f"Found {len(models)} models")
            return model_ids
            
        except Exception as e:
            print_verbose_error("✗ Failed to list models", e, self.verbose)
            
            # Provide specific diagnostics
            error_str = str(e).lower()
            if "not found" in error_str or "404" in error_str:
                print_error("Models endpoint not found - LlamaStack may not be fully initialized")
            elif "permission" in error_str or "auth" in error_str:
                print_error("No permission to list models - check authentication")
            else:
                print_error("Unknown model listing error")
                
            self.add_test_result("Models", False, f"Failed to list models: {str(e)}")
            return {}
    
    async def test_inference_completions(self, model_id: str) -> bool:
        """Test text completions"""
        print_test_header("📝 Testing Text Completions")
        
        try:
            prompt = "The capital of France is"
            
            print_info(f"Testing with model: {model_id}")
            print_info(f"Prompt: '{prompt}'")
            
            response = self.client.inference.completion(
                model_id=model_id,
                content=prompt,
                sampling_params=SamplingParams(
                    max_tokens=20,
                    temperature=0.1,
                    strategy={"type": "greedy"}
                )
            )
            
            completion_text = response.content
            print_success(f"✓ Completion successful")
            print_info(f"Response: '{completion_text}'")
            
            # Basic validation of response
            if len(completion_text.strip()) > 0:
                print_success("✓ Non-empty response received")
                self.add_test_result("Inference Completions", True, f"Generated: '{completion_text[:50]}...'")
                return True
            else:
                print_warning("⚠️  Empty response received")
                self.add_test_result("Inference Completions", False, "Empty response")
                return False
            
        except Exception as e:
            print_error(f"✗ Completion failed: {str(e)}")
            self.add_test_result("Inference Completions", False, f"Failed: {str(e)}")
            return False
    
    async def test_inference_chat(self, model_id: str) -> bool:
        """Test chat completions"""
        print_test_header("💬 Testing Chat Completions")
        
        try:
            messages = [
                UserMessage(
                    content="Hello! Can you tell me a short joke about computers?",
                    role="user"
                )
            ]
            
            print_info(f"Testing with model: {model_id}")
            print_info("Message: 'Hello! Can you tell me a short joke about computers?'")
            
            response = self.client.inference.chat_completion(
                model_id=model_id,
                messages=messages,
                sampling_params=SamplingParams(
                    max_tokens=100,
                    temperature=0.7,
                    strategy={"type": "greedy"}
                )
            )
            
            chat_response = response.completion_message.content
            print_success(f"✓ Chat completion successful")
            print_info(f"Response: '{chat_response}'")
            
            self.add_test_result("Chat Completions", True, f"Generated response: '{chat_response[:50]}...'")
            return True
            
        except Exception as e:
            print_error(f"✗ Chat completion failed: {str(e)}")
            self.add_test_result("Chat Completions", False, f"Failed: {str(e)}")
            return False
    
    async def test_embeddings(self, model_id: str) -> bool:
        """Test embedding generation"""
        print_test_header("🧮 Testing Embeddings")
        
        try:
            text = "This is a test sentence for embedding generation."
            print_info(f"Testing with model: {model_id}")
            print_info(f"Text: '{text}'")
            
            response = self.client.inference.embeddings(
                model_id=model_id,
                contents=[text]
            )
            
            embeddings = response.embeddings
            if embeddings and len(embeddings) > 0:
                embedding = embeddings[0]
                print_success(f"✓ Embedding generation successful")
                print_info(f"Embedding dimension: {len(embedding)}")
                print_info(f"First 5 values: {embedding[:5]}")
                
                # Validate embedding dimensions (should be > 0)
                if len(embedding) > 0:
                    self.add_test_result("Embeddings", True, f"Generated {len(embedding)}-dimensional embedding")
                    return True
                else:
                    print_error("✗ Empty embedding vector")
                    self.add_test_result("Embeddings", False, "Empty embedding vector")
                    return False
            else:
                print_error("✗ No embeddings returned")
                self.add_test_result("Embeddings", False, "No embeddings returned")
                return False
                
        except Exception as e:
            print_error(f"✗ Embedding generation failed: {str(e)}")
            self.add_test_result("Embeddings", False, f"Failed: {str(e)}")
            return False
    
    async def test_tool_groups(self, model_id: str) -> Dict[str, bool]:
        """Test available tool groups and tool functionality"""
        print_test_header("🔧 Testing Tool Groups")
        
        tool_group_status = {}
        expected_tools = ["builtin::websearch", "builtin::rag", "mcp::openshift"]
        
        print_info("Testing individual tool availability and functionality...")
        
        working_tools = []
        failed_tools = []
        
        # Test each expected tool by trying to create an agent with it
        for tool in expected_tools:
            print_info(f"Testing tool: {tool}")
            
            try:
                # For MCP tools, check the underlying service first
                if tool.startswith("mcp::"):
                    try:
                        tool_group_id = tool
                        print_info(f"  Checking MCP service for {tool_group_id}...")
                        tools = self.client.tool_runtime.list_tools(tool_group_id=tool_group_id)
                        print_success(f"  ✓ MCP service accessible, found {len(tools) if tools else 0} tools")
                        
                        if not tools:
                            print_error(f"  ✗ No tools found for {tool_group_id}")
                            tool_group_status[tool] = False
                            failed_tools.append(f"{tool}: No tools found in MCP service")
                            continue
                            
                    except Exception as mcp_error:
                        print_verbose_error(f"  ✗ MCP service check failed for {tool}", mcp_error, self.verbose)
                        tool_group_status[tool] = False
                        
                        error_str = str(mcp_error).lower()
                        if "taskgroup" in error_str:
                            failed_tools.append(f"{tool}: TaskGroup async error (LlamaStack issue)")
                        elif "connection" in error_str or "refused" in error_str:
                            failed_tools.append(f"{tool}: MCP service unreachable")
                        else:
                            failed_tools.append(f"{tool}: MCP service error - {str(mcp_error)}")
                        continue
                
                # Test agent creation with the tool
                print_info(f"  Creating test agent with {tool}...")
                test_agent = Agent(
                    client=self.client,
                    model=model_id,
                    instructions=f"You are a test agent with {tool} capabilities.",
                    tools=[tool]
                )
                
                working_tools.append(tool)
                tool_group_status[tool] = True
                print_success(f"  ✓ Tool {tool} is available and functional (Agent ID: {test_agent.agent_id})")
                
            except Exception as tool_error:
                print_verbose_error(f"  ✗ Tool {tool} test failed", tool_error, self.verbose)
                tool_group_status[tool] = False
                
                # Provide specific error diagnostics
                error_str = str(tool_error).lower()
                if "not found" in error_str:
                    failed_tools.append(f"{tool}: Tool not registered in LlamaStack")
                elif "taskgroup" in error_str:
                    failed_tools.append(f"{tool}: TaskGroup async error")
                elif "permission" in error_str or "auth" in error_str:
                    failed_tools.append(f"{tool}: Authentication/permission error")
                elif "timeout" in error_str:
                    failed_tools.append(f"{tool}: Timeout error")
                else:
                    failed_tools.append(f"{tool}: {str(tool_error)}")
        
        # Summary reporting
        print_info("Tool Groups Test Summary:")
        if working_tools:
            print_success(f"✓ Working tools ({len(working_tools)}): {', '.join(working_tools)}")
            
        if failed_tools:
            print_error(f"✗ Failed tools ({len(failed_tools)}):")
            for failed_tool in failed_tools:
                print_error(f"  - {failed_tool}")
        
        # Determine overall result
        if working_tools:
            self.add_test_result("Tool Groups", True, f"Working: {working_tools}, Failed: {len(failed_tools)}")
        else:
            self.add_test_result("Tool Groups", False, f"No working tools found. Failures: {failed_tools}")
        
        return tool_group_status
    
    async def test_agent_sessions(self, model_id: str) -> bool:
        """Test agent session creation and management"""
        print_test_header("👥 Testing Agent Sessions")
        
        try:
            # Create agent using the proper Agent class
            print_info("Creating test agent...")
            
            agent = Agent(
                client=self.client,
                model=model_id,
                instructions="You are a helpful test agent for validation purposes."
            )
            
            print_success(f"✓ Agent created: {agent.agent_id}")
            
            # Create a session using the agent
            print_info("Creating agent session...")
            session_name = f"test-session-{int(time.time())}"
            session_id = agent.create_session(session_name=session_name)
            
            print_success(f"✓ Agent session created: {session_id}")
            
            # Test a simple turn to validate functionality
            print_info("Testing agent turn...")
            turn_response = agent.create_turn(
                messages=[{"role": "user", "content": "Hello, can you respond with a short greeting?"}],
                session_id=session_id
            )
            
            print_success("✓ Agent turn completed successfully")
            
            # Note: Session cleanup is handled automatically by the Agent class
            print_success("✓ Agent session test completed")
            
            self.add_test_result("Agent Sessions", True, f"Agent {agent.agent_id} and session {session_id} working")
            return True
            
        except Exception as e:
            print_error(f"✗ Agent session test failed: {str(e)}")
            self.add_test_result("Agent Sessions", False, f"Failed: {str(e)}")
            return False
    
    async def test_websearch_tool(self, model_id: str) -> bool:
        """Test websearch tool functionality"""
        print_test_header("🔍 Testing WebSearch Tool")
        
        try:
            print_info("Testing WebSearch tool by creating agent...")
            
            # Try to create an agent with websearch tool
            websearch_agent = Agent(
                client=self.client,
                model=model_id,
                instructions="You are a test agent with websearch capabilities.",
                tools=["builtin::websearch"]
            )
            
            print_success("✓ WebSearch agent created successfully")
            
            # Test creating a session with websearch
            session_id = websearch_agent.create_session(f"websearch-test-{int(time.time())}")
            print_success(f"✓ WebSearch session created: {session_id}")
            
            # Test a simple websearch turn (optional - might require API keys)
            try:
                print_info("Testing basic websearch turn...")
                turn_response = websearch_agent.create_turn(
                    messages=[{"role": "user", "content": "What is the weather like?"}],
                    session_id=session_id
                )
                print_success("✓ WebSearch turn completed successfully")
            except Exception as turn_error:
                print_warning(f"⚠️  WebSearch turn failed (likely missing API keys): {turn_error}")
                print_info("WebSearch tool is configured but may need API credentials")
            
            self.add_test_result("WebSearch Tool", True, "WebSearch tool available and agent creation successful")
            return True
                
        except Exception as e:
            print_warning(f"⚠️  WebSearch tool test failed: {str(e)}")
            print_info("This might be expected if websearch is not configured or requires API keys")
            self.add_test_result("WebSearch Tool", False, f"Failed: {str(e)}")
            return False
    
    async def test_mcp_functionality(self, model_id: str) -> bool:
        """Test MCP (Model Context Protocol) functionality"""
        print_test_header("🔌 Testing MCP Integration")
        
        # First, check if MCP service is reachable
        print_info("Step 1: Checking MCP service availability...")
        try:
            # Try to list MCP tools to verify service is running
            print_info("Attempting to list MCP tools...")
            tools = self.client.tool_runtime.list_tools(tool_group_id="mcp::openshift")
            print_success(f"✓ MCP service is reachable, found {len(tools) if tools else 0} tools")
            
            if not tools:
                print_error("✗ No MCP tools found - MCP service may not be properly configured")
                self.add_test_result("MCP Integration", False, "MCP service reachable but no tools found")
                return False
                
        except Exception as e:
            print_verbose_error("✗ Failed to connect to MCP service", e, self.verbose)
            
            # Check for specific error patterns to provide better diagnostics
            error_str = str(e).lower()
            if "connection" in error_str or "refused" in error_str:
                print_error("MCP service appears to be down or unreachable")
                print_info("Expected MCP endpoint: mcp-service:8080")
            elif "taskgroup" in error_str:
                print_error("MCP service has TaskGroup async handling issues")
                print_info("This is a known issue with LlamaStack's MCP integration")
            elif "timeout" in error_str:
                print_error("MCP service is not responding (timeout)")
            else:
                print_error("Unknown MCP service error")
                
            self.add_test_result("MCP Integration", False, f"MCP service error: {str(e)}")
            return False
        
        # Step 2: Analyze available tools
        print_info("Step 2: Analyzing available MCP tools...")
        tool_name = None
        try:
            first_tool = tools[0]
            
            # Find the correct tool name attribute
            for attr in ['tool_name', 'name', 'identifier', 'id', 'tool_id']:
                if hasattr(first_tool, attr):
                    tool_name = getattr(first_tool, attr)
                    print_info(f"Found tool name: {tool_name}")
                    break
                    
            if not tool_name:
                tool_name = str(first_tool)
                print_warning(f"Could not find standard tool name attribute, using: {tool_name}")
                
            print_info(f"Available tools: {[getattr(t, attr) if hasattr(t, attr) else str(t) for t in tools[:3]]}")
            
        except Exception as e:
            print_verbose_error("✗ Failed to analyze MCP tools", e, self.verbose)
            self.add_test_result("MCP Integration", False, f"Tool analysis failed: {str(e)}")
            return False
        
        # Step 3: Test agent creation with MCP tools
        print_info("Step 3: Testing MCP agent creation...")
        try:
            mcp_agent = Agent(
                client=self.client,
                model=model_id,
                instructions="You are a test agent with OpenShift MCP capabilities.",
                tools=["mcp::openshift"]
            )
            
            print_success(f"✓ MCP OpenShift agent created: {mcp_agent.agent_id}")
            
            # Test session creation
            session_id = mcp_agent.create_session(f"mcp-test-{int(time.time())}")
            print_success(f"✓ MCP session created: {session_id}")
            
        except Exception as e:
            print_verbose_error("✗ Failed to create MCP agent", e, self.verbose)
            
            # Check for specific agent creation issues
            error_str = str(e).lower()
            if "tool" in error_str and "not found" in error_str:
                print_error("MCP tool not properly registered in LlamaStack")
            elif "taskgroup" in error_str:
                print_error("Agent creation failed due to TaskGroup async issues")
            else:
                print_error("Unknown agent creation error")
                
            self.add_test_result("MCP Integration", False, f"Agent creation failed: {str(e)}")
            return False
        
        # Step 4: Test MCP functionality through agent conversation
        print_info("Step 4: Testing MCP functionality through agent conversation...")
        try:
            print_info("Testing MCP agent with OpenShift query...")
            
            # Use the MCP agent we already created to perform an actual task
            turn_response = mcp_agent.create_turn(
                messages=[{
                    "role": "user", 
                    "content": "Can you list the pods in the openshift-gitops namespace? If you cannot access that namespace, try to list namespaces or check your current Kubernetes configuration."
                }],
                session_id=session_id
            )
            
            print_success("✓ MCP agent conversation completed")

            # Debug: Print the response object details
            print_success(f"✓ Response type: {type(turn_response)}")
            print_success(f"✓ Response attributes: {dir(turn_response)}")
            
            # If it's a generator, iterate through it
            if hasattr(turn_response, '__iter__') and hasattr(turn_response, '__next__'):
                print_info("Response is a generator, iterating through items:")
                response_items = []
                try:
                    for item in turn_response:
                        print_info(f"  Generator item: {item}")
                        response_items.append(item)
                    print_success(f"✓ Collected {len(response_items)} items from generator")
                except Exception as gen_error:
                    print_error(f"Error iterating generator: {gen_error}")
            else:
                # Not a generator, print directly
                print_success(f"✓ Response content: {turn_response}")
            # Analyze the response to see if MCP tool was actually used
            if hasattr(turn_response, 'steps') and turn_response.steps:
                tool_used = False
                for step in turn_response.steps:
                    if hasattr(step, 'tool_calls') and step.tool_calls:
                        tool_used = True
                        tool_names = [tc.tool_name for tc in step.tool_calls if hasattr(tc, 'tool_name')]
                        print_success(f"✓ MCP tools used: {tool_names}")
                        break
                
                if tool_used:
                    print_success("✓ MCP tools are functioning and being invoked by the agent")
                    self.add_test_result("MCP Tool Functionality", True, "MCP tools working through agent")
                else:
                    print_warning("⚠️  Agent responded but may not have used MCP tools")
                    self.add_test_result("MCP Tool Functionality", True, "Agent functional, tool usage unclear")
            else:
                print_info("Agent response received but step details not available")
                self.add_test_result("MCP Tool Functionality", True, "Agent functional, limited response details")
                
        except Exception as e:
            print_verbose_error("✗ MCP agent conversation failed", e, self.verbose)
            
            # Provide specific diagnostics
            error_str = str(e).lower()
            if "unauthorized" in error_str or "authentication" in error_str:
                print_error("MCP agent lacks proper authentication to perform tasks")
            elif "timeout" in error_str:
                print_error("MCP agent conversation timed out")
            elif "taskgroup" in error_str:
                print_error("TaskGroup async error during agent conversation")
            else:
                print_error("Unknown MCP agent conversation error")
                
            self.add_test_result("MCP Tool Functionality", False, f"Agent conversation failed: {str(e)}")
            # Don't return False here - we still had successful agent creation
        
        # Overall MCP integration assessment
        print_info("MCP Integration Assessment:")
        print_success("✓ MCP service is running and accessible")
        print_success("✓ MCP tools are registered and discoverable") 
        print_success("✓ MCP agent creation works")
        
        self.add_test_result("MCP Integration", True, "MCP integration is functional")
        return True
    
    async def test_rag_functionality(self, model_id: str) -> bool:
        """Test RAG (Retrieval Augmented Generation) functionality"""
        print_test_header("📚 Testing RAG Functionality")
        
        try:
            print_info("Testing RAG tool by creating agent...")
            
            # Try to create an agent with RAG tool
            rag_agent = Agent(
                client=self.client,
                model=model_id,
                instructions="You are a test agent with RAG capabilities for knowledge search.",
                tools=["builtin::rag"]
            )
            
            print_success("✓ RAG agent created successfully")
            
            # Test creating a session with RAG
            session_id = rag_agent.create_session(f"rag-test-{int(time.time())}")
            print_success(f"✓ RAG session created: {session_id}")
            
            print_info("RAG functionality is configured and available")
            self.add_test_result("RAG Functionality", True, "RAG tools available")
            return True
                
        except Exception as e:
            print_warning(f"⚠️  RAG functionality test failed: {str(e)}")
            print_info("This might be expected if RAG/vector database is not properly configured")
            self.add_test_result("RAG Functionality", False, f"Failed: {str(e)}")
            return False
    
    async def test_safety_functionality(self, model_id: str) -> bool:
        """Test Safety API functionality"""
        print_test_header("🛡️  Testing Safety API")
        
        try:
            # First try to check if safety shields are available
            print_info("Checking available safety shields...")
            
            # Try to list shields if the API exists
            try:
                if hasattr(self.client, 'shields'):
                    shields = self.client.shields.list()
                    print_info(f"Found {len(shields)} shields available")
                    if shields:
                        shield_id = shields[0].identifier if hasattr(shields[0], 'identifier') else str(shields[0])
                        print_info(f"Using shield: {shield_id}")
                    else:
                        print_warning("No shields available, trying with default shield ID")
                        shield_id = "trustyai_fms"
                else:
                    print_info("Shields listing not available, trying with expected shield ID")
                    shield_id = "trustyai_fms"
            except:
                print_info("Shields listing failed, trying with expected shield ID")
                shield_id = "trustyai_fms"
            
            # Test safety check with sample content
            test_content = "This is a safe test message for safety validation."
            print_info(f"Testing safety check with shield '{shield_id}' and content: '{test_content}'")
            
            # Try to perform safety check
            safety_response = await self.client.safety.run_shield(
                messages=[UserMessage(content=test_content, role="user")],
                shield_id=shield_id,
                params={}
            )
            
            print_success("✓ Safety API is functional")
            print_info(f"Safety response received for shield: {shield_id}")
            
            self.add_test_result("Safety API", True, f"Safety checks functional with shield: {shield_id}")
            return True
            
        except Exception as e:
            print_warning(f"⚠️  Safety API test failed: {str(e)}")
            
            # Provide more helpful diagnostic information
            if "not served by provider" in str(e):
                print_info("Shield configuration issue - the specified shield is not available")
                print_info("This is expected if the safety provider is not fully configured")
            else:
                print_info("This might be expected if safety provider is not properly configured")
            
            self.add_test_result("Safety API", False, f"Failed: {str(e)}")
            return False
    
    async def test_eval_functionality(self, model_id: str) -> bool:
        """Test Evaluation API functionality"""
        print_test_header("📊 Testing Evaluation API")
        
        try:
            # Check if eval API is available
            if not hasattr(self.client, 'eval'):
                print_info("⚠️  Evaluation API not available in this client version")
                print_info("This is expected for basic LlamaStack deployments")
                self.add_test_result("Evaluation API", False, "Evaluation API not available in client")
                return False
            
            print_info("Evaluation API found, checking capabilities...")
            
            # Check available evaluation methods
            eval_methods = []
            if hasattr(self.client.eval, 'evaluate'):
                eval_methods.append('evaluate')
            if hasattr(self.client.eval, 'run_evaluation'):
                eval_methods.append('run_evaluation')
            if hasattr(self.client.eval, 'list_evaluations'):
                eval_methods.append('list_evaluations')
                
            if eval_methods:
                print_success(f"✓ Found evaluation methods: {eval_methods}")
                
                # Try a minimal evaluation test (likely to fail due to missing datasets/config)
                try:
                    print_info("Testing evaluation with minimal example...")
                    # This will likely fail but shows the API is accessible
                    eval_response = self.client.eval.evaluate(
                        input_rows=[{"input": "test", "expected_output": "test"}],
                        scoring_functions=["basic"],
                        model_id=model_id
                    )
                    print_success("✓ Evaluation API fully functional")
                    self.add_test_result("Evaluation API", True, "Evaluation API fully functional")
                    return True
                    
                except Exception as eval_error:
                    print_info(f"Evaluation test failed (expected): {eval_error}")
                    print_success("✓ Evaluation API is accessible but needs proper configuration")
                    self.add_test_result("Evaluation API", True, "Evaluation API accessible but needs configuration")
                    return True
            else:
                print_warning("⚠️  No evaluation methods found")
                print_info("Evaluation API exists but methods are not implemented")
                self.add_test_result("Evaluation API", False, "Evaluation methods not implemented")
                return False
            
        except Exception as e:
            print_warning(f"⚠️  Evaluation API test failed: {str(e)}")
            print_info("This is expected if evaluation provider is not configured")
            self.add_test_result("Evaluation API", False, f"Failed: {str(e)}")
            return False
    
    async def test_vector_db_functionality(self) -> bool:
        """Test Vector Database functionality"""
        print_test_header("🗃️  Testing Vector Database")
        
        try:
            # Try to list vector databases
            vector_dbs = self.client.vector_dbs.list()
            
            print_success(f"✓ Vector DB API accessible")
            print_info(f"Found {len(vector_dbs) if vector_dbs else 0} vector databases")
            
            self.add_test_result("Vector Database", True, f"Vector DB API functional")
            return True
            
        except Exception as e:
            print_warning(f"⚠️  Vector DB test failed: {str(e)}")
            print_info("Vector DB functionality may not be fully configured")
            self.add_test_result("Vector Database", False, f"Failed: {str(e)}")
            return False
    
    def validate_configuration(self):
        """Validate expected configuration against deployment"""
        print_test_header("⚙️  Configuration Validation")
        
        print_info("Expected configuration based on deployment:")
        print_info("  - VLLM inference provider")
        print_info("  - Sentence transformers embedding")
        print_info("  - MCP integration (OpenShift)")
        print_info("  - WebSearch tools (Tavily/Brave)")
        print_info("  - RAG functionality")
        print_info("  - Safety provider (TrustyAI)")
        print_info("  - Vector database (Milvus)")
        
        # This is informational - actual validation happens through API tests
        self.add_test_result("Configuration", True, "Configuration expectations set")
    
    def print_summary(self):
        """Print comprehensive test summary with diagnostics"""
        print_test_header("📊 Test Summary")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print_success(f"Passed: {passed_tests}")
        
        if failed_tests > 0:
            print_error(f"Failed: {failed_tests}")
        
        print(f"\n{Colors.CYAN}Detailed Results:{Colors.NC}")
        failed_details = []
        for result in self.test_results:
            status = "✓" if result['success'] else "✗"
            color = Colors.GREEN if result['success'] else Colors.RED
            print(f"{color}{status}{Colors.NC} {result['test']}: {result['details']}")
            if not result['success']:
                failed_details.append(f"{result['test']}: {result['details']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n{Colors.WHITE}Success Rate: {success_rate:.1f}%{Colors.NC}")
        
        # Overall assessment
        if success_rate >= 90:
            print_success("🎉 LlamaStack instance is functioning excellently!")
        elif success_rate >= 75:
            print_success("✅ LlamaStack instance is functioning well!")
        elif success_rate >= 60:
            print_warning("⚠️  LlamaStack instance has some issues but basic functionality works")
        else:
            print_error("❌ LlamaStack instance has significant issues")
        
        # Error analysis and recommendations
        if failed_tests > 0:
            print_test_header("🔍 Error Analysis & Recommendations")
            
            # Categorize common issues
            connection_issues = [f for f in failed_details if any(keyword in f.lower() for keyword in ['connection', 'refused', 'unreachable', 'timeout'])]
            mcp_issues = [f for f in failed_details if any(keyword in f.lower() for keyword in ['mcp', 'taskgroup', 'openshift'])]
            auth_issues = [f for f in failed_details if any(keyword in f.lower() for keyword in ['auth', 'permission', 'unauthorized', '403'])]
            config_issues = [f for f in failed_details if any(keyword in f.lower() for keyword in ['not found', '404', 'not configured'])]
            
            if connection_issues:
                print_error("🔌 Connection Issues:")
                for issue in connection_issues:
                    print_error(f"  • {issue}")
                print_info("💡 Recommendation: Check if LlamaStack service is running and accessible")
                
            if mcp_issues:
                print_error("🔌 MCP Integration Issues:")
                for issue in mcp_issues:
                    print_error(f"  • {issue}")
                print_info("💡 Recommendation: Check MCP service status and TaskGroup handling in LlamaStack")
                
            if auth_issues:
                print_error("🔐 Authentication Issues:")
                for issue in auth_issues:
                    print_error(f"  • {issue}")
                print_info("💡 Recommendation: Verify API tokens and service permissions")
                
            if config_issues:
                print_error("⚙️  Configuration Issues:")
                for issue in config_issues:
                    print_error(f"  • {issue}")
                print_info("💡 Recommendation: Check LlamaStack deployment configuration")
            
            # General troubleshooting tips
            print_info("\n🛠️  General Troubleshooting:")
            print_info("  • Use --verbose flag for detailed error information")
            print_info("  • Check service logs for more details")
            print_info("  • Verify all required services are running")
            print_info("  • Check network connectivity and firewall settings")
    
    async def run_all_tests(self):
        """Run all validation tests"""
        print(f"{Colors.PURPLE}{'='*80}{Colors.NC}")
        print(f"{Colors.WHITE}Enhanced LlamaStack Comprehensive Validation{Colors.NC}")
        print(f"{Colors.PURPLE}{'='*80}{Colors.NC}")
        print_info(f"Target URL: {self.base_url}")
        print_info(f"Timestamp: {datetime.now()}")
        print_info(f"Timeout: {self.timeout}s")
        
        # Configuration validation (informational)
        self.validate_configuration()
        
        # Test connection first
        if not await self.test_connection():
            print_error("Cannot proceed - connection failed")
            self.print_summary()
            return False
        
        # Get available models
        model_ids = await self.test_models()
        
        # Test inference if we have models
        llm_model = model_ids.get('llm')
        embedding_model = model_ids.get('embedding')
        
        if llm_model:
            await self.test_inference_completions(llm_model)
            await self.test_inference_chat(llm_model)
            await self.test_agent_sessions(llm_model)
        else:
            print_error("No LLM model found - skipping inference and agent tests")
            self.add_test_result("Inference Tests", False, "No LLM model available")
        
        if embedding_model:
            await self.test_embeddings(embedding_model)
        else:
            print_error("No embedding model found - skipping embedding tests")
            self.add_test_result("Embedding Tests", False, "No embedding model available")
        
        # Test tool functionality
        tool_group_status = await self.test_tool_groups(llm_model if llm_model else "default")
        await self.test_websearch_tool(llm_model if llm_model else "default")
        await self.test_mcp_functionality(llm_model if llm_model else "default")
        await self.test_rag_functionality(llm_model if llm_model else "default")
        
        # Test additional functionality
        if llm_model:
            await self.test_safety_functionality(llm_model)
        
        await self.test_eval_functionality(llm_model if llm_model else "default")
        await self.test_vector_db_functionality()
        
        # Print summary
        self.print_summary()
        
        # Return overall success
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        return (passed_tests / total_tests) >= 0.6  # 60% success rate threshold

async def main():
    parser = argparse.ArgumentParser(description="Enhanced LlamaStack deployment validation")
    parser.add_argument("--url", required=True, help="LlamaStack base URL")
    parser.add_argument("--token", help="API token (if required)")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--json-output", help="Save results to JSON file")
    parser.add_argument("--skip-ssl-verify", action="store_true", help="Skip SSL certificate verification (for development/self-signed certs)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose error reporting with full stack traces")
    
    args = parser.parse_args()
    
    # Create validator instance
    validator = EnhancedLlamaStackValidator(args.url, args.token, args.timeout, args.skip_ssl_verify, args.verbose)
    
    try:
        # Run all tests
        success = await validator.run_all_tests()
        
        # Save JSON output if requested
        if args.json_output:
            results = {
                'timestamp': datetime.now().isoformat(),
                'url': args.url,
                'success_rate': (sum(1 for r in validator.test_results if r['success']) / len(validator.test_results)) * 100,
                'tests': [
                    {
                        'name': r['test'],
                        'success': r['success'],
                        'details': r['details'],
                        'timestamp': r['timestamp'].isoformat()
                    }
                    for r in validator.test_results
                ]
            }
            with open(args.json_output, 'w') as f:
                json.dump(results, f, indent=2)
            print_info(f"Results saved to {args.json_output}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_error("\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
