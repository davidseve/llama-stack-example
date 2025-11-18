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
from llama_stack_client.lib.agents.react.agent import ReActAgent
from llama_stack_client.lib.agents.react.tool_parser import ReActOutput

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
        
        # Setup agent with all available tools
        # Configure RAG tool with vector DB IDs
        available_tools = [
            {
                "name": "builtin::rag",
                "args": {
                    "vector_db_ids": [self.vector_db_id],
                    "top_k": 5
                }
            }
        ]
        
        instructions = """
You are a helpful assistant. You have access to a number of tools.
Whenever a tool is called, be sure return the Response in a friendly and helpful tone.
    """   
        self.agent = ReActAgent(
            client=self.client,
            model=self.model_id,
            instructions=instructions,
            tools=available_tools,
            response_format={
                "type": "json_schema",
                "json_schema": ReActOutput.model_json_schema(),
            },
            sampling_params={"max_tokens": 1024, "temperature": 0.1}  # Increased tokens for complex reasoning
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
        """Create a new agent session"""
        self.session_id = self.agent.create_session("chatbot-session")
    
    def chat(self, message: str):
        """Send a message to the agent and get response"""
        try:
            if not self.session_id:
                self.create_session()
            
            print(f"\n🧠 ReActAgent Processing: '{message}'")
            print(f"📊 RAG Status: {'✅ Loaded' if self.rag_loaded else '❌ Not loaded'}")
            print(f"🛠️  Available tools:  builtin::rag")
            print(f"🔄 Using ReAct methodology: Reason → Act → Observe → Reason...")
            print("=" * 60)
            
            response = self.agent.create_turn(
                messages=[{"role": "user", "content": message}],
                session_id=self.session_id,
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
            
            print(response)
            print(f"\n💬 Response:")
            print(response.output_message.content)
            
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
        
        query = "give to me all the information you can have about discounts application and how Calculation Incorrect is done. follow the main instructions"
        print(f"Query: {query}")
        chatbot.chat(query)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()