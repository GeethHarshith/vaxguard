import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

def create_model():
    return IsolationForest(
        contamination=0.05,
        random_state=42
    )

def generate_scenario_data():
    # Make the random data reproducible
    np.random.seed(42)
    
    # Create 1000 minutes of sensor readings
    timestamps = pd.date_range(
        start="2026-09-17 08:00",
        periods=1000,
        freq="min"
    )
    
    # Normal refrigerator temperature
    temperature = np.random.normal(
        loc=5.0,
        scale=0.5,
        size=1000
    )
    
    # Put everything into a table
    data = pd.DataFrame({
        "timestamp": timestamps,
        "temperature": temperature
    })
    
    # Simulate a temperature excursion
    data.loc[700:730, "temperature"] = np.linspace(
        5.0,
        12.0,
        31
    )
    
    # Simulate missing sensor data (data gaps)
    # Drop 15 minutes of normal readings (indices 400 to 414)
    data = data.drop(range(400, 415))
    # Drop 5 minutes of readings during the excursion to test overlap (indices 710 to 714)
    data = data.drop(range(710, 715))
    # Reset index so it's contiguous again
    data = data.reset_index(drop=True)
    
    return data

def analyze_sensor_data(data, model):
    """
    Takes a DataFrame with 'timestamp' and 'temperature' and a trained IsolationForest model.
    Returns: (analyzed_data, gaps_list, incident_reports)
    """
    if data.empty:
        return data, [], []
        
    df = data.copy()
    
    # Ask the AI to classify each reading
    df["ai_prediction"] = model.predict(df[["temperature"]])
    
    # Convert AI output into readable labels
    df["status"] = df["ai_prediction"].map({
        1: "NORMAL",
        -1: "ANOMALY"
    })
    
    # Add an anomaly score
    df["anomaly_score"] = model.decision_function(df[["temperature"]])
    
    # Identify continuous periods of anomalies
    is_anomaly = df["status"] == "ANOMALY"
    df["incident_group"] = (is_anomaly != is_anomaly.shift()).cumsum()
    
    anomalies_only = df[is_anomaly]
    
    # Detect missing sensor readings (DATA GAPS)
    time_diff = df["timestamp"].diff()
    gap_mask = time_diff > pd.Timedelta(minutes=1)
    
    gaps_list = []
    for idx in df[gap_mask].index:
        gap_end = df.loc[idx, "timestamp"]
        pos = df.index.get_loc(idx)
        gap_start = df.iloc[pos - 1]["timestamp"]
        duration = time_diff.loc[idx]
        missing_count = int(duration.total_seconds() // 60) - 1
        duration_mins = int(duration.total_seconds() // 60)
        
        gaps_list.append({
            "start": gap_start,
            "end": gap_end,
            "duration_minutes": duration_mins,
            "missing_count": missing_count
        })
        
    incident_reports = []
    if not anomalies_only.empty:
        incidents = anomalies_only.groupby("incident_group")
        for group_id, incident_data in incidents:
            start_time = incident_data["timestamp"].min()
            end_time = incident_data["timestamp"].max()
            duration_minutes = int((end_time - start_time).total_seconds() // 60) + 1
            peak_temp = incident_data["temperature"].max()
            avg_score = incident_data["anomaly_score"].mean()
            
            has_incomplete_data = False
            for g in gaps_list:
                if g["end"] >= start_time and g["start"] <= end_time:
                    has_incomplete_data = True
                    break
            
            incident_reports.append({
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration_minutes,
                "peak_temp": peak_temp,
                "avg_score": avg_score,
                "has_incomplete_data": has_incomplete_data
            })
            
    return df, gaps_list, incident_reports


def run_prototype_scenario():
    data = generate_scenario_data()
    model = create_model()
    model.fit(data[["temperature"]])
    analyzed_data, gaps_list, incident_reports = analyze_sensor_data(data, model)
    return analyzed_data, gaps_list, incident_reports


def main():
    analyzed_data, gaps_list, incident_reports = run_prototype_scenario()
    
    print(analyzed_data.head(10))
    print("\nTemperature during simulated incident:")
    print(analyzed_data.iloc[695:720])
    
    print("\n--- Sensor Data Gap Report ---")
    for g in gaps_list:
        print(f"DATA GAP DETECTED:")
        print(f"  Gap Start (Last Reading): {g['start'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Gap End (Next Reading):   {g['end'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Missing Readings:         {g['missing_count']}")
        print(f"  Duration of Gap:          {g['duration_minutes']} minutes")
        print("-" * 50)

    if not gaps_list:
        print("No sensor data gaps detected.")

    print("\n--- Incident Escalation Report ---")
    print("IMPORTANT NOTICE: This system provides decision support only.")
    print("It does NOT determine if vaccines are safe or unsafe to use.")
    print("Final assessment must follow established public health protocols.\n")

    if not incident_reports:
        print("No suspected excursion windows detected.")
    else:
        for inc in incident_reports:
            print(f"Suspected Excursion Window:")
            print(f"  Start Time:     {inc['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  End Time:       {inc['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration:       {inc['duration']} minutes")
            print(f"  Peak Temp:      {inc['peak_temp']:.2f} °C")
            print(f"  Avg AI Score:   {inc['avg_score']:.2f} (Anomaly score, NOT a probability)")
            if inc['has_incomplete_data']:
                print(f"  WARNING:        Incomplete data (sensor gap) intersects this window.")
            print("-" * 50)

if __name__ == "__main__":
    main()