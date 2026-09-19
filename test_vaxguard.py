import pandas as pd
import sys
import os

# Ensure prototype can be imported
sys.path.append(os.path.dirname(__file__))
import prototype

def run_tests():
    print("\n\n" + "="*60)
    print("STARTING VAXGUARD VALIDATION TESTS")
    print("="*60)
    
    passed = 0
    failed = 0
    
    def assert_test(name, condition, error_msg=""):
        nonlocal passed, failed
        if condition:
            print(f"[PASS] {name}")
            passed += 1
        else:
            print(f"[FAIL] {name} - {error_msg}")
            failed += 1

    data, gaps_list, incident_reports = prototype.run_prototype_scenario()
    
    # Known simulated excursion parameters
    simulated_start = pd.to_datetime("2026-09-17 19:40:00")
    simulated_end = pd.to_datetime("2026-09-17 20:10:00")
    
    # 1. NORMAL SCENARIO
    false_positives = [
        inc for inc in incident_reports 
        if not (inc['start_time'] <= simulated_end and inc['end_time'] >= simulated_start)
    ]
    num_fp = len(false_positives)
    assert_test("NORMAL SCENARIO: Sensible false positive rate", num_fp < 30, f"Found {num_fp} false positive windows")
    
    # 2. TEMPERATURE EXCURSION
    tp_incident = None
    for inc in incident_reports:
        if inc['start_time'] <= simulated_end and inc['end_time'] >= simulated_start:
            if inc['peak_temp'] > 10.0:
                tp_incident = inc
                break
                
    assert_test("TEMPERATURE EXCURSION: Anomaly detected", tp_incident is not None, "Did not detect the main excursion")
    if tp_incident:
        assert_test("TEMPERATURE EXCURSION: Window overlaps", tp_incident['start_time'] <= simulated_end and tp_incident['end_time'] >= simulated_start, "No overlap")
        assert_test("TEMPERATURE EXCURSION: Peak temp approx 12C", abs(tp_incident['peak_temp'] - 12.0) < 0.5, f"Peak temp was {tp_incident['peak_temp']}")
    
    # 3. EXPOSURE WINDOW
    if tp_incident:
        expected_duration = int((tp_incident['end_time'] - tp_incident['start_time']).total_seconds() // 60) + 1
        assert_test("EXPOSURE WINDOW: Duration based on elapsed timestamps", tp_incident['duration'] == expected_duration, "Duration calculation mismatch")
    
    # 4. MISSING SENSOR DATA
    assert_test("MISSING SENSOR DATA: Gaps detected", len(gaps_list) == 2, f"Expected 2 gaps, found {len(gaps_list)}")
    if len(gaps_list) == 2:
        # Check first gap (the 15 min one dropped at index 400)
        assert_test("MISSING SENSOR DATA: Gap duration reported correctly", gaps_list[0]['duration_minutes'] == 16, f"Gap duration was {gaps_list[0]['duration_minutes']}")
        assert_test("MISSING SENSOR DATA: Missing count reported correctly", gaps_list[0]['missing_count'] == 15, f"Gap missing count was {gaps_list[0]['missing_count']}")
    
    # 5. GAP DURING INCIDENT
    if tp_incident:
        assert_test("GAP DURING INCIDENT: Incomplete data warning flagged", tp_incident['has_incomplete_data'] == True, "Did not flag incomplete data for overlapping gap")
        
    # 6. ANOMALY SCORE
    assert_test("ANOMALY SCORE: Score column generated", 'anomaly_score' in data.columns, "No anomaly_score column")
    if tp_incident:
        assert_test("ANOMALY SCORE: Score is negative for excursion", tp_incident['avg_score'] < 0, f"Score was {tp_incident['avg_score']}")
        
    # 7. REPORT
    if tp_incident:
        keys_exist = all(k in tp_incident for k in ['start_time', 'end_time', 'duration', 'peak_temp', 'avg_score', 'has_incomplete_data'])
        assert_test("REPORT: Summary contains all required fields", keys_exist, "Missing fields in report dictionary")
        
    # 8. DETECTION DELAY
    print("\n" + "-"*60)
    print("DETECTION DELAY ANALYSIS")
    print("-"*60)
    if tp_incident:
        delay = (tp_incident['start_time'] - simulated_start).total_seconds() / 60.0
        print(f"Simulated Incident Started:  {simulated_start}")
        print(f"AI Detection Triggered At:   {tp_incident['start_time']}")
        print(f"Detection Delay:             {delay} minutes")
        if delay > 0:
            print(f"Explanation: IsolationForest requires the temperature to drift sufficiently far from the 5°C norm before flagging it. This took {delay} minutes of temperature rise.")
    else:
        print("Could not calculate delay: Main incident not detected.")
    
    print(f"\nFalse Positive Anomaly Windows: {num_fp} (1-minute blips caused by IsolationForest thresholding the 5% random normal outliers)")
    
    print("\n" + "="*60)
    print(f"TESTS PASSED: {passed}")
    print(f"TESTS FAILED: {failed}")
    print("="*60)

if __name__ == "__main__":
    run_tests()
