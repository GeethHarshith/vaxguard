import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sys
import os

sys.path.append(os.path.dirname(__file__))
import prototype

# --- Configuration ---
st.set_page_config(page_title="VaxGuard", layout="wide")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp {
        background-color: #f6f8fa;
        color: #24292f;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Native streamit buttons as cards */
    div.stButton > button {
        white-space: pre-wrap !important;
        text-align: left !important;
        justify-content: flex-start !important;
        color: #24292f !important;
        border: 1px solid #d0d7de !important;
        background-color: #ffffff !important;
        border-radius: 8px !important;
        padding: 16px !important;
        height: 160px !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    div.stButton > button:hover {
        border-color: #0969da !important;
    }
    
    /* Selected card styling */
    div.stButton > button[kind="primary"] {
        border: 2px solid #0969da !important;
        background-color: #f8faff !important;
        box-shadow: 0 2px 6px rgba(9, 105, 218, 0.1);
    }
    
    /* Control buttons in the header */
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button {
        background-color: #24292f !important;
        color: #ffffff !important;
        border: 1px solid #1f2328 !important;
        font-weight: 700 !important;
        text-align: center !important;
        justify-content: center !important;
        height: 40px !important;
        padding: 0 16px !important;
        border-radius: 6px !important;
        white-space: nowrap !important;
    }
    div[data-testid="stHorizontalBlock"]:first-of-type div.stButton > button:hover {
        background-color: #424a53 !important;
    }

    .event-log {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85em;
        line-height: 1.4;
        color: #57606a;
    }
    
    h3, h4 { margin-top: 0 !important; padding-top: 0 !important; }
    
    .detail-panel {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
def init_simulation():
    # Start at idx 15 so we have a visible line
    st.session_state.sim_index = 15
    st.session_state.is_running = False
    st.session_state.event_log = []
    st.session_state.sim_start_time = datetime.now(ZoneInfo("Asia/Kolkata"))
    st.session_state.view_report = None
    
    np.random.seed(42)
    # 200 ticks = 200 minutes of simulation mapped sequentially from sim_start_time
    # We want sim_start_time to be at sim_index 15, so times start 15 mins before sim_start_time
    start_offset = st.session_state.sim_start_time - timedelta(minutes=15)
    times = pd.date_range(start=start_offset, periods=200, freq="min")
    
    s1_temp = np.random.normal(loc=5.0, scale=0.3, size=200)
    
    s2_temp = np.random.normal(loc=5.0, scale=0.3, size=200)
    s2_temp[50:90] = np.linspace(5.0, 11.0, 40)
    s2_temp[90:120] = np.random.normal(loc=11.5, scale=0.4, size=30)
    s2_temp[120:150] = np.linspace(11.0, 5.0, 30)
    s2_temp[150:] = np.random.normal(loc=5.0, scale=0.3, size=50)
    
    s3_temp = np.random.normal(loc=5.0, scale=0.3, size=200)
    
    s4_temp = np.random.normal(loc=5.0, scale=0.3, size=200)
    s4_temp[130:140] = np.array([5.5, 6.5, 8.5, 10.0, 10.5, 9.0, 7.5, 6.0, 5.5, 5.2])
    
    st.session_state.sequences = {
        "Storage 01": pd.DataFrame({"timestamp": times, "temperature": s1_temp}),
        "Storage 02": pd.DataFrame({"timestamp": times, "temperature": s2_temp}),
        "Storage 03": pd.DataFrame({"timestamp": times, "temperature": s3_temp}),
        "Storage 04": pd.DataFrame({"timestamp": times, "temperature": s4_temp})
    }
    
    st.session_state.historical_incidents = {k: [] for k in ["Storage 01", "Storage 02", "Storage 03", "Storage 04"]}
    st.session_state.model = prototype.create_model()
    st.session_state.model.fit(pd.DataFrame({"temperature": np.random.normal(loc=5.0, scale=0.5, size=1000)}))
    st.session_state.last_status = {k: "STABLE" for k in ["Storage 01", "Storage 02", "Storage 03", "Storage 04"]}

if 'sequences' not in st.session_state:
    init_simulation()
    st.session_state.sim_speed = 5
    st.session_state.selected_storage = "Storage 01"

def log_event(storage, message):
    ts = st.session_state.sequences["Storage 01"].iloc[st.session_state.sim_index]["timestamp"].strftime("%H:%M:%S")
    st.session_state.event_log.insert(0, f"{ts}  {storage:<10}  {message}")
    if len(st.session_state.event_log) > 15:
        st.session_state.event_log.pop()

# --- Main Live Fragment ---
@st.fragment(run_every="500ms")
def live_dashboard():
    # Advance time if running
    if st.session_state.is_running and st.session_state.sim_index < 199:
        st.session_state.sim_index += st.session_state.sim_speed
        if st.session_state.sim_index >= 199:
            st.session_state.sim_index = 199
            st.session_state.is_running = False

    idx = st.session_state.sim_index
    current_real_dt = datetime.now(ZoneInfo("Asia/Kolkata"))
    
    # ---------------- HEADER ----------------
    col_head1, col_head2, col_head3 = st.columns([1.5, 1, 1.5])

    with col_head1:
        st.markdown("""
        <div style='margin-bottom: 10px;'>
            <h3 style='margin: 0; padding: 0; color: #24292f;'>VAXGUARD</h3>
            <div style='color: #57606a; font-weight: 500; font-size: 0.9em; letter-spacing: 0.5px;'>Vaccine Cold-Chain Anomaly Monitor</div>
        </div>
        """, unsafe_allow_html=True)

    with col_head3:
        st.markdown(f"""
        <div style='font-family: -apple-system; font-size: 1.0em; color: #57606a; text-align: right;'>
            <span style='color: #cf222e; font-weight: bold;'>● LIVE</span><br/>
            {current_real_dt.strftime('%d %b %Y').upper()}<br/>
            {current_real_dt.strftime('%H:%M:%S')} IST
        </div>
        """, unsafe_allow_html=True)

    with col_head2:
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            if st.button("START", use_container_width=True):
                st.session_state.is_running = True
                log_event("SYSTEM", "SIMULATION STARTED")
        with col_b2:
            if st.button("PAUSE", use_container_width=True):
                st.session_state.is_running = False
        with col_b3:
            if st.button("RESET", use_container_width=True):
                init_simulation()
                st.rerun()
                
        speed_map = {"1x": 1, "2x": 2, "5x": 5}
        sel_speed = st.radio("Simulation speed:", ["1x", "2x", "5x"], index=2, horizontal=True, label_visibility="collapsed")
        st.session_state.sim_speed = speed_map[sel_speed]

    st.markdown("<hr style='margin: 10px 0;'/>", unsafe_allow_html=True)

    # ---------------- DATA PROCESSING ----------------
    analyzed = {}
    for s_id in ["Storage 01", "Storage 02", "Storage 03", "Storage 04"]:
        df = st.session_state.sequences[s_id].iloc[:idx+1].copy()
        
        # Storage 03 gap mapping: Ticks 80 to 140
        if s_id == "Storage 03" and idx >= 80:
            gap_end = min(idx + 1, 140)
            df = df.drop(df.index[80:gap_end])
            
        status = "STABLE"
        score = 100
        active_inc = None
        
        if len(df) > 5:
            a_df, gaps, incs = prototype.analyze_sensor_data(df, st.session_state.model)
            
            if df.empty or (s_id == "Storage 03" and 80 <= idx < 140):
                status = "OFFLINE"
                score = 0
            elif incs:
                last_time = df.iloc[-1]["timestamp"]
                for inc in incs:
                    if inc['end_time'] == last_time:
                        active_inc = inc
                        break
                
                if active_inc:
                    if active_inc['duration'] < 3:
                        status = "WATCH"
                    else:
                        status = "ACTIVE ANOMALY"
                    score = max(0, 100 - active_inc['duration'] * 5 - (active_inc['peak_temp'] - 5)*10)
                
                for inc in incs:
                    if inc['end_time'] < last_time:
                        existing = [h for h in st.session_state.historical_incidents[s_id] if h.get('start_time') == inc['start_time']]
                        if not existing:
                            norm = inc.copy()
                            norm["storage_id"] = s_id
                            norm["type"] = "ANOMALY"
                            st.session_state.historical_incidents[s_id].append(norm)
                            log_event(s_id, "INCIDENT RESOLVED")
                            
            if status == "STABLE" and gaps:
                 for gap in gaps:
                     if gap['end'] <= df.iloc[-1]["timestamp"]:
                         existing = [h for h in st.session_state.historical_incidents[s_id] if h.get('start_time') == gap['start']]
                         if not existing:
                             st.session_state.historical_incidents[s_id].append({
                                 "storage_id": s_id,
                                 "start_time": gap['start'],
                                 "end_time": gap['end'],
                                 "duration": gap['duration_minutes'],
                                 "type": "GAP"
                             })
                             log_event(s_id, "SENSOR RECONNECTED")
                             
            if st.session_state.last_status[s_id] != status:
                if status == "OFFLINE":
                    log_event(s_id, "SENSOR OFFLINE")
                elif status == "ACTIVE ANOMALY":
                    log_event(s_id, "ANOMALY DETECTED")
                elif status == "WATCH":
                    log_event(s_id, "TEMP RISE DETECTED")
                elif status == "STABLE":
                    if st.session_state.last_status[s_id] == "OFFLINE":
                        log_event(s_id, "SENSOR RECONNECTED")
                    elif st.session_state.last_status[s_id] in ["ACTIVE ANOMALY", "WATCH"]:
                        log_event(s_id, "TEMPERATURE RECOVERED")
                st.session_state.last_status[s_id] = status

            analyzed[s_id] = {
                'df': a_df,
                'status': status,
                'score': int(score),
                'active_inc': active_inc,
                'temp': df.iloc[-1]["temperature"] if not (s_id == "Storage 03" and 80 <= idx < 140) else None,
            }
        else:
            analyzed[s_id] = {
                'df': df,
                'status': "STABLE",
                'score': 100,
                'active_inc': None,
                'temp': df.iloc[-1]["temperature"] if not df.empty else None,
            }

    # ---------------- MAIN LAYOUT ----------------
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        grid = st.columns(2)
        for i, s_id in enumerate(["Storage 01", "Storage 02", "Storage 03", "Storage 04"]):
            data = analyzed[s_id]
            status = data['status']
            
            if status == "OFFLINE":
                temp_str = "UNKNOWN"
                meta_text = "SENSOR OFFLINE\nData gap"
                icon = "⚪"
            elif status == "ACTIVE ANOMALY":
                temp_str = f"{data['temp']:.1f} °C" if data['temp'] is not None else "UNKNOWN"
                meta_text = f"ACTIVE ANOMALY\nStability {data['score']}%\nSensor Online"
                icon = "🔴"
            elif status == "WATCH":
                temp_str = f"{data['temp']:.1f} °C" if data['temp'] is not None else "UNKNOWN"
                meta_text = f"WATCH\nStability {data['score']}%\nSensor Online"
                icon = "🟡"
            else:
                temp_str = f"{data['temp']:.1f} °C" if data['temp'] is not None else "UNKNOWN"
                meta_text = f"STABLE\nStability {data['score']}%\nSensor Online"
                icon = "🟢"
                
            # Formatting text to mimic cards
            btn_text = f"{icon} {s_id}\n\n{temp_str}\n{meta_text}"
            
            with grid[i % 2]:
                is_selected = (st.session_state.selected_storage == s_id)
                if st.button(btn_text, key=f"storage_card_{s_id}", type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state.selected_storage = s_id
                    st.session_state.view_report = None

    with col_right:
        st.markdown("<div class='detail-panel'>", unsafe_allow_html=True)
        s_id = st.session_state.selected_storage
        data = analyzed[s_id]
        status = data['status']
        hist = st.session_state.historical_incidents[s_id]
        
        # Header for the right panel
        if status == "ACTIVE ANOMALY":
            header_color = "#cf222e"
        elif status == "WATCH":
            header_color = "#b35900"
        elif status == "OFFLINE":
            header_color = "#8c959f"
        else:
            header_color = "#2da44e"
            
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;">
            <span>{s_id}</span>
            <span style="color: {header_color};">{status}</span>
        </div>
        """, unsafe_allow_html=True)
        
        df_plot = data['df'].copy()
        if not df_plot.empty:
            base = alt.Chart(df_plot).encode(
                x=alt.X('timestamp:T', title=None, axis=alt.Axis(format="%H:%M", grid=False, labelColor='#57606a')),
                y=alt.Y('temperature:Q', title="Temperature (°C)", scale=alt.Scale(domain=[0, 15]), axis=alt.Axis(grid=True, gridColor='#e1e4e8', labelColor='#57606a'))
            )
            line = base.mark_line(color='#24292f', strokeWidth=2)
            safe_line = alt.Chart(pd.DataFrame({'y': [8.0]})).mark_rule(color='#cf222e', strokeDash=[4, 4]).encode(y='y:Q')
            
            if 'status' in df_plot.columns:
                anomalies = df_plot[df_plot['status'] == 'ANOMALY']
                if not anomalies.empty:
                    dots = alt.Chart(anomalies).mark_circle(color='#cf222e', size=80).encode(
                        x='timestamp:T',
                        y='temperature:Q'
                    )
                    chart = (safe_line + line + dots).properties(height=250)
                else:
                    chart = (safe_line + line).properties(height=250)
            else:
                chart = (safe_line + line).properties(height=250)
        else:
            chart = alt.Chart(pd.DataFrame()).mark_line().properties(height=250)
            
        st.altair_chart(chart, use_container_width=True)
        
        # Info rows
        temp_val = f"{data['temp']:.1f} °C" if data['temp'] is not None else "UNKNOWN"
        sens_val = "ONLINE" if status != "OFFLINE" else "OFFLINE"
        score_val = f"{data['score']}%" if status != "OFFLINE" else "N/A"
        
        st.markdown(f"""
        <table style="width:100%; font-size:0.95em; border-collapse: collapse; margin-bottom: 20px;">
            <tr style="border-bottom: 1px solid #eaecef;"><td style="padding: 6px 0; color:#57606a;">Current temperature</td><td style="text-align:right; font-weight:bold;">{temp_val}</td></tr>
            <tr style="border-bottom: 1px solid #eaecef;"><td style="padding: 6px 0; color:#57606a;">Configured requirement</td><td style="text-align:right;">2.0 – 8.0 °C</td></tr>
            <tr style="border-bottom: 1px solid #eaecef;"><td style="padding: 6px 0; color:#57606a;">Stability score</td><td style="text-align:right; font-weight:bold;">{score_val}</td></tr>
            <tr style="border-bottom: 1px solid #eaecef;"><td style="padding: 6px 0; color:#57606a;">Sensor status</td><td style="text-align:right;">{sens_val}</td></tr>
        </table>
        """, unsafe_allow_html=True)
            
        latest_anomaly = next((h for h in reversed(hist) if h.get('type') == 'ANOMALY'), None)
        
        if status == "ACTIVE ANOMALY" and data['active_inc']:
            inc = data['active_inc']
            st.markdown(f"""
            <div style="color: #cf222e; font-weight: bold; margin-bottom: 8px;">SUSPECTED EXCURSION</div>
            <table style="width:100%; font-size:0.9em; margin-bottom: 15px;">
                <tr><td style="color:#57606a; padding-bottom: 4px;">Detected at</td><td style="text-align:right;">{inc['start_time'].strftime('%H:%M:%S')} IST</td></tr>
                <tr><td style="color:#57606a; padding-bottom: 4px;">Possible exposure window</td><td style="text-align:right;">{inc['start_time'].strftime('%H:%M:%S')} – {inc['end_time'].strftime('%H:%M:%S')} IST</td></tr>
                <tr><td style="color:#57606a; padding-bottom: 4px;">Duration</td><td style="text-align:right;">{inc['duration']} min</td></tr>
                <tr><td style="color:#57606a; padding-bottom: 4px;">Peak temperature</td><td style="text-align:right;">{inc['peak_temp']:.1f} °C</td></tr>
                <tr><td style="color:#57606a; padding-bottom: 4px;">Anomaly score</td><td style="text-align:right;">{inc['avg_score']:.2f}</td></tr>
            </table>
            
            <div style="font-weight: bold; margin-bottom: 4px; font-size: 0.9em;">EVIDENCE</div>
            <div style="font-size: 0.9em; color:#57606a; margin-bottom: 15px;">
                • Temperature rising<br/>
                • Abnormal behavior detected<br/>
                • Sensor data available
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("VIEW INCIDENT REPORT", key="report_active"):
                st.session_state.view_report = inc
                
        elif status == "STABLE" and latest_anomaly:
            st.markdown(f"""
            <div style="color: #b35900; font-weight: bold; margin-bottom: 8px;">RECENT EVENT</div>
            <div style="font-size: 0.9em; color:#57606a; margin-bottom: 15px;">
                Previous anomaly detected at {latest_anomaly['start_time'].strftime('%H:%M:%S')} IST<br/>
                Peak temperature: {latest_anomaly['peak_temp']:.1f} °C<br/>
                Duration: {latest_anomaly['duration']} min
            </div>
            """, unsafe_allow_html=True)
            if st.button("VIEW INCIDENT REPORT", key="report_hist"):
                st.session_state.view_report = latest_anomaly
                
        elif status == "OFFLINE":
            dur = idx - 79 if idx > 79 else 0
            if data['df'].empty:
                last_time = "UNKNOWN"
            else:
                last_time = data['df'].iloc[-1]['timestamp'].strftime('%H:%M:%S') + " IST"
            
            st.markdown(f"""
            <div style="color: #8c959f; font-weight: bold; margin-bottom: 8px;">DATA GAP DETECTED</div>
            <table style="width:100%; font-size:0.9em; margin-bottom: 15px;">
                <tr><td style="color:#57606a; padding-bottom: 4px;">Last reading</td><td style="text-align:right;">{last_time}</td></tr>
                <tr><td style="color:#57606a; padding-bottom: 4px;">Data gap</td><td style="text-align:right;">{dur} min</td></tr>
            </table>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True) # End detail panel

        # Render Incident Report Modal-like Expander
        if st.session_state.view_report is not None:
            rep = st.session_state.view_report
            with st.expander("VAXGUARD INCIDENT REPORT", expanded=True):
                st.markdown(f"""
                **Storage:** {s_id}  
                **Incident:** Suspected temperature excursion  
                **Detected:** {rep['start_time'].strftime('%H:%M:%S')} IST  
                **Possible exposure window:** {rep['start_time'].strftime('%H:%M:%S')} – {rep.get('end_time', rep['start_time']).strftime('%H:%M:%S')} IST  
                **Peak temperature:** {rep.get('peak_temp', 'N/A')}{' °C' if 'peak_temp' in rep else ''}  
                **Duration:** {rep['duration']} min  
                **Anomaly score:** {rep.get('avg_score', 'N/A')}  
                **Data completeness:** {'Incomplete' if rep.get('has_incomplete_data', False) else 'Complete'}  
                
                **Evidence:**  
                Temperature rise + persistent abnormal behavior
                
                ---
                **HUMAN REVIEW REQUIRED**  
                The system provides decision support and does not independently determine vaccine viability.
                """)
                if st.button("Close Report", key="close_report"):
                    st.session_state.view_report = None
                    st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("**EVENT LOG**")
    for log in st.session_state.event_log:
        st.markdown(f"<div class='event-log'>{log}</div>", unsafe_allow_html=True)

# Run the live fragment
live_dashboard()
