"""
Multi-Agent Reasoning Chatbot with Streamlit Web Interface
Main Streamlit application for interactive web-based reasoning.
"""

import streamlit as st
import json
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Initialize configuration and logging
from dotenv import load_dotenv
load_dotenv()

from config.logging_config import setup_logging
setup_logging()

from config.openai_client import initialize_client
initialize_client()

from core.agent_init import initialize_agents
from core.blend import blend_responses
from visualization.metrics import metrics_tracker
from utils.utils import get_local_context_for_prompt, append_reasoning_history

# Page config
st.set_page_config(
    page_title="Multi-Agent Reasoning",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .header-container {
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .agent-response {
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid;
        margin-bottom: 10px;
    }
    .agent-response-analyst {
        border-color: #FF6B6B;
        background-color: #FFE5E5;
    }
    .agent-response-creative {
        border-color: #4ECDC4;
        background-color: #E5F9F7;
    }
    .final-response {
        padding: 20px;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        border-radius: 8px;
        font-size: 16px;
        margin: 20px 0;
        width: 100%;
        box-sizing: border-box;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "agents" not in st.session_state:
    st.session_state.agents = initialize_agents()
    st.session_state.history = []
    st.session_state.metrics_data = None
    st.session_state.last_reasoning = None  
    st.session_state.current_results = None 
    st.session_state.refine_outputs = []  # List lưu tất cả refinement loops
    st.session_state.show_feedback = False

# Header
st.markdown("""
    <div class="header-container">
        <h1>Multi-Agent Reasoning System</h1>
        <p>Collaborative AI reasoning with multiple perspectives</p>
    </div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["Reasoning", "Metrics", "History"])

with tab1:
    st.subheader("Multi-Step Reasoning Process")
    
    # Input
    user_prompt = st.text_area(
        "Enter your question or prompt:",
        height=100,
        placeholder="Type your question here...",
        key="user_prompt"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        run_button = st.button("Run Reasoning", use_container_width=True)
    with col2:
        clear_context = st.checkbox("Clear agent context after reasoning")
    
    if run_button and user_prompt and len(user_prompt) > 4:
        # Reset feedback state for new reasoning
        st.session_state.show_feedback = False
        st.session_state.refine_outputs = []  # Reset list refinement loops
        
        # Create a container for all results
        results_container = st.container()
        progress_bar = st.progress(0)
        status_container = st.container()
        
        try:
            # Get local context
            local_context = get_local_context_for_prompt(user_prompt, max_records=2)
            extended_prompt = f"{user_prompt}\n\n{local_context}" if local_context else user_prompt
            
            # Step 1: Discuss
            status_container.info("Step 1: Agents Discussing...")
            progress_bar.progress(15)
            opinions = {}
            start_discuss = time.time()
            
            for agent in st.session_state.agents:
                opinion, duration = agent.discuss(extended_prompt)
                opinions[agent.name] = opinion
            
            discuss_duration = time.time() - start_discuss
            metrics_tracker.record_step_time("Discuss", discuss_duration)
            
            # Display Step 1 Results
            with results_container:
                with st.expander("Step 1: Initial Discussion - Click to view responses"):
                    cols = st.columns(len(st.session_state.agents))
                    for col, agent in zip(cols, st.session_state.agents):
                        with col:
                            st.write(f"**{agent.name}:**")
                            st.write(opinions[agent.name])
            
            # Step 2: Verify
            status_container.info("Step 2: Verifying Responses...")
            progress_bar.progress(30)
            verified_opinions = {}
            start_verify = time.time()
            
            with ThreadPoolExecutor() as executor:
                futures = {executor.submit(lambda a=agent: (a, a.verify(opinions[a.name]))): agent 
                          for agent in st.session_state.agents}
                for future in futures:
                    agent, (verified_opinion, _) = future.result()
                    verified_opinions[agent.name] = verified_opinion
            
            verify_duration = time.time() - start_verify
            metrics_tracker.record_step_time("Verify", verify_duration)
            
            # Display Step 2 Results
            with results_container:
                with st.expander("Step 2: Verification - Click to view responses"):
                    cols = st.columns(len(st.session_state.agents))
                    for col, agent in zip(cols, st.session_state.agents):
                        with col:
                            st.write(f"**{agent.name}:**")
                            st.write(verified_opinions[agent.name])
            
            # Step 3: Critique
            status_container.info("Step 3: Cross-Critique...")
            progress_bar.progress(45)
            critiques = {}
            start_critique = time.time()
            
            num_agents = len(st.session_state.agents)
            for i, agent in enumerate(st.session_state.agents):
                other_agent = st.session_state.agents[(i + 1) % num_agents]
                critique, _ = agent.critique(verified_opinions[other_agent.name])
                critiques[agent.name] = critique
            
            critique_duration = time.time() - start_critique
            metrics_tracker.record_step_time("Critique", critique_duration)
            
            # Display Step 3 Results
            with results_container:
                with st.expander("Step 3: Critiques - Click to view responses"):
                    cols = st.columns(len(st.session_state.agents))
                    for col, agent in zip(cols, st.session_state.agents):
                        with col:
                            st.write(f"**{agent.name}:**")
                            st.write(critiques[agent.name])
            
            # Step 4: Refine
            status_container.info("Step 4: Refining Responses...")
            progress_bar.progress(65)
            refined_opinions = {}
            start_refine = time.time()
            
            for agent in st.session_state.agents:
                refined_opinion, _ = agent.refine(opinions[agent.name])
                refined_opinions[agent.name] = refined_opinion
            
            refine_duration = time.time() - start_refine
            metrics_tracker.record_step_time("Refine", refine_duration)
            
            # Display Step 4 Results
            with results_container:
                with st.expander("Step 4: Refinement - Click to view responses"):
                    cols = st.columns(len(st.session_state.agents))
                    for col, agent in zip(cols, st.session_state.agents):
                        with col:
                            st.write(f"**{agent.name}:**")
                            st.write(refined_opinions[agent.name])
            
            # Step 5: Blend
            status_container.info("Step 5: Blending Optimal Response...")
            progress_bar.progress(85)
            agent_responses = [(agent.name, refined_opinions[agent.name]) for agent in st.session_state.agents]
            start_blend = time.time()
            optimal_response = blend_responses(agent_responses, user_prompt)
            blend_duration = time.time() - start_blend
            metrics_tracker.record_step_time("Blend", blend_duration)
            
            progress_bar.progress(100)
            status_container.success("Reasoning Complete!")
            
            st.divider()
            
            # Display Step 5 Results
            with results_container:
                st.subheader("Step 5: Final Blended Response")
                st.markdown(f"""
                    <div class="final-response">
                    {optimal_response}
                    </div>
                """, unsafe_allow_html=True)
            
            # Lưu kết quả vào session state để giữ sau khi rerun
            st.session_state.current_results = {
                "user_prompt": user_prompt,
                "extended_prompt": extended_prompt,
                "opinions": opinions,
                "verified_opinions": verified_opinions,
                "critiques": critiques,
                "refined_opinions": refined_opinions,
                "optimal_response": optimal_response
            }
            
            # Save to history
            record = {
                "timestamp": datetime.now().isoformat(),
                "user_prompt": user_prompt,
                "final_response": optimal_response,
                "agent_responses": refined_opinions,
                "critiques": critiques,
                "user_feedback": "pending"
            }
            st.session_state.history.append(record)
            append_reasoning_history({
                "timestamp": record["timestamp"],
                "user_prompt": user_prompt,
                "final_response": optimal_response,
                "user_feedback": "web"
            })
            
            # Lưu vào session state để prepare cho Feedback section
            st.session_state.show_feedback = True
            st.rerun()
            
        except Exception as e:
            st.error(f"Error during reasoning: {str(e)}")
    
    elif run_button and len(user_prompt) <= 4:
        st.warning("Please enter a prompt with more than 4 characters")
    
    elif st.session_state.current_results and st.session_state.get("show_feedback", False):
        results = st.session_state.current_results
        
        # Display Step 1-5 from session state
        st.subheader("Step 1-5: Reasoning Process")
        
        # Step 1
        with st.expander("Step 1: Initial Discussion - Click to view responses"):
            cols = st.columns(len(st.session_state.agents))
            for col, agent in zip(cols, st.session_state.agents):
                with col:
                    st.write(f"**{agent.name}:**")
                    st.write(results["opinions"].get(agent.name, "N/A"))
        
        # Step 2
        with st.expander("Step 2: Verification - Click to view responses"):
            cols = st.columns(len(st.session_state.agents))
            for col, agent in zip(cols, st.session_state.agents):
                with col:
                    st.write(f"**{agent.name}:**")
                    st.write(results["verified_opinions"].get(agent.name, "N/A"))
        
        # Step 3
        with st.expander("Step 3: Critiques - Click to view responses"):
            cols = st.columns(len(st.session_state.agents))
            for col, agent in zip(cols, st.session_state.agents):
                with col:
                    st.write(f"**{agent.name}:**")
                    st.write(results["critiques"].get(agent.name, "N/A"))
        
        # Step 4
        with st.expander("Step 4: Refinement - Click to view responses"):
            cols = st.columns(len(st.session_state.agents))
            for col, agent in zip(cols, st.session_state.agents):
                with col:
                    st.write(f"**{agent.name}:**")
                    st.write(results["refined_opinions"].get(agent.name, "N/A"))
        
        # Step 5
        st.write("**Step 5: Final Blended Response**")
        st.markdown(f"""
            <div class="final-response">
            {results["optimal_response"]}
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Hiển thị tất cả Refine Loops nếu có
        if st.session_state.refine_outputs:
            st.divider()
            st.subheader(f"Refinement Loops ({len(st.session_state.refine_outputs)} loops)")
            
            for refine_data in st.session_state.refine_outputs:
                st.info(f"Loop {refine_data['loop_number']}: {refine_data['feedback_reason']}")
                
                # Hiển thị Step 4 Refined (Loop)
                st.write(f"**Step 4 - Refined Agent Responses (Loop {refine_data['loop_number']}):**")
                cols_refined = st.columns(len(st.session_state.agents))
                for col, agent in zip(cols_refined, st.session_state.agents):
                    with col:
                        st.write(f"**{agent.name}:**")
                        with st.expander(f"View Loop {refine_data['loop_number']}", expanded=False):
                            st.write(refine_data["refined_opinions_new"][agent.name])
                
                st.divider()
                
                # Comparison
                st.subheader(f"So sánh Kết quả (Loop {refine_data['loop_number']})")
                col_comp1, col_comp2 = st.columns(2)
                with col_comp1:
                    st.write("**Before Loop:**")
                    st.write(refine_data["optimal_response_old"])
                with col_comp2:
                    st.write(f"**After Loop {refine_data['loop_number']}:**")
                    st.markdown(f"""
                        <div class="final-response">
                        {refine_data["optimal_response_new"]}
                        </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
        else:
            st.subheader("Previous Results (Click 'Run Reasoning' to start new reasoning)")
            
            with st.expander("View Previous Results", expanded=False):
                st.write("**Question:**")
                st.write(results["user_prompt"])
        
        # Feedback section
        st.divider()
        st.subheader("Feedback")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            helpful = st.radio("Was this helpful?", ["Yes", "No", "Neutral"], horizontal=True, key="feedback_radio_display")
        
        # Nếu chọn "No", hiển thị input và button Refine
        if helpful == "No":
            st.warning("Vui lòng nhập lý do để chúng tôi cải thiện phản hồi")
            feedback_reason = st.text_area("Lý do tại sao phản hồi không tốt?", placeholder="Ví dụ: Cần chi tiết hơn, Không trả lời đúng câu hỏi, ...", height=80, key="feedback_reason_display")
            
            col_refine1, col_refine2, col_refine3 = st.columns([1, 1, 2])
            with col_refine1:
                if st.button("Refine", use_container_width=True, key="refine_btn_display"):
                    if feedback_reason.strip():
                        refined_opinions = results["refined_opinions"]
                        optimal_response = results["optimal_response"]
                        user_prompt = results["user_prompt"]
                        
                        st.info("Đang refine dựa trên feedback của bạn...")
                        progress_bar_refine = st.progress(0)
                        status_container_refine = st.container()
                        
                        status_container_refine.info("Step 4 (Refinement Loop): Refining Responses with feedback...")
                        progress_bar_refine.progress(80)
                        
                        refined_opinions_new = {}
                        start_refine = time.time()
                        
                        refinement_context = f"\n\nPhản hồi từ người dùng: {feedback_reason}\n\nVui lòng cải thiện phản hồi dựa trên feedback này."
                        
                        for agent in st.session_state.agents:
                            refine_input = refined_opinions[agent.name] + refinement_context
                            refined_opinion, _ = agent.refine(refine_input)
                            refined_opinions_new[agent.name] = refined_opinion
                        
                        refine_duration = time.time() - start_refine
                        metrics_tracker.record_step_time("Refine (Loop)", refine_duration)
                        
                        # Step 5: Blend again
                        status_container_refine.info("Step 5 (Refinement Loop): Re-blending Optimal Response...")
                        progress_bar_refine.progress(90)
                        agent_responses_new = [(agent.name, refined_opinions_new[agent.name]) for agent in st.session_state.agents]
                        start_blend = time.time()
                        optimal_response_new = blend_responses(agent_responses_new, user_prompt)
                        blend_duration = time.time() - start_blend
                        metrics_tracker.record_step_time("Blend (Loop)", blend_duration)
                        
                        progress_bar_refine.progress(100)
                        status_container_refine.success("Refinement Complete!")
                        
                        # Append refined version vào list refinement loops
                        st.session_state.refine_outputs.append({
                            "loop_number": len(st.session_state.refine_outputs) + 1,
                            "feedback_reason": feedback_reason,
                            "refined_opinions_new": refined_opinions_new,
                            "optimal_response_old": optimal_response,
                            "optimal_response_new": optimal_response_new
                        })
                        st.session_state.current_results["refined_opinions"] = refined_opinions_new
                        st.session_state.current_results["optimal_response"] = optimal_response_new
                        
                        st.rerun()
                    else:
                        st.error("Vui lòng nhập lý do trước khi refine")
        
        # Button Save Response
        st.divider()
        col_save1, col_save2 = st.columns([1, 4])
        with col_save1:
            if st.button("Save Response", use_container_width=True, key="save_btn_display"):
                if st.session_state.current_results:
                    results = st.session_state.current_results
                    optimal_response = results["optimal_response"]
                    refined_opinions = results.get("refined_opinions", results["refined_opinions"])
                    user_prompt = results["user_prompt"]
                    critiques = results["critiques"]
                    opinions = results["opinions"]  # Step 1
                    verified_opinions = results["verified_opinions"]  # Step 2
                    
                    # Save final response with all steps
                    record = {
                        "timestamp": datetime.now().isoformat(),
                        "user_prompt": user_prompt,
                        "step1_opinions": opinions,  # Step 1: Initial Discussion
                        "step2_verified": verified_opinions,  # Step 2: Verification
                        "step3_critiques": critiques,  # Step 3: Critique
                        "step4_refined": refined_opinions,  # Step 4: Refinement
                        "step5_final": optimal_response,  # Step 5: Final Blended Response
                        "refinement_loops": st.session_state.refine_outputs,  # All refinement loops if any
                        "user_feedback": helpful,
                        "feedback_reason": feedback_reason if helpful == "No" else None
                    }
                    st.session_state.history.append(record)
                    
                    # Save full record to persistent history file
                    append_reasoning_history(record)
                    
                    st.success("Response saved to history!")
                    
                    # Clear session state
                    st.session_state.current_results = None
                    st.session_state.refine_outputs = []
                    st.session_state.show_feedback = False
            
            st.write("**Final Response:**")
            st.markdown(f"""
                <div class="final-response">
                {results["optimal_response"]}
                </div>
            """, unsafe_allow_html=True)

with tab2:
    st.subheader("Metrics Dashboard")
    
    if metrics_tracker.agent_metrics:
        # Metrics overview
        col1, col2, col3 = st.columns(3)
        
        total_tokens = sum(
            metrics_tracker.agent_metrics[a]['tokens_used'] 
            for a in metrics_tracker.agent_metrics
        )
        total_steps = sum(len(metrics_tracker.step_times.get(step, [])) 
                         for step in metrics_tracker.step_times)
        avg_response_time = sum(
            sum(metrics_tracker.agent_metrics[a]['durations']) 
            for a in metrics_tracker.agent_metrics
        ) / max(len(st.session_state.agents) * total_steps, 1) if total_steps > 0 else 0
        
        with col1:
            st.metric("Total Tokens Used", int(total_tokens))
        with col2:
            st.metric("Total Steps", int(total_steps))
        with col3:
            st.metric("Avg Response Time", f"{avg_response_time:.2f}s")
        
        st.divider()
        
        # Agent metrics
        st.subheader("Agent Performance")
        agents_list = list(metrics_tracker.agent_metrics.keys())
        agent_tokens = [metrics_tracker.agent_metrics[a]['tokens_used'] for a in agents_list]
        agent_durations = [
            sum(metrics_tracker.agent_metrics[a]['durations']) / len(metrics_tracker.agent_metrics[a]['durations'])
            if metrics_tracker.agent_metrics[a]['durations'] else 0
            for a in agents_list
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            df_tokens = pd.DataFrame({
                "Agent": agents_list,
                "Tokens": agent_tokens
            })
            st.bar_chart(df_tokens.set_index("Agent"))
        
        with col2:
            df_duration = pd.DataFrame({
                "Agent": agents_list,
                "Duration (s)": agent_durations
            })
            st.bar_chart(df_duration.set_index("Agent"))
        
        # Step times - Display horizontally
        st.subheader("Step Timeline")
        step_durations = {step: sum(metrics_tracker.step_times[step]) 
                         for step in metrics_tracker.step_times}
        if step_durations:
            # Display step durations as columns
            step_names = list(step_durations.keys())
            step_values = list(step_durations.values())
            
            cols = st.columns(len(step_names))
            for col, step_name, step_value in zip(cols, step_names, step_values):
                with col:
                    st.metric(step_name, f"{step_value:.2f}s")
    else:
        st.info("No metrics available yet. Run reasoning to generate metrics!")

with tab3:
    st.subheader("Conversation History")
    
    if st.session_state.history:
        for idx, record in enumerate(reversed(st.session_state.history), 1):
            with st.expander(f"Query {len(st.session_state.history) - idx + 1}"):
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.caption(record["timestamp"])
                with col2:
                    st.caption("Completed" if record.get("user_feedback") else "Pending")
                
                st.write("**Question:**")
                st.write(record["user_prompt"])
                
                # Handle both new and old record formats
                if record.get("step5_final"):
                    # New format with all steps
                    st.write("**Step 1 - Initial Opinions:**")
                    for agent, opinion in record.get("step1_opinions", {}).items():
                        with st.expander(f"{agent}"):
                            st.write(opinion)
                    
                    st.write("**Step 2 - Verified Opinions:**")
                    for agent, verified in record.get("step2_verified", {}).items():
                        with st.expander(f"{agent}"):
                            st.write(verified)
                    
                    st.write("**Step 3 - Critiques:**")
                    for agent, critique in record.get("step3_critiques", {}).items():
                        with st.expander(f"{agent}"):
                            st.write(critique)
                    
                    st.write("**Step 4 - Refined Responses:**")
                    for agent, refined in record.get("step4_refined", {}).items():
                        with st.expander(f"{agent}"):
                            st.write(refined)
                    
                    st.write("**Step 5 - Final Blended Response:**")
                    st.markdown(f"""
                        <div class="final-response">
                        {record["step5_final"]}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show refinement loops if any
                    if record.get("refinement_loops"):
                        st.write("**Refinement Loops:**")
                        for loop in record["refinement_loops"]:
                            st.write(f"Loop {loop['loop_number']}: {loop['feedback_reason']}")
                else:
                    # Old format (backward compatibility)
                    st.write("**Response:**")
                    st.write(record.get("final_response", "N/A"))
                    
                    if record.get("agent_responses"):
                        st.write("**Agent Responses:**")
                        for agent, response in record["agent_responses"].items():
                            st.write(f"**{agent}:**")
                            st.write(response)
                    
                    if record.get("critiques"):
                        st.write("**Critiques:**")
                        for agent, critique in record["critiques"].items():
                            st.write(f"**{agent}:**")
                            st.write(critique)
    else:
        st.info("No history yet. Start reasoning to build history!")
        
    # Export history
    if st.session_state.history:
        st.divider()
        if st.button("Export History as JSON"):
            history_json = json.dumps(st.session_state.history, indent=2, ensure_ascii=False)
            st.download_button(
                label="Download History",
                data=history_json,
                file_name=f"reasoning_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
