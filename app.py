import streamlit as st
import pandas as pd
import io

# --- Mock Data to make the app functional immediately ---
# In a full deployment, this replaces the CSV lookup and LLM response
STANDARD_DATA = {
    "ph": {"limit": "6.5 - 8.5", "risk": "Beyond this range causes corrosion or severe digestive irritation."},
    "arsenic": {"limit": "0.01", "risk": "Chronic exposure leads to skin lesions and toxicity."},
    "fluoride": {"limit": "1.0", "risk": "Excess (>1.5) causes dental and skeletal fluorosis."},
    "lead": {"limit": "0.01", "risk": "Neurotoxic, especially dangerous for children."}
}

def check_parameter(param, val):
    param_clean = param.lower().strip()
    if param_clean in STANDARD_DATA:
        limit_str = STANDARD_DATA[param_clean]["limit"]
        risk = STANDARD_DATA[param_clean]["risk"]
        
        if "-" in limit_str:
            low, high = map(float, limit_str.split("-"))
            if low <= val <= high:
                return "GREEN", f"Safe ({val}). Within permissible range ({limit_str}).", "None"
            else:
                return "RED", f"CRITICAL ({val}). Outside safe range ({limit_str}).", risk
        else:
            limit = float(limit_str)
            if val <= limit:
                return "GREEN", f"Safe ({val}). Below permissible limit ({limit}).", "None"
            else:
                return "RED", f"CRITICAL ({val}). Exceeds permissible limit ({limit}).", risk
    return "YELLOW", f"Unknown Parameter ({param}). Value: {val}", "No threshold data available in standard."

# --- Streamlit UI ---
st.set_page_config(page_title="Water Quality Advisor", layout="wide")
st.title("🚰 JalVision: Water Quality Advisory Agent")

tab1, tab2 = st.tabs(["💬 AI Advisor Chat (Simulated)", "📊 Batch CSV Analysis"])

with tab1:
    st.subheader("Ask the Water Quality Agent")
    user_query = st.text_input("Enter your query (e.g., 'My pH is 9.2' or 'Is 0.05 arsenic safe?'):")
    
    if user_query:
        # Simple rule-based parser to simulate the Agent behavior locally
        found = False
        for param in STANDARD_DATA.keys():
            if param in user_query.lower():
                # Extract numbers if present
                words = user_query.split()
                for word in words:
                    try:
                        val = float(word.strip("?,. "))
                        status, msg, risk = check_parameter(param, val)
                        if status == "GREEN":
                            st.success(f"**{param.upper()} Status:** {msg}")
                        else:
                            st.error(f"**{param.upper()} Status:** {msg}\n\n**Health Risk:** {risk}")
                        found = True
                        break
                    except ValueError:
                        continue
        if not found:
            st.info("💡 *This simulated agent answers specific threshold questions (e.g., 'pH 9'). Connect your Watsonx/Granite API key to unlock semantic policy search across Jal Jeevan docs.*")

with tab2:
    st.subheader("Batch Sample Processing")
    st.write("Upload a water test sheet CSV with column headers: `parameter` and `value`")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if 'parameter' in df.columns and 'value' in df.columns:
            results = []
            for _, row in df.iterrows():
                status, msg, risk = check_parameter(str(row['parameter']), float(row['value']))
                results.append({"Parameter": row['parameter'], "Value": row['value'], "Status": status, "Details": msg, "Health Note": risk})
            
            res_df = pd.DataFrame(results)
            
            # Custom styled dataframe output
            def color_status(val):
                if val == "GREEN": return 'background-color: #d4edda; color: #155724'
                if val == "RED": return 'background-color: #f8d7da; color: #721c24'
                return 'background-color: #fff3cd; color: #856404'
                
            st.dataframe(res_df.style.applymap(color_status, subset=['Status']))
            
            # Advisory Export PDF simulation
            csv_download = res_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Advisory Report (CSV)", csv_download, "water_advisory.csv", "text/csv")
        else:
            st.error("CSV must contain 'parameter' and 'value' columns.")