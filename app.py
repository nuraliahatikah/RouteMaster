import streamlit as st
import json
import os
from routemaster.reply_engine import evaluate_review
from routemaster.integration_hub import build_issue_payload, push_issue_to_produck
st.set_page_config(page_title="RouteMaster — Track 2", page_icon="🦆", layout="wide")

KB_PATH = os.path.join("property_data", "local_knowledge.txt")

st.title("🦆 RouteMaster")
st.caption("Track 2 — Local review reply workspace for Mini Homestay Bak (Pontian)")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Customer review")
    sample_choice = st.selectbox(
        "Paste a review or pick a sample scenario:",
        ["Custom paste", "Parking — only one spot inside", "Trash bag leaked", "Positive stay"]
    )
    
    if sample_choice == "Parking — only one spot inside":
        review_input = "The place was fine but we brought three cars and had no idea where to put the last one. Terrible experience."
    elif sample_choice == "Trash bag leaked":
        review_input = "The kitchen trash bag leaked all over the floor when we lifted it up, creating a massive dirty mess."
    elif sample_choice == "Positive stay":
        review_input = "Everything was super clean and beautiful! The kids loved the place."
    else:
        review_input = st.text_area("Custom input block:", value="")

    run_btn = st.button("Run evaluation", type="primary")

with col_right:
    st.subheader("Analysis & Sponsor Hub")
    
    if run_btn and review_input:
        # Run local evaluation
        result = evaluate_review(review_input, KB_PATH)
        
        # Output visual stats
        st.metric("Detected Sentiment", result.sentiment.upper())
        st.text_area("Grounded Correspondence Reply Draft:", value=result.draft_reply, height=150)
        
        st.markdown("---")
        
        # Render the Mandatory Track 2 Platform Hub
        st.markdown("### 🔧 Track 2 Required Stack Hub")
        payload = build_issue_payload(result)
        
        st.json(payload.to_dict())
        
        api_key_input = st.text_input("Produck API key (optional)", type="password")
        
        if st.button("Push issue to Produck API", type="secondary", use_container_width=True):
            with st.spinner("Broadcasting payload tracking object..."):
                success, msg, body = push_issue_to_produck(payload, api_key=api_key_input)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    
        # Robust download checkpoint for demo submissions
        st.download_button(
            label="Download issue payload (JSON)",
            data=json.dumps(payload.to_dict(), indent=2),
            file_name=f"produck_issue_{result.topics[0]}.json",
            mime="application/json",
            use_container_width=True
        )