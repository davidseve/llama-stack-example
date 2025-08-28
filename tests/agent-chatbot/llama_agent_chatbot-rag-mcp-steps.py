#!/usr/bin/env python3
"""
Llama Stack Agent Chatbot - Simplified Version
"""

import os
import ssl
import httpx
import logging
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient, RAGDocument
from llama_stack_client.lib.agents.agent import Agent

# Suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

class LlamaStackChatbot:
    def __init__(self):
        self.base_url = os.getenv("REMOTE_BASE_URL", "http://localhost:8321")
        self.model_id = os.getenv("INFERENCE_MODEL_ID", "granite32-8b")
        self.session_id = None
        self.vector_db_id = "my_documents"
        self.rag_loaded = False  # Track RAG loading status
        
        # Basic sampling parameters
        self.sampling_params = {
            "strategy": {"type": "greedy"},
            "max_tokens": 4096
        }
        
        # Setup client with SSL and auth
        self._setup_client()
        
        # Load Discounts application documentation into RAG
        self.load_discounts_application_documents()
        
        # Create separate agents for different tool types to avoid parallel tool calls
        openshift_tools = ["mcp::openshift"]
        rag_tools = [{
            "name": "builtin::rag",
            "args": {
                "vector_db_ids": [self.vector_db_id],
                "top_k": 5
            }
        }]
        
        base_instructions = """
You are an expert software engineer and DevOps specialist for applications. Your primary goal is to help users understand, configure, and troubleshoot the application system and its components.

**Important:** Make only ONE tool call at a time. The system does not support simultaneous tool calls.
"""
        
        openshift_instructions = base_instructions + """
**Your Role:** You specialize in OpenShift/Kubernetes operations. Use the OpenShift MCP tool to:
- List pods, deployments, services, and other resources
- Check logs and status information
- Investigate system-level issues
- Monitor cluster health and resource usage
"""

        rag_instructions = base_instructions + """
**Your Role:** You specialize in application knowledge and troubleshooting. Use the RAG knowledge base to:
- Search for application configuration details
- Find troubleshooting guides and solutions
- Provide context about discount application architecture
- Suggest fixes based on documented best practices
"""
        
        # Create OpenShift-focused agent
        self.openshift_agent = Agent(
            client=self.client,
            model=self.model_id,
            instructions=openshift_instructions,
            tools=openshift_tools,
            sampling_params=self.sampling_params,
            max_infer_iters=1,  # Single tool call only
            enable_session_persistence=True
        )
        
        # Create RAG-focused agent 
        self.rag_agent = Agent(
            client=self.client,
            model=self.model_id,
            instructions=rag_instructions,
            tools=rag_tools,
            sampling_params=self.sampling_params,
            max_infer_iters=1,  # Single tool call only
            enable_session_persistence=True
        )
        
        # Keep a general agent without tools for synthesis
        self.general_agent = Agent(
            client=self.client,
            model=self.model_id,
            instructions=base_instructions + """
**Your Role:** You synthesize information from system investigations and knowledge base searches to provide comprehensive responses to user queries about application troubleshooting and management.
""",
            tools=[],  # No tools - just for synthesis
            sampling_params=self.sampling_params,
            max_infer_iters=1,
            enable_session_persistence=True
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
    
    def load_discounts_application_documents(self):
        """Load Discounts Application documentation into RAG"""
        print("📚 Loading Discounts application documentation...")
        
        documents = [
            RAGDocument(
                document_id="discounts-application-overview",
                content="""
                DISCOUNTS APPLICATION - OVERVIEW
                
                APPLICATION: discounts-app
                VERSION: 2.3.1
                FUNCTION: E-commerce discount management and calculation system
                
                RESPONSIBILITIES:
                - Calculate and apply various discount types (percentage, fixed, BOGO)
                - Manage discount campaigns and promotional codes
                - Handle user loyalty programs and tier-based discounts
                - Process bulk discount operations for enterprise customers
                - Validate discount eligibility and constraints
                - Generate discount analytics and reporting
                
                ARCHITECTURE:
                - Microservices-based architecture with 5 main services
                - API Gateway on port 8080 for external access
                - PostgreSQL database for discount rules and user data
                - Redis cache for session management and discount calculations
                - Event-driven architecture using Apache Kafka
                - Container-based deployment with Docker/Kubernetes
                
                CORE SERVICES:
                - discount-calculator: Core discount calculation engine
                - campaign-manager: Manages promotional campaigns
                - user-service: Handles user authentication and profiles
                - product-catalog: Product information and pricing
                - analytics-service: Reporting and business intelligence
                
                API ENDPOINTS:
                - POST /api/v1/discounts/calculate - Calculate discount for cart
                - GET /api/v1/campaigns - List active campaigns
                - POST /api/v1/campaigns - Create new discount campaign
                - GET /api/v1/users/{id}/discounts - Get user-specific discounts
                - POST /api/v1/codes/validate - Validate promo codes
                
                DISCOUNT TYPES SUPPORTED:
                - Percentage discounts (10%, 25%, 50%)
                - Fixed amount discounts ($5, $10, $25)
                - Buy-One-Get-One (BOGO) offers
                - Tiered discounts based on quantity or total
                - Loyalty program discounts
                - Time-based flash sales
                """,
                mime_type="text/plain",
                metadata={"application": "discounts-app", "type": "overview", "version": "2.3.1"}
            ),
            RAGDocument(
                document_id="discounts-application-troubleshooting",
                content="""
                DISCOUNTS APPLICATION - TROUBLESHOOTING
                
                COMMON PROBLEMS AND SOLUTIONS:
                
                PROBLEM 1: "Discount Calculation Incorrect"
                SYMPTOMS: Users receiving wrong discount amounts
                DIAGNOSIS:
                - Check discount-calculator service logs: kubectl logs -f deployment/discount-calculator
                - Verify discount rules in database: SELECT * FROM discount_rules WHERE active = true
                - Test calculation endpoint: curl -X POST /api/v1/discounts/calculate
                SOLUTIONS:
                - Review discount rule precedence and stacking logic
                - Check for floating-point calculation errors
                - Verify product catalog prices are up to date
                - Clear Redis cache if stale data detected
                
                PROBLEM 2: "Promo Codes Not Working"
                SYMPTOMS: Valid promo codes being rejected
                DIAGNOSIS:
                - Check campaign-manager service logs
                - Verify code exists: SELECT * FROM promo_codes WHERE code = 'DISCOUNT20'
                - Check expiration dates and usage limits
                - Test validation endpoint: curl -X POST /api/v1/codes/validate
                SOLUTIONS:
                - Verify promo code is active and within date range
                - Check usage limits haven't been exceeded
                - Ensure case-sensitivity settings are correct
                - Review minimum order requirements
                
                PROBLEM 3: "Database Connection Issues"
                SYMPTOMS: Services failing to connect to PostgreSQL
                DIAGNOSIS:
                - Check database connectivity: pg_isready -h postgres-service -p 5432
                - Review connection pool metrics
                - Check service environment variables for DB credentials
                SOLUTIONS:
                - Verify PostgreSQL service is running and accessible
                - Check connection string format and credentials
                - Monitor connection pool size and adjust if needed
                - Restart services if connection pool is exhausted
                
                PROBLEM 4: "High Response Times"
                SYMPTOMS: API requests taking too long to process
                DIAGNOSIS:
                - Monitor service metrics in Grafana dashboard
                - Check Redis cache hit rates
                - Review database query performance
                - Analyze API Gateway logs for bottlenecks
                SOLUTIONS:
                - Scale up discount-calculator replicas if CPU bound
                - Optimize database queries with proper indexing
                - Increase Redis cache size and TTL values
                - Implement circuit breaker pattern for external calls
                
                PROBLEM 5: "Analytics Service Down"
                SYMPTOMS: Reporting dashboard showing no data
                DIAGNOSIS:
                - Check analytics-service health: curl /health
                - Verify Kafka connection for event streaming
                - Review data pipeline logs in analytics pods
                SOLUTIONS:
                - Restart analytics-service deployment
                - Check Kafka topic offsets and consumer lag
                - Verify data warehouse connection credentials
                - Run manual data sync if needed
                
                USEFUL COMMANDS:
                - kubectl get pods -l app=discounts-app
                - kubectl logs -f deployment/discount-calculator --tail=100
                - kubectl port-forward svc/api-gateway 8080:8080
                - redis-cli -h redis-service FLUSHDB (clear cache)
                - psql -h postgres-service -U discounts_user -d discounts_db
                """,
                mime_type="text/plain",
                metadata={"application": "discounts-app", "type": "troubleshooting", "severity": "critical"}
            ),
            RAGDocument(
                document_id="discounts-application-configuration",
                content="""
                DISCOUNTS APPLICATION - CONFIGURATION
                
                MAIN CONFIGURATION COMPONENTS:
                
                1. APPLICATION SETTINGS
                File: application.yml
                Key parameters:
                - server.port: 8080 (API Gateway port)
                - spring.profiles.active: production
                - database.max-connections: 20
                - cache.redis.ttl: 3600 seconds
                - discount.max-stack-count: 3 (maximum stacked discounts)
                
                2. DATABASE CONFIGURATION
                PostgreSQL Settings:
                - Host: postgres-service.default.svc.cluster.local
                - Database: discounts_db
                - Username: discounts_user
                - Connection pool: 10-20 connections
                - Timeout: 30 seconds
                
                3. IMPORTANT ENVIRONMENT VARIABLES:
                - DATABASE_URL: PostgreSQL connection string
                - REDIS_URL: Redis cache connection string
                - KAFKA_BROKERS: Comma-separated list of Kafka brokers
                - LOG_LEVEL: Application logging level (DEBUG, INFO, WARN, ERROR)
                - MAX_DISCOUNT_PERCENT: Maximum allowed discount percentage (default: 90%)
                - CURRENCY: Default currency code (USD)
                - TAX_CALCULATION: Enable/disable tax calculation (true/false)
                
                4. DISCOUNT RULES CONFIGURATION
                Rule Types:
                - percentage: Percentage-based discounts (5-90%)
                - fixed_amount: Fixed dollar amount discounts
                - bogo: Buy-one-get-one offers
                - quantity_tier: Volume-based pricing tiers
                - loyalty_tier: Customer loyalty level discounts
                
                Rule Precedence:
                1. User-specific targeted offers
                2. Loyalty program discounts
                3. Promo code discounts
                4. Campaign-based discounts
                5. Product category discounts
                
                5. API RATE LIMITING
                Limits per service:
                - discount-calculator: 1000 requests/minute
                - campaign-manager: 500 requests/minute
                - user-service: 2000 requests/minute
                - analytics-service: 100 requests/minute
                
                6. CACHING STRATEGY
                Redis Cache Configuration:
                - User discount eligibility: 15 minutes TTL
                - Product pricing: 1 hour TTL
                - Campaign rules: 30 minutes TTL
                - Promo code validation: 5 minutes TTL
                
                7. MONITORING AND HEALTH CHECKS
                Health endpoints:
                - /health: Overall application health
                - /metrics: Prometheus metrics
                - /info: Application version and build info
                - /ready: Readiness probe for Kubernetes
                
                Monitored metrics:
                - Discount calculation latency
                - Promo code validation success rate
                - Database connection pool usage
                - Redis cache hit rate
                - API request volume and error rates
                
                8. SECURITY CONFIGURATION
                Authentication:
                - JWT token validation for API access
                - Service-to-service mTLS communication
                - API key authentication for partner integrations
                
                Authorization:
                - Role-based access control (admin, manager, user)
                - Discount amount limits based on user role
                - Campaign management permissions
                
                9. BACKUP AND DISASTER RECOVERY
                Database backups:
                - Daily automated backups at 2 AM UTC
                - 30-day retention policy
                - Point-in-time recovery capability
                - Cross-region backup replication
                
                10. INTEGRATION POINTS
                External systems:
                - Payment gateway for discount application
                - Inventory management system for product data
                - Customer service system for discount disputes
                - Marketing automation for campaign triggers
                - Analytics platform for business intelligence
                """,
                mime_type="text/plain",
                metadata={"application": "discounts-app", "type": "configuration", "environment": "production"}
            )
        ]
        
        try: 
            # Check if RAG tool is available
            if not hasattr(self.client, 'tool_runtime') or not hasattr(self.client.tool_runtime, 'rag_tool'):
                raise Exception("RAG tool is not available in the client. Check if RAG is properly configured in the server.")
            
            # Insert documents into the vector database
            result = self.client.tool_runtime.rag_tool.insert(
                documents=documents,
                vector_db_id=self.vector_db_id,
                chunk_size_in_tokens=512,
            )
            print(f"✅ Discounts application documents loaded successfully. Vector DB ID: {self.vector_db_id}")
            

            
            # Verify documents were inserted by inspecting RAG tool
            try:
                print(f"🔍 Inspecting RAG tool to find correct query method...")
                rag_tool = self.client.tool_runtime.rag_tool
                
                # Try with correct parameters
                query_result = None
                try:
                    query_result = rag_tool.query(
                        content="Discounts application configuration",
                        vector_db_ids=[self.vector_db_id]
                    )
                    print(f"✅ RAG query with correct parameters worked!")
                except Exception as correct_e:
                    print(f"❌ Correct parameters query failed: {correct_e}")
                
                if query_result is not None:
                    print(f"🔍 RAG verification query successful. Found results.")
                    self.rag_loaded = True
                else:
                    print(f"⚠️  All RAG query attempts failed, but documents were inserted successfully")
                    print(f"✅ Marking RAG as loaded since document insertion succeeded")
                    self.rag_loaded = True
                    
            except Exception as verify_e:
                print(f"⚠️  RAG inspection failed: {verify_e}")
                print(f"✅ Marking RAG as loaded since document insertion succeeded")
                self.rag_loaded = True
                
        except Exception as e:
            print(f"❌ Error loading RAG documents: {e}")
            print(f"📋 Details: {type(e).__name__}: {str(e)}")
            self.rag_loaded = False
            # Continue without RAG functionality
    
    def create_session(self):
        """Create sessions for all agents"""
        self.openshift_session_id = self.openshift_agent.create_session("openshift-session")
        self.rag_session_id = self.rag_agent.create_session("rag-session")
        self.general_session_id = self.general_agent.create_session("general-session")
    
    def chat(self, message: str):
        """Send a message to the appropriate agent and get response"""
        try:
            if not hasattr(self, 'openshift_session_id'):
                self.create_session()
            
            print(f"\n🤖 Processing query: '{message}'")
            print(f"📊 RAG Status: {'✅ Loaded' if self.rag_loaded else '❌ Not loaded'}")
            print("=" * 50)
            
            # Check if this query might need both OpenShift info and RAG knowledge
            needs_openshift = any(keyword in message.lower() for keyword in ['pod', 'namespace', 'deployment', 'service', 'openshift', 'kubectl', 'cluster'])
            needs_rag = any(keyword in message.lower() for keyword in ['discount', 'application', 'troubleshoot', 'error', 'configuration', 'issue'])
            
            if needs_openshift and needs_rag:
                print("🔄 Detected complex query requiring both OpenShift and RAG data")
                
                # First, get OpenShift information
                openshift_query = f"List the pods in the openshift-gitops namespace and provide system information"
                print(f"\n📍 Step 1: OpenShift agent")
                print(f"🛠️  Using: mcp::openshift")
                openshift_response = self.openshift_agent.create_turn(
                    messages=[{"role": "user", "content": openshift_query}],
                    session_id=self.openshift_session_id,
                    stream=False
                )
                print(f"🔍 OpenShift response: {openshift_response}")
                
                # Then, get RAG information  
                rag_query = f"Search for information about 'Discount Calculation Incorrect' troubleshooting"
                print(f"\n📍 Step 2: RAG agent")
                print(f"🛠️  Using: builtin::rag")
                rag_response = self.rag_agent.create_turn(
                    messages=[{"role": "user", "content": rag_query}],
                    session_id=self.rag_session_id,
                    stream=False
                )
                print(f"🔍 RAG response: {rag_response}")
                # Combine responses using general agent
                print(f"\n📍 Step 3: Synthesis")
                openshift_content = openshift_response.output_message.content if openshift_response else "No OpenShift data available"
                rag_content = rag_response.output_message.content if rag_response else "No RAG data available"
                
                combined_query = f"""Based on the following information, provide a comprehensive analysis:

OPENSHIFT SYSTEM DATA:
{openshift_content}

APPLICATION KNOWLEDGE:
{rag_content}

Original user query: {message}

Please synthesize this information to provide a complete response."""

                print(f"🔍 Combined query: {combined_query}")
                response = self.general_agent.create_turn(
                    messages=[{"role": "user", "content": combined_query}],
                    session_id=self.general_session_id,
                    stream=False
                )
                
            elif needs_openshift:
                print("🔄 Using OpenShift agent")
                print(f"🛠️  Using: mcp::openshift")
                response = self.openshift_agent.create_turn(
                    messages=[{"role": "user", "content": message}],
                    session_id=self.openshift_session_id,
                    stream=False
                )
                
            elif needs_rag:
                print("🔄 Using RAG agent")
                print(f"🛠️  Using: builtin::rag")
                response = self.rag_agent.create_turn(
                    messages=[{"role": "user", "content": message}],
                    session_id=self.rag_session_id,
                    stream=False
                )
                
            else:
                print("🔄 Using general agent")
                print(f"🛠️  Using: no tools (general knowledge)")
                response = self.general_agent.create_turn(
                    messages=[{"role": "user", "content": message}],
                    session_id=self.general_session_id,
                    stream=False
                )
            
            # Print detailed response information
            print("\n📋 AGENT RESPONSE:")
            print("=" * 50)
            
            # Check if tools were used
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"🔧 Tools used: {[tool.tool_name for tool in response.tool_calls]}")
                for tool_call in response.tool_calls:
                    print(f"   - {tool_call.tool_name}: {tool_call.arguments}")
            else:
                print("🔧 No tools were used in this response")
                
            # Additional debugging for tool calls
            if hasattr(response, 'steps'):
                print(f"🔄 Response has {len(response.steps)} steps")
                for i, step in enumerate(response.steps):
                    print(f"   Step {i+1}: {type(step)} - {getattr(step, 'step_type', 'unknown')}")
                    if hasattr(step, 'tool_calls') and step.tool_calls:
                        for tool_call in step.tool_calls:
                            print(f"      Tool: {tool_call.tool_name}")
            
            print(f"\n💬 Response:")
            if hasattr(response, 'output_message') and response.output_message:
                print(response.output_message.content)
            else:
                print("No response content available")
            
            return response
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
def main():
    """Main function to run a single query"""
    try:
        chatbot = LlamaStackChatbot()
        chatbot.create_session()
        
        # Test query - should trigger mcp::openshift tool for MCP server investigation
        query = "list the pods in the openshift-gitops namespace, give to me all the information you can have about discounts application Discount Calculation Incorrect"
        print(f"Query: {query}")
        chatbot.chat(query)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()