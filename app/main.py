"""
Streamlit UI for Insurance Claims Agent
Allows users to write or upload claim details
"""
import streamlit as st
import json
import sys
import logging
import io
from datetime import datetime
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))

# Initialize app components
from app.agent.graph import claims_graph
from app.database.vector_store import policy_store
from app.utils.logger import logger
from app.utils.config import config


# Custom log handler for Streamlit display
class StreamlitLogHandler(logging.Handler):
    """Log handler that stores messages in session state for UI display"""
    def emit(self, record):
        log_entry = self.format(record)
        # Get current execution ID
        execution_id = st.session_state.get("current_execution_id")
        if execution_id:
            if "execution_logs" not in st.session_state:
                st.session_state.execution_logs = {}
            if execution_id not in st.session_state.execution_logs:
                st.session_state.execution_logs[execution_id] = []
            # Avoid repeating the same log entry consecutively
            exec_list = st.session_state.execution_logs[execution_id]
            if not exec_list or exec_list[-1] != log_entry:
                exec_list.append(log_entry)
                st.session_state.execution_logs[execution_id] = exec_list


# Add Streamlit handler to logger
if not any(isinstance(h, StreamlitLogHandler) for h in logger.handlers):
    streamlit_handler = StreamlitLogHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    streamlit_handler.setFormatter(formatter)
    logger.addHandler(streamlit_handler)


# Page configuration
st.set_page_config(
    page_title="Insurance Claims Processing Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)


def initialize_vector_store():
    """Initialize vector store with policy documents"""
    if st.session_state.get("vector_store_initialized"):
        return
    
    with st.spinner("🔄 Loading policy documents into vector store..."):
        try:
            policy_store.populate_from_pdf()
            st.session_state.vector_store_initialized = True
            logger.info("Vector store initialized successfully")
        except Exception as e:
            st.error(f"Error initializing vector store: {e}")
            logger.error(f"Vector store initialization failed: {e}")


def display_logs():
    """Display captured logs for current execution only"""
    execution_id = st.session_state.get("current_execution_id")
    if execution_id and "execution_logs" in st.session_state:
        logs = st.session_state.execution_logs.get(execution_id, [])
        if logs:
            with st.expander("📋 Processing Logs", expanded=False):
                logs_text = "\n".join(logs)
                st.code(logs_text, language="log")


def start_execution():
    """Start a new execution and create a unique execution ID"""
    import uuid
    execution_id = str(uuid.uuid4())
    st.session_state.current_execution_id = execution_id
    # Reset execution_logs so only this execution's logs are kept
    st.session_state.execution_logs = {}
    st.session_state.execution_logs[execution_id] = []
    return execution_id


def end_execution():
    """End current execution"""
    st.session_state.current_execution_id = None


def process_claim(claim_data: dict) -> dict:
    """Process claim through LangGraph workflow"""
    # Start tracking this execution
    start_execution()
    
    logger.info(f"=" * 80)
    logger.info(f"🚀 NEW CLAIM PROCESSING REQUEST")
    logger.info(f"Claim ID: {claim_data.get('claim_id', 'N/A')}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"=" * 80)
    
    try:
        # Convert claim data to JSON string
        claim_json = json.dumps(claim_data)
        
        # Initialize state
        initial_state = {
            "claim_json": claim_json,
            "current_step": "initialized"
        }
        
        # Run through LangGraph
        logger.info("🎯 Invoking LangGraph workflow...")
        final_state = claims_graph.invoke(initial_state)
        
        logger.info(f"✅ Workflow completed. Final decision: {final_state.get('final_decision', 'N/A')}")
        logger.info(f"=" * 80)
        
        return final_state
    
    except Exception as e:
        logger.error(f"❌ Error processing claim: {e}")
        logger.error(f"=" * 80)
        raise e


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<div class="main-header">🏥 Insurance Claims Processing Agent</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Initialize vector store
    initialize_vector_store()
    
    # Sidebar
    with st.sidebar:
        st.header("ℹ️ About")
        st.write("""
        This AI agent automatically processes auto insurance claims using:
        - **LangGraph** for workflow orchestration
        - **RAG** for policy retrieval
        - **GPT-4o-mini** for intelligent decision making
        """)
        
        st.header("📊 System Status")
        st.metric("Vector Store", "✅ Active" if st.session_state.get("vector_store_initialized") else "⏳ Loading")
        st.metric("Model", config.model_name)
        st.metric("Policy Documents", policy_store.collection.count() if st.session_state.get("vector_store_initialized") else 0)
        
        st.markdown("---")
        st.caption(f"Powered by LangChain & LangGraph")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 Manual Entry", "📤 Upload JSON", "📚 Logs Viewer"])
    
    # === TAB 1: Manual Entry ===
    with tab1:
        st.subheader("Enter Claim Details Manually")
        
        col1, col2 = st.columns(2)
        
        with col1:
            claim_id = st.text_input("Claim ID *", placeholder="e.g., CLM-2026-001")
            policy_holder = st.text_input("Policy Holder Name *", placeholder="e.g., John Doe")
            vendor_name = st.text_input("Vendor/Service Provider *", placeholder="e.g., AutoFix Garage")
        
        with col2:
            total_amount = st.number_input("Total Claim Amount ($) *", min_value=0.0, step=10.0, value=0.0)
        
        st.markdown("**Invoice Items**")
        
        # Dynamic invoice items
        if "invoice_items" not in st.session_state:
            st.session_state.invoice_items = [{"item": "", "amount": 0.0}]
        
        for i, item in enumerate(st.session_state.invoice_items):
            col_item, col_amount, col_remove = st.columns([3, 2, 1])
            
            with col_item:
                item_desc = st.text_input(f"Item Description", value=item["item"], key=f"item_desc_{i}", placeholder="e.g., Engine Repair")
            
            with col_amount:
                item_amount = st.number_input(f"Amount ($)", value=item["amount"], min_value=0.0, step=10.0, key=f"item_amount_{i}")
            
            with col_remove:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.invoice_items.pop(i)
                    st.rerun()
            
            st.session_state.invoice_items[i] = {"item": item_desc, "amount": item_amount}
        
        if st.button("➕ Add Another Item"):
            st.session_state.invoice_items.append({"item": "", "amount": 0.0})
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🚀 Process Claim", type="primary", use_container_width=True):
            # Validate inputs
            if not claim_id or not policy_holder or not vendor_name:
                st.error("❌ Please fill in all required fields marked with *")
                return
            
            if total_amount <= 0:
                st.error("❌ Claim amount must be greater than 0")
                return
            
            # Build claim data
            claim_data = {
                "claim_id": claim_id,
                "policy_holder": policy_holder,
                "vendor_name": vendor_name,
                "invoice_items": [item for item in st.session_state.invoice_items if item["item"]],
                "total_amount": total_amount
            }
            
            # Process claim
            with st.spinner("🔄 Processing claim through AI agent..."):
                try:
                    result = process_claim(claim_data)
                    
                    # Display results
                    st.success("✅ Claim processing completed!")
                    
                    # Display logs
                    display_logs()
                    
                    # Decision box
                    decision = result.get("final_decision", "UNKNOWN")
                    reasoning = result.get("final_reasoning", "No reasoning provided")
                    
                    if decision == "APPROVED":
                        st.markdown(f'<div class="success-box"><h3>✅ CLAIM APPROVED</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                    elif decision == "DENIED" or decision == "INVALID":
                        st.markdown(f'<div class="error-box"><h3>❌ CLAIM DENIED</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="warning-box"><h3>⚠️ REQUIRES MANUAL REVIEW</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                    
                    # Detailed breakdown
                    with st.expander("📋 View Detailed Processing Steps"):
                        st.json({
                            "claim_id": result.get("claim_id"),
                            "is_valid": result.get("is_valid"),
                            "validation_reason": result.get("validation_reason", "Valid"),
                            "policy_queries_generated": len(result.get("policy_queries", [])),
                            "recommendation": result.get("recommendation"),
                            "recommendation_reasoning": result.get("recommendation_reasoning"),
                            "price_check_result": result.get("price_check_result"),
                            "final_decision": result.get("final_decision"),
                            "final_reasoning": result.get("final_reasoning")
                        })
                
                except Exception as e:
                    st.error(f"❌ Error processing claim: {str(e)}")
                    logger.error(f"Claim processing error: {e}")
                    display_logs()
    
    # === TAB 2: Upload JSON ===
    with tab2:
        st.subheader("Upload Claim JSON File")
        
        uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])
        
        if uploaded_file is not None:
            try:
                claim_data = json.load(uploaded_file)
                
                st.success("✅ File uploaded successfully!")
                st.json(claim_data)
                
                if st.button("🚀 Process Uploaded Claim", type="primary", use_container_width=True):
                    with st.spinner("🔄 Processing claim..."):
                        try:
                            result = process_claim(claim_data)
                            
                            st.success("✅ Claim processing completed!")
                            
                            # Display logs
                            display_logs()
                            
                            decision = result.get("final_decision", "UNKNOWN")
                            reasoning = result.get("final_reasoning", "No reasoning provided")
                            
                            if decision == "APPROVED":
                                st.markdown(f'<div class="success-box"><h3>✅ CLAIM APPROVED</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                            elif decision == "DENIED" or decision == "INVALID":
                                st.markdown(f'<div class="error-box"><h3>❌ CLAIM DENIED</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="warning-box"><h3>⚠️ REQUIRES MANUAL REVIEW</h3><p>{reasoning}</p></div>', unsafe_allow_html=True)
                            
                            with st.expander("📋 View Detailed Processing Steps"):
                                st.json(result)
                        
                        except Exception as e:
                            st.error(f"❌ Error processing claim: {str(e)}")
                            display_logs()
            
            except json.JSONDecodeError:
                st.error("❌ Invalid JSON file. Please upload a valid JSON file.")
    
    # === TAB 3: Logs Viewer ===
    with tab3:
        st.subheader("Logs Viewer")

        # List files from ./logs directory
        from pathlib import Path as _Path
        log_dir = _Path("logs")

        if not log_dir.exists():
            st.info("No `logs` directory found in the workspace.")
        else:
            files = sorted([p.name for p in log_dir.iterdir() if p.is_file()])
            if not files:
                st.info("No log files found in `./logs/`.")
            else:
                selected = st.selectbox("Select log file", files)

                # Read and display the selected file
                file_path = log_dir / selected
                try:
                    with open(file_path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                except Exception as e:
                    st.error(f"Error reading log file: {e}")
                    content = ""

                if content:
                    st.download_button("Download Log File", data=content, file_name=selected, mime="text/plain")
                    st.markdown("### Log Contents")
                    st.code(content, language="log")


if __name__ == "__main__":
    main()
