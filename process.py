import pandas as pd
from pathlib import Path
from config import Config

def format_raw_file(file):
    headers = ["Time", "Crane Tilt Up", "Crane Tilt Down", "Crane Clamp Close", "Crane Clamp Open", "Rod Clamp Open", "Rod Clamp Close",
               "Casing Clamp Close", "Casing Clamp Open", "Start-up", "Switch Aux. 2", "Switch Feeder Guide Open", "Switch Feeder Guide Close",
               "Switch Breakout 1 IN raw value", "Switch Breakout 1 OUT raw value", "Switch Breakout 4 IN raw value", "Switch Breakout 4 OUT raw value",
               "Switch Override Feed", "Switch Threading Mode", "Switch Esp Rotary IN", "Switch Esp Rotary OUT", "Switch Fine Feed", "Switch Aux. 1",
               "Switch Water Pump", "Switch Percussion Close", "Switch Percussion Open", "Feeder Hook IN", "Feeder Hook OUT", "Mud Pump Mode", "Mud Pump Start",
               "Crane Stick Up (mv)", "Crane Stick Down (mV)", "Crane Swing Left (mV)", "Crane Swing Right (mV)", "Crane Extension IN (mV)",
               "Crane Extension OUT (mV)", "Crane Rotary Left (mV)", "Crane Rotary Right (mV)", "Feed Pressure Pot (%)", "Joystick 1 Rocker (%)",
               "Joystick 1 Axe X (%)", "Joystick 1 Axe Y raw value (%)", "Joystick 2 Rocker (%)", "Joystick 2 Axe X (%)", "Joystick 2 Axe Y (%)",
               "Joystick 3 Rocker (%)", "Joystick 3 Axe X raw value (%)", "Joystick 3 Axe Y (%)", "Joystick 4 Rocker (%)", "Joystick 4 Axe X (%)",
               "Joystick 4 Axe Y (%)", "Joystick Feed raw value (%)", "Joystick hoist raw value (%)", "Joystick JIB raw value (%)", "Joystick Rotation 1 raw value (%)",
               "Joystick Rotation 2 raw value (%)", "Pot Aux. 2 (%)", "Pot Fine Feed (%)", "Pot Aux. 1 (%)", "Pot Water Pump (%)", "Joystick Left Traction (%)", "Joystick Right Traction (%)",
               "RPM Rotation 1 raw value (rpm)", "RPM Rotation 2  raw value (rpm)", "Hyd. Oil Temp (°F)", "Rotation 1 pressure raw value (psi)", "Rotation 2 pressure raw value (psi)",
               "Air pressure raw value (psi)", "Feed pressure raw value (psi)", "Feeder position sensor (mV)", "Machine mode raw value", "Penetration rate (ft/hrs)",
               "RPM Turtle Mode", "RPM Rabbit Mode", "RPM Auto Mode", "Functions Enable", "Functions Disable", "Low Fuel Level", "Button Raise RPM",
               "Button Lower RPM", "Fuel Level (%)", "Rotation 1 Speed List", "Rotation 2 Speed List", "Drill Footage (ft)", "Hole Length (ft)"]

    df = pd.read_csv(file, delimiter=';', header=None)
    file = Path(file)

    output_path = Path(Config.FORMATTED_DIR) 
    output_path.mkdir(parents=True, exist_ok=True)
    file_formatted = output_path/f"{file.stem}_formatted{file.suffix}"

    original_cols = df.shape[1]
    expected_cols = len(headers)

    # 3) Normalize column count (handle trailing/extra semicolons)
    if original_cols > expected_cols:
        # Too many columns in file → keep first N
        df = df.iloc[:, :expected_cols]
    elif original_cols < expected_cols:
        # Too few columns → pad with empty columns so we still match headers
        for i in range(expected_cols - original_cols):
            df[f"_extra_{i}"] = pd.NA

    df.columns = headers
    df.insert(1, 'Date', '')

    df['Date'] = (
        pd.to_datetime(df['Time'], errors='coerce')
        .dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')  # re-format ISO
    )
    df.to_csv(file_formatted, sep=',', index=False, encoding='utf-8')
    return file_formatted