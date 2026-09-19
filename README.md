# VaxGuard

### AI-Based Vaccine Cold-Chain Anomaly Monitor

VaxGuard is a decision-support prototype designed to monitor simulated
vaccine cold-chain sensor streams, detect abnormal temperature behavior,
reconstruct suspected exposure windows, and generate incident information
for human review.

## Problem

Temperature excursions and missing sensor readings can compromise
visibility into vaccine cold-chain conditions.

## What VaxGuard Does

- Monitors simulated temperature streams
- Detects anomalous temperature behavior
- Estimates possible exposure windows
- Detects sensor/data gaps
- Preserves historical incidents after recovery
- Provides evidence behind alerts
- Generates an incident report for human review

## Architecture

Sensor Simulation
       ↓
Data Processing
       ↓
Anomaly Detection
       ↓
Incident Reconstruction
       ↓
Operational Dashboard
       ↓
Human Review

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Isolation Forest

## Demo

![VaxGuard Dashboard](assets/dashboard.png)

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
