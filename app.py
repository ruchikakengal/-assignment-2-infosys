import streamlit as st

import requests

import json

import pandas as pd

import plotly.express as px

import plotly.graph_objects as go

from datetime import datetime

import time

import base64

from typing import Dict, Any, List



# Configuration

BACKEND_URL = "http://localhost:8000"

st.set_page_config(

    page_title="Commercial AI Compliance Checker",

    page_icon="⚖️",

    layout="wide",

    initial_sidebar_state="expanded"

)



def init_session_state():

    """Initialize session state variables"""

    defaults = {

        'analysis_results': None,

        'modified_contract': "",

        'api_status': "unknown",

        'analysis_history': [],

        'current_tab': "analyze",

        'batch_results': None

    }

    

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value



def check_api_health():

    """Check if backend API is healthy"""

    try:

        response = requests.get(f"{BACKEND_URL}/health", timeout=10)

        if response.status_code == 200:

            data = response.json()

            st.session_state.api_status = data.get('status', 'healthy')

            return data

        else:

            st.session_state.api_status = "unhealthy"

            return None

    except:

        st.session_state.api_status = "unreachable"

        return None



def analyze_contract_text(contract_text: str, regulations: List[str] = None, 

                         jurisdiction: str = "US", industry: str = "general"):

    """Send contract text to backend for analysis"""

    try:

        payload = {

            "contract_text": contract_text,

            "regulations": regulations,

            "jurisdiction": jurisdiction,

            "industry": industry

        }

        

        with st.spinner("🔍 Analyzing contract compliance..."):

            response = requests.post(

                f"{BACKEND_URL}/analyze-text/",

                json=payload,

                timeout=120

            )

            

        if response.status_code == 200:

            return response.json()

        else:

            st.error(f"Analysis failed: {response.text}")

            return None

    except Exception as e:

        st.error(f"Error connecting to backend: {e}")

        return None



def upload_contract_file(uploaded_file):

    """Upload contract file to backend"""

    try:

        with st.spinner("📤 Uploading and analyzing contract..."):

            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}

            response = requests.post(

                f"{BACKEND_URL}/upload-contract/",

                files=files,

                timeout=120

            )

            

        if response.status_code == 200:

            return response.json()

        else:

            st.error(f"Upload failed: {response.text}")

            return None

    except Exception as e:

        st.error(f"Error uploading file: {e}")

        return None



def display_compliance_dashboard(results: Dict[str, Any]):

    """Display commercial-grade compliance dashboard"""

    st.subheader("📊 Compliance Executive Dashboard")

    

    # Key metrics

    col1, col2, col3, col4 = st.columns(4)

    

    with col1:

        overall_score = results.get('overall_score', 0) * 100

        st.metric(

            "Overall Compliance Score", 

            f"{overall_score:.1f}%",

            delta=f"{overall_score - 50:.1f}%" if overall_score > 50 else None,

            delta_color="normal" if overall_score >= 70 else "inverse"

        )

    

    with col2:

        total_issues = sum(len(reg['issues']) for reg in results['results'])

        st.metric("Total Issues Found", total_issues)

    

    with col3:

        regulations_analyzed = len(results['results'])

        st.metric("Regulations Analyzed", regulations_analyzed)

    

    with col4:

        risk_level = results.get('risk_level', 'medium').upper()

        risk_color = "red" if risk_level == "HIGH" else "orange" if risk_level == "MEDIUM" else "green"

        st.metric("Risk Level", risk_level)

    

    # Risk assessment visualization

    col1, col2 = st.columns(2)

    

    with col1:

        # Risk distribution chart

        risk_data = []

        for reg in results['results']:

            risk_data.append({

                'Regulation': reg['regulation'],

                'Score': reg['compliance_score'] * 100,

                'Risk': reg['risk_assessment'].upper()

            })

        

        if risk_data:

            df = pd.DataFrame(risk_data)

            fig = px.bar(

                df, 

                x='Regulation', 

                y='Score',

                color='Risk',

                title="Compliance Score by Regulation",

                color_discrete_map={'HIGH': '#EF553B', 'MEDIUM': '#FFA15A', 'LOW': '#00CC96'}

            )

            fig.update_layout(height=300)

            st.plotly_chart(fig, use_container_width=True)

    

    with col2:

        # Issues by regulation

        issues_data = []

        for reg in results['results']:

            issues_data.append({

                'Regulation': reg['regulation'],

                'Issues': len(reg['issues']),

                'Missing Clauses': len(reg['missing_clauses'])

            })

        

        if issues_data:

            df = pd.DataFrame(issues_data)

            fig = px.bar(

                df, 

                x='Regulation', 

                y=['Issues', 'Missing Clauses'],

                title="Issues & Missing Clauses by Regulation",

                barmode='group'

            )

            fig.update_layout(height=300)

            st.plotly_chart(fig, use_container_width=True)

    

    st.divider()



def display_regulation_details(results: Dict[str, Any]):

    """Display detailed analysis for each regulation"""

    st.subheader("📈 Regulation-wise Detailed Analysis")

    

    for regulation in results['results']:

        with st.expander(

            f"**{regulation['regulation']}** - {regulation['compliance_score']*100:.1f}% Compliance • {regulation['risk_assessment'].upper()} RISK", 

            expanded=True

        ):

            col1, col2 = st.columns(2)

            

            with col1:

                st.markdown("##### 🚨 Compliance Issues")

                for issue in regulation['issues']:

                    st.error(f"• {issue}")

            

            with col2:

                st.markdown("##### 💡 Actionable Recommendations")

                for recommendation in regulation['recommendations']:

                    st.success(f"• {recommendation}")

            

            if regulation['missing_clauses']:

                st.markdown("##### 📝 Required Clause Additions")

                for clause in regulation['missing_clauses']:

                    risk_color = "🔴" if clause['risk_level'] == 'high' else "🟡" if clause['risk_level'] == 'medium' else "🟢"

                    

                    with st.expander(f"{risk_color} **{clause['clause']}** - {clause['risk_level'].upper()} RISK"):

                        st.write(f"**Description:** {clause['description']}")

                        if clause['legal_citation']:

                            st.write(f"**Legal Reference:** {clause['legal_citation']}")

                        st.write(f"**Requirements:** {', '.join(clause['requirements'])}")

                        

                        st.markdown("**AI-Suggested Clause:**")

                        st.code(clause['suggested_text'], language='text')

            

            if regulation['legal_references']:

                st.markdown("##### ⚖️ Legal References")

                for ref in regulation['legal_references']:

                    st.info(f"• {ref}")



def display_executive_summary(results: Dict[str, Any]):

    """Display executive summary for business stakeholders"""

    st.subheader("📋 Executive Summary")

    

    col1, col2 = st.columns([2, 1])

    

    with col1:

        st.markdown(results['summary'])

    

    with col2:

        st.markdown("##### 🎯 Key Takeaways")

        

        # Extract key points from summary

        summary_text = results['summary']

        key_points = [

            line.replace('•', '').strip() 

            for line in summary_text.split('\n') 

            if line.strip().startswith('•')

        ]

        

        for point in key_points[:5]:

            st.write(f"• {point}")



def main():

    # Custom CSS

    st.markdown("""

    <style>

    .main-header {

        font-size: 2.5rem;

        color: #1f77b4;

        text-align: center;

        margin-bottom: 2rem;

    }

    .commercial-badge {

        background-color: #ff6b6b;

        color: white;

        padding: 0.2rem 0.5rem;

        border-radius: 0.25rem;

        font-size: 0.8rem;

        font-weight: bold;

    }

    </style>

    """, unsafe_allow_html=True)

    

    st.markdown('<h1 class="main-header">⚖️ Commercial AI Contract Compliance Checker</h1>', unsafe_allow_html=True)

    st.markdown('<p style="text-align: center; font-size: 1.2rem;">Enterprise-grade regulatory compliance analysis powered by OpenAI</p>', unsafe_allow_html=True)

    

    init_session_state()

    

    # Sidebar

    with st.sidebar:

        st.image("https://via.placeholder.com/150x50/1f77b4/ffffff?text=COMMERCIAL", width=150)

        st.markdown("---")

        

        # API Status

        st.subheader("🔧 System Status")

        if st.button("Check System Health", use_container_width=True):

            health_data = check_api_health()

            if health_data and health_data.get('status') == 'healthy':

                st.success("✅ System Healthy")

                services = health_data.get('services', {})

                for service, status in services.items():

                    color = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"

                    st.write(f"{color} {service.title()}: {status}")

            else:

                st.error("❌ System Unhealthy")

        

        st.markdown("---")

        

        # Configuration

        st.subheader("⚙️ Analysis Configuration")

        

        jurisdiction = st.selectbox(

            "Primary Jurisdiction",

            ["US", "US_CA", "US_NY", "global"],

            help="Select the primary legal jurisdiction"

        )

        

        industry = st.selectbox(

            "Industry/Sector",

            ["financial", "banking", "lending", "insurance", "auto_finance", "general"],

            help="Select the industry context"

        )

        

        st.markdown("---")

        

        # Quick Actions

        st.subheader("🚀 Quick Actions")

        

        if st.button("View Analysis History", use_container_width=True):

            st.session_state.current_tab = "history"

        

        st.markdown("---")

        st.markdown("""

        **Supported Regulations:**

        - GLBA (Financial Privacy)

        - FCRA (Credit Reporting)  

        - TILA (Lending Disclosures)

        - CCPA/CPRA (California Privacy)

        - NYDFS (Cybersecurity)

        """)

    

    # Main content tabs

    tab1, tab2, tab3 = st.tabs(["📤 Analyze Contract", "📊 Results", "📈 History & Stats"])

    

    with tab1:

        st.header("Contract Analysis")

        

        analysis_method = st.radio(

            "Select Analysis Method:",

            ["Upload PDF Contract", "Paste Contract Text"],

            horizontal=True

        )

        

        if analysis_method == "Upload PDF Contract":

            st.subheader("📄 Upload Contract PDF")

            uploaded_file = st.file_uploader(

                "Choose a contract PDF file", 

                type="pdf",

                help="Upload a PDF contract for compliance analysis"

            )

            

            if uploaded_file is not None:

                col1, col2 = st.columns(2)

                with col1:

                    if st.button("🚀 Analyze Contract", type="primary", use_container_width=True):

                        results = upload_contract_file(uploaded_file)

                        if results:

                            st.session_state.analysis_results = results

                            st.session_state.modified_contract = results.get('modified_contract', '')

                            st.session_state.current_tab = "results"

                            st.rerun()

                

                with col2:

                    if st.button("📋 View Sample Contract", use_container_width=True):

                        st.info("Sample contract analysis would be displayed here")

        

        elif analysis_method == "Paste Contract Text":

            st.subheader("📝 Paste Contract Text")

            contract_text = st.text_area(

                "Paste your contract text here:",

                height=400,

                placeholder="Paste contract text here...\n\nExample:\nCAR FINANCING AGREEMENT\n\nBORROWER: John Smith...\nLENDER: ABC Bank...\nFINANCED AMOUNT: $50,000...",

                help="Paste the full contract text for analysis"

            )

            

            if st.button("🚀 Analyze Contract Text", type="primary", use_container_width=True):

                if contract_text.strip():

                    results = analyze_contract_text(contract_text, jurisdiction=jurisdiction, industry=industry)

                    if results:

                        st.session_state.analysis_results = results

                        st.session_state.modified_contract = results.get('modified_contract', '')

                        st.session_state.current_tab = "results"

                        st.rerun()

                else:

                    st.warning("Please enter contract text to analyze")

    

    with tab2:

        if st.session_state.analysis_results:

            results = st.session_state.analysis_results

            

            # Display dashboard and analysis

            display_compliance_dashboard(results)

            display_executive_summary(results)

            display_regulation_details(results)

            

            # Export section

            st.subheader("💾 Export Results")

            

            col1, col2, col3 = st.columns(3)

            

            with col1:

                # Download analysis as JSON

                analysis_json = json.dumps(results, indent=2)

                st.download_button(

                    label="📥 Download Analysis (JSON)",

                    data=analysis_json,

                    file_name=f"compliance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",

                    mime="application/json",

                    use_container_width=True

                )

            

            with col2:

                # Download modified contract

                if st.session_state.modified_contract:

                    st.download_button(

                        label="📄 Download Enhanced Contract",

                        data=st.session_state.modified_contract,

                        file_name=f"enhanced_contract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",

                        mime="text/plain",

                        use_container_width=True

                    )

            

            with col3:

                # Download executive summary

                executive_summary = results.get('executive_summary', '')

                st.download_button(

                    label="📋 Download Executive Summary",

                    data=executive_summary,

                    file_name=f"executive_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",

                    mime="text/plain",

                    use_container_width=True

                )

            

            # Search similar contracts

            st.subheader("🔍 Search Similar Contracts")

            search_query = st.text_input("Enter search terms to find similar contracts:")

            if search_query and st.button("Search Database"):

                try:

                    search_response = requests.get(

                        f"{BACKEND_URL}/search-contracts",

                        params={"query": search_query, "limit": 5}

                    )

                    if search_response.status_code == 200:

                        search_results = search_response.json()

                        if search_results['results']:

                            st.write("Similar contracts found:")

                            for result in search_results['results']:

                                with st.expander(f"Relevance: {result['relevance_score']:.2f} - {result['type'].title()}"):

                                    st.text(result['document'][:300] + "...")

                        else:

                            st.info("No similar contracts found.")

                except Exception as e:

                    st.error(f"Search failed: {e}")

        

        else:

            st.info("👆 Upload a contract or paste text to see analysis results")

            st.markdown("""

            ### 🎯 What You'll Get:

            

            **Comprehensive Compliance Analysis:**

            - 📊 Overall compliance score and risk assessment

            - 🔍 Regulation-specific gap analysis

            - 📝 AI-generated clause suggestions

            - ⚖️ Legal references and citations

            - 💡 Actionable recommendations

            

            **Commercial Features:**

            - Enterprise-grade regulatory knowledge

            - Multi-jurisdiction support

            - Industry-specific compliance

            - Historical analysis tracking

            """)

    

    with tab3:

        st.header("Analysis History & Statistics")

        

        col1, col2 = st.columns(2)

        

        with col1:

            st.subheader("📈 System Statistics")

            try:

                stats_response = requests.get(f"{BACKEND_URL}/analysis-history", params={"limit": 5})

                if stats_response.status_code == 200:

                    history_data = stats_response.json()

                    st.metric("Total Analyses", history_data.get('total', 0))

                    st.metric("Recent Analyses", len(history_data.get('history', [])))

                else:

                    st.error("Could not fetch statistics")

            except:

                st.error("Service unavailable")

        

        with col2:

            st.subheader("🕒 Recent Analyses")

            try:

                history_response = requests.get(f"{BACKEND_URL}/analysis-history", params={"limit": 10})

                if history_response.status_code == 200:

                    history_data = history_response.json()

                    for analysis in history_data.get('history', [])[:5]:

                        with st.expander(f"Analysis {analysis.get('analysis_id', '')}"):

                            st.write(f"Jurisdiction: {analysis.get('jurisdiction', 'Unknown')}")

                            st.write(f"Industry: {analysis.get('industry', 'Unknown')}")

                            st.write(f"Date: {analysis.get('analysis_timestamp', 'Unknown')}")

                else:

                    st.info("No analysis history available")

            except:

                st.error("Could not fetch history")



if __name__ == "__main__":

    main()
