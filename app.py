import streamlit as st
import pandas as pd
from google import genai
from google.genai import types

# 1. SETUP THE MODERN GOOGLE GENAI API
if "GEMINI_API_KEY" in st.secrets:
    try:
        # Initialize client according to modern SDK standards
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        api_ready = True
    except Exception as e:
     # Check if it's a server overload error
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            st.warning("⏳ The AI servers are currently experiencing high traffic. Please wait 10 seconds and try asking again.")
        else:
    # For all other random errors
            st.error(f"AI Generation Failed: {e}")

# 2. BULLETPROOF STANDARD DICTIONARY
STANDARD_DATA = {
    "ph": {"limit": "6.5 - 8.5", "risk": "Beyond this range causes corrosion or severe digestive irritation."},
    "arsenic": {"limit": "0.01", "risk": "Chronic exposure leads to skin lesions and toxicity."},
    "fluoride": {"limit": "1.0", "risk": "Excess (>1.5) causes dental and skeletal fluorosis."},
    "lead": {"limit": "0.01", "risk": "Neurotoxic, especially dangerous for children."}
}

def check_numerical_limit(param, val):
    param_clean = param.lower().strip()
    if param_clean in STANDARD_DATA:
        limit_str = STANDARD_DATA[param_clean]["limit"]
        risk = STANDARD_DATA[param_clean]["risk"]
        
        if "-" in limit_str:
            low, high = map(float, limit_str.split("-"))
            if low <= val <= high:
                return "GREEN", f"Safe ({val}). Within safe range ({limit_str}).", "None"
            else:
                return "RED", f"CRITICAL ({val}). Outside safe range ({limit_str}).", risk
        else:
            limit = float(limit_str)
            if val <= limit:
                return "GREEN", f"Safe ({val}). Below permissible limit ({limit}).", "None"
            else:
                return "RED", f"CRITICAL ({val}). Exceeds permissible limit ({limit}).", risk
    return "YELLOW", f"Unknown Parameter ({param}).", "No standard rules stored."

# 3. STREAMLIT INTERFACE SETUP
st.set_page_config(page_title="Water Quality Advisor", layout="wide")
st.title("🚰 Aquaguard AI Advisory System")

tab1, tab2 = st.tabs(["💬 AI Advisor Chat", "📊 Batch CSV Analysis"])

with tab1:
    st.subheader("Ask the Water Quality Agent")
    user_query = st.text_input("Enter your question (e.g., 'Is pH 9.5 safe?' or 'What are the main goals of Jal Jeevan Mission?'):")
    
    if user_query:
        found_numerical = False
        
        # Look for target parameters inside the prompt
        for param in STANDARD_DATA.keys():
            if param in user_query.lower():
                words = user_query.split()
                for word in words:
                    # Clean clean common punctuation marks from words
                    cleaned_word = word.strip("?,.!:; ")
                    try:
                        val = float(cleaned_word)
                        status, msg, risk = check_numerical_limit(param, val)
                        if status == "GREEN":
                            st.success(f"**Direct Lookup:** {msg}")
                        else:
                            st.error(f"**Direct Lookup:** {msg}\n\n**Health Risk:** {risk}")
                        found_numerical = True
                        break  # Found valid comparison number
                    except ValueError:
                        continue  # Keep looking through words
        
        # If it's a structural policy/informational query, send it to Gemini
        if not found_numerical:
            if api_ready:
                with st.spinner("AI is thinking..."):
                    try:
                        # Correctly apply structural system instructions via GenerateContentConfig
                        config = types.GenerateContentConfig(
                            system_instruction="You are an expert Indian water safety officer. Answer the user precisely using official guidelines.",
                            temperature=0.2
                        )
                        response = client.models.generate_content(
                            model='gemini-3.5-flash',
                            contents=user_query,
                            config=config
                        )
                        st.markdown("### AI Advisory Note:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"AI Generation Failed: {e}")
            else:
                st.warning("AI is offline. Please paste your GEMINI_API_KEY into your Streamlit Secrets panel.")

with tab2:
    st.subheader("Batch Sample Processing")
    uploaded_file = st.file_uploader("Upload water test sheet CSV", type="csv")
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'parameter' in df.columns and 'value' in df.columns:
            results = []
            for _, row in df.iterrows():
                try:
                    status, msg, risk = check_numerical_limit(str(row['parameter']), float(row['value']))
                    results.append({"Parameter": row['parameter'], "Value": row['value'], "Status": status, "Details": msg, "Health Note": risk})
                except Exception:
                    results.append({"Parameter": row['parameter'], "Value": row['value'], "Status": "ERROR", "Details": "Invalid row inputs", "Health Note": "N/A"})
            
            res_df = pd.DataFrame(results)
            
            # FIXED: Changed deprecated .applymap to modern .map
            def color_status(val):
                if val == "GREEN": return 'background-color: #d4edda; color: #155724'
                if val == "RED": return 'background-color: #f8d7da; color: #721c24'
                return 'background-color: #fff3cd; color: #856404'
                
            st.dataframe(res_df.style.map(color_status, subset=['Status']))
        else:
            st.error("CSV must contain exactly 'parameter' and 'value' columns.")