import http.server
import socketserver
import urllib.parse
import json
import os
import logging

# --- Oil Cooler Coefficient Data (Unchanged) ---
DISCHARGE_TEMP_COEFFS = {
'CXH01-50-199Y': [2.49E+01, -1.58E+00, 1.28E+00, -7.82E-02, 9.35E-02, -2.24E-02, -1.89E-03, 2.70E-03, -1.56E-03, 3.23E-04],
'CXH01-60-230Y': [2.49E+01, -1.58E+00, 1.28E+00, -7.82E-02, 9.36E-02, -2.24E-02, -1.89E-03, 2.70E-03, -1.57E-03, 3.23E-04],
'CXH01-70-264Y': [-3.30E+00, -2.13E+00, 3.36E+00, -9.21E-02, 1.34E-01, -7.43E-02, -1.87E-03, 3.02E-03, -2.16E-03, 7.51E-04],
'CXH01-80-298':  [4.01E+00, -1.38E+00,2.48E+00,-6.08E-02,9.44E-02,-5.16E-02,-1.20E-03,2.06E-03,-1.56E-03,5.42E-04],
'CXH01-90-340Y': [3.30E+01, 7.88E-01,3.61E-01, 1.67E-02, -2.56E-02, 4.36E-03, -5.03E-04, 1.65E-04, -1.14E-04, 8.64E-05],
'CXH01-100-370Y': [3.30E+01, 7.88E-01,3.61E-01, 1.67E-02, -2.56E-02,4.36E-03, -5.03E-04, 1.65E-04, -1.14E-04, 8.64E-05],
'CXH51-110-398Y': [5.22E+01, -8.27E-02,-1.01E+00, -1.80E-03, 1.70E-02, 3.36E-02, -7.38E-04, 9.43E-04, -6.84E-04, -9.95E-05],
'CXH51-125-468Y': [3.69E+01, -5.78E-01,3.31E-01,-3.08E-02, 4.77E-02, -7.47E-04, -1.01E-03, 1.57E-03, -1.07E-03, 1.71E-04],
'CXH51-140-538Y': [3.11E+01,5.52E-01,4.53E-01,-8.68E-03,-1.14E-02,1.56E-03, -8.02E-04,1.00E-03,-2.91E-04,1.12E-04],
'CXH91-160-620Y': [3.10E+01,-1.02E-01,4.42E-01, -1.35E-02, 2.16E-02, 7.50E-04, -1.04E-03, 1.10E-03, -6.59E-04, 1.21E-04],
'CXH91-180-702Y': [3.17E+01, -1.30E-01, 4.54E-01, -1.40E-02, 2.26E-02, 4.46E-04, -1.07E-03, 1.14E-03, -6.83E-04, 1.26E-04],
'CXH91-210-810Y': [3.72E+01, 2.32E-01, 1.22E-01, -8.74E-03, 2.23E-03, 8.40E-03, -1.07E-03, 8.51E-04, -3.78E-04, 5.41E-05],
'CXH91-240-912Y': [4.98E+01, 2.27E-01, -7.12E-01, -1.35E-02, 3.61E-03, 2.65E-02, -7.67E-04, 9.37E-04, -3.91E-04, -8.28E-05],
'CXH91-280-1000Y': [4.58E+01, -5.57E-02, -5.68E-01, -1.08E-02, 1.23E-02, 2.49E-02, -7.45E-04, 9.79E-04, -5.37E-04, -5.63E-05],
'CXH91-310-1085Y': [2.62E+01, 5.27E-01, 7.78E-01, -2.16E-04, -1.36E-02, -3.72E-03, -5.67E-04, 6.41E-04, -2.15E-04, 1.28E-04],
'CXH02-70-199Y': [3.43E+01, -6.28E-01, 6.26E-01, -4.02E-02, 5.39E-02, -8.24E-03, -1.41E-03, 2.02E-03, -1.20E-03, 2.31E-04],
'CXH02-80-230Y': [3.43E+01, -6.28E-01, 6.26E-01, -4.02E-02, 5.39E-02, -8.24E-03, -1.41E-03, 2.02E-03, -1.20E-03, 2.31E-04],
'CXH02-90-264Y': [3.80E+01, 2.96E-01, 9.26E-02, -5.43E-03, 1.97E-03, 9.08E-03, -7.47E-04, 9.23E-04, -4.78E-04, 6.00E-05],
'CXH02-100-298Y': [-5.39E+00, -2.08E+00, 3.58E+00, -7.45E-02, 1.36E-01, -8.07E-02, -1.49E-03, 2.78E-03, -2.26E-03, 8.12E-04],
'CXH02-120-340Y': [4.35E+01, 8.59E-01, -3.30E-01, 5.61E-03, -2.71E-02, 1.81E-02, -5.71E-04, 6.95E-04, -1.56E-04, -2.67E-06],
'CXH52-110-316Y': [5.01E+01, -1.22E+00, -6.58E-01, -2.29E-02, 6.23E-02, 2.35E-02, -8.94E-04, 1.50E-03, -1.20E-03, -6.64E-06],
'CXH52-125-372Y': [1.76E+01, -1.04E+00, 1.52E+00, -3.44E-02, 6.43E-02, -2.61E-02, -1.17E-03, 1.78E-03, -1.26E-03, 3.54E-04],
'CXH52-140-428Y': [1.36E+01, -5.98E-01, 1.65E+00, -2.34E-02, 3.90E-02, -2.46E-02, -7.62E-04, 1.34E-03, -9.26E-04, 3.13E-04],
'CXH52-160-468Y': [4.58E+01, -1.19E-01, -1.93E-01, -1.78E-02, 2.60E-02, 1.11E-02, -8.77E-04, 1.37E-03, -8.65E-04, 9.29E-05],
'CXH52-180-538Y': [3.90E+01, 1.12E+00, -2.92E-01, 3.09E-02, -4.76E-02, 2.18E-02, -1.49E-04, -5.68E-05, 1.90E-04, -6.04E-05],
'CXH92-180-545Y': [7.77E+00, -1.41E+00, 2.13E+00, -5.11E-02, 8.66E-02, -3.93E-02, -1.37E-03, 2.28E-03, -1.59E-03, 4.55E-04],
'CXH92-210-620Y': [3.81E+01, 3.84E-01, -4.04E-02, -2.86E-03, 4.62E-04, 1.12E-03, -7.82E-04, 9.45E-04, -4.58E-04, 4.87E-05],
'CXH92-240-702Y': [3.90E+01, 3.69E-01, -4.27E-02, -3.04E-03, 8.88E-04, 1.12E-02, -8.05E-04, 9.77E-04, -4.76E-04, 5.22E-05],
'CXH92-280-810Y': [1.29E+01, -4.47E-01, 1.96E+00, -1.36E-02, 3.26E-02, -3.48E-02, -5.98E-04, 1.08E-03, -7.87E-04, 3.84E-04],
'CXH92-300-912Y': [4.17E+01, 2.63E-01, -2.15E-01, -3.22E-04, 1.74E-03, 1.54E-02, -8.28E-04, 8.23E-04, -4.14E-04, 8.09E-06],
'CXH92-310-1000Y': [4.84E+01, 2.66E-01, -7.28E-01, 7.32E-04, -1.84E-03, 2.81E-02, -6.07E-04, 7.72E-04, -4.01E-04, -7.47E-05],
}

def calculate_discharge_temp_and_advise(compressor_model, sst, sdt):
    if compressor_model not in DISCHARGE_TEMP_COEFFS:
        return None, "Discharge temp data not available for this model."
    coeffs = DISCHARGE_TEMP_COEFFS[compressor_model]
    C1, C2, C3, C4, C5, C6, C7, C8, C9, C10 = coeffs
    s = sst; d = sdt
    discharge_temp = (C1 + (C2*s) + (C3*d )+ (C4*s**2) + (C5*s*d) + (C6*d**2 )+ (C7*s**3) + (C8*s**2*d) + (C9*s*d**2) + (C10*d**3))
    if discharge_temp <= 70: advice = "No oil cooler required."
    elif 70 < discharge_temp <= 87: advice = "Liquid injection required."
    else: advice = "Oil cooler required."
    return discharge_temp, advice

def apply_corrections_and_get_compressor_family(chiller_type_series, series_subtype, series_model_family_from_dropdown):
    evaporator_corr = 0; condenser_corr = 0
    compressor_family_for_envelope = series_model_family_from_dropdown
    if chiller_type_series == "air": 
        if series_subtype in ["kas", "kaa"]: evaporator_corr = -3.5
        elif series_subtype == "kaf": evaporator_corr = -1.5
        condenser_corr = +15 
    elif chiller_type_series == "water": 
        if series_subtype == "kwk": evaporator_corr = -1.5
        elif series_subtype == "kwi": evaporator_corr = -1.5
        elif series_subtype == "kws": evaporator_corr = -3.5
        condenser_corr = +2 
    return evaporator_corr, condenser_corr, compressor_family_for_envelope

def check_specific_motor_sdt_and_advise_final(selected_compressor_model, cond_temp_for_calc):
    lower_motor_models_cxh = [
        "CXH01-50-199Y", "CXH01-60-230Y", "CXH01-70-264Y", "CXH01-80-298Y", "CXH01-90-340Y", "CXH01-100-370Y",
        "CXH51-110-398Y", "CXH51-125-4687", "CXH51-140-538Y", 
        "CXH91-160-620Y", "CXH91-180-702Y", "CXH91-210-810Y", "CXH91-240-912Y", "CXH91-280-1000Y", "CXH91-310-1085Y",
        "CXHI01-50-199Y", "CXHI01-60-230Y", "CXHI01-70-264Y", "CXHI01-80-298Y", "CXHI01-90-340Y", "CXHI01-100-370Y",
        "CXHI51-110-398Y", "CXHI51-125-4687", "CXHI51-140-538Y", 
        "CXHI91-160-620Y", "CXHI91-180-702Y", "CXHI91-210-810Y", "CXHI91-240-912Y", "CXHI91-280-1000Y", "CXHI91-310-1085Y",
        "KXI01-50-230Y", "KXI01-60-264Y", "KXI01-70-298Y", "KXI101-80-340Y", "KXI101-90-370Y", "KXI151-100-428Y", "KXI151-110-468Y", "KXI151-125-538Y", "KXI91-140-620Y", "KXI91-160-702Y", "KXI91-180-810Y", "KXI91-210-912Y", "KXI91-240-1000Y", "KXI191-280-1085Y", "KXI102-50-199Y",
        "KXH01-50-230Y", "KXH01-60-264Y", "KXH01-70-298Y", "KXH01-80-340Y", "KXH01-90-370Y", "KXH51-100-428Y", "KXH51-110-468Y", "KXH51-125-538Y", "KXH91-140-620Y", "KXH91-160-702Y", "KXH91-180-810Y", "KXH91-210-912Y", "KXH91-240-1000Y", "KXH91-280-1085Y", "KXH02-50-199Y"
    ]
    higher_motor_models_cxh = [
        "CXH02-70-199Y", "CXH02-80-230Y", "CXH02-90-264Y", "CXH02-100-298Y", "CXH02-120-340Y", "CXH52-110-316Y", "CXH52-125-372Y", "CXH52-140-428Y", "CXH52-160-4687", "CXH52-180-538Y", "CXH92-180-545Y", "CXH92-210-620Y", "CXH92-240-702Y", "CXH92-280-810Y", "CXH92-300-912Y", "CXH92-310-1000Y", "CXHI02-70-199Y", "ICXHI02-80-230Y", "CXHI02-90-264Y", "CXHI02-100-298Y", "CXHI02-120-340Y", "CXHI52-110-316Y", "CXHI52-125-372Y", "CXHI52-140-428Y", "CXHI52-160-4687", "CXHI52-180-538Y", "CXHI92-180-545Y", "CXHI92-210-620Y", "CXHI92-240-702Y", "CXHI92-280-810Y", "CXHI92-300-912Y", "CXHI92-310-1000Y"
    ]
    abs_sdt_limit_lower_motor = 65.0 
    abs_sdt_limit_higher_motor = 70.0
    sdt_rule1_max = 55.0
    sdt_rule2_range_max = 65.0
    sdt_rule3_range_max = 70.0
    is_invalid_now = False; message = ""
    model_type = "unknown"; current_model_abs_limit = float('inf')
    if selected_compressor_model in lower_motor_models_cxh: model_type = "lower"
    elif selected_compressor_model in higher_motor_models_cxh: model_type = "higher"
    if model_type == "lower": current_model_abs_limit = abs_sdt_limit_lower_motor
    elif model_type == "higher": current_model_abs_limit = abs_sdt_limit_higher_motor
    if cond_temp_for_calc > current_model_abs_limit:
        is_invalid_now = True
        message = (f"OUT OF ENVELOPE. Selected motor ({selected_compressor_model}) absolute SDT limit ({current_model_abs_limit}°C) exceeded. Calculated SDT is {cond_temp_for_calc:.1f}°C.")
    else:
        if cond_temp_for_calc <= sdt_rule1_max:
            message = "The operating conditions are within the compressor working envelope."
            if model_type == "higher": 
                message = ("The operating conditions are within the compressor working envelope. Higher motor selected. Due to lower lift condition, consider lower motor.")
        elif sdt_rule1_max < cond_temp_for_calc <= sdt_rule2_range_max:
            message = ("The operating conditions are within the compressor working envelope. Due to higher lift, consider the higher motor.")
        elif model_type == "higher" and sdt_rule2_range_max < cond_temp_for_calc <= sdt_rule3_range_max :
            message = "The operating conditions for the selected higher motor are within the compressor working envelope."
        elif not message: 
            if model_type == "unknown" and selected_compressor_model:
                message = f"Operating conditions are within the general envelope. Specific SDT advice for {selected_compressor_model} at {cond_temp_for_calc:.1f}°C requires Kirloskar data."
            else: 
                message = "The operating conditions are within this compressor's working envelope."
    return is_invalid_now, message

def check_envelope(refrigerant, compressor_family, selected_compressor_model, evap_temp, cond_temp_for_calc):
    is_geometrically_out = True 
    geometric_status_message = "Operating point is outside defined GEOMETRIC envelopes." 
    envelope_type_applied_text = "N/A" 
    if compressor_family in ["KXI", "KXH"]:
        if refrigerant in ["R134a"]:
            envelope_type_applied_text = "R134a (KXI/KXH)"
            if (-15 <= evap_temp <= 12.3 and 20 <= cond_temp_for_calc <= 52 and (0.629 * evap_temp + 21.258 - cond_temp_for_calc) < 0): is_geometrically_out = False
    if compressor_family in ["KXI", "KXH"]:
        if refrigerant in ["R513A"]:
            envelope_type_applied_text = "R513A (KXI/KXH)"
            if (-15 <= evap_temp <= 12.3 and 20 <= cond_temp_for_calc <= 52 and (0.629 * evap_temp + 21.258 - cond_temp_for_calc) < 0): is_geometrically_out = False
        elif refrigerant in ["R1234Ze"]:
            envelope_type_applied_text = "R1234Ze (KXI/KXH)"
            if (-15 <= evap_temp <= 12.5 and 20 <= cond_temp_for_calc <= 50 and (0.5161 * evap_temp + 21.548 - cond_temp_for_calc) < 0): is_geometrically_out = False
    elif compressor_family in ["CXH", "CXHI"]:
        if refrigerant in ["R134a", "R513A"]:
            envelope_type_applied_text = "R134a / R513A Primary (CXH/CXHI)"
            if (-20 <= evap_temp <= 13 and 20 <= cond_temp_for_calc <= 65 and (1.625 * evap_temp + 84.5 - cond_temp_for_calc) > 0 and (0.9285 * evap_temp + 21.857 - cond_temp_for_calc) <= 0):
                is_geometrically_out = False
            else: 
                envelope_type_applied_text = "R134a / R513A Fallback (CXH/CXHI)"
                if (-20 <= evap_temp <= 25 and 20 <= cond_temp_for_calc <= 70 and (1.5833 * evap_temp + 82.6664 - cond_temp_for_calc) >= 0 and (0.85185 * evap_temp + 21.7 - cond_temp_for_calc) <= 0):    
                    is_geometrically_out = False
                    geometric_status_message = f"Operating point is WITHIN the {envelope_type_applied_text} GEOMETRIC envelope (using fallback definition)."
        elif refrigerant == "R407C":
            envelope_type_applied_text = "R407C (CXH/CXHI)"
            if (-25 <= evap_temp <= 12.5 and 20 <= cond_temp_for_calc <= 60 and (12 * evap_temp + 1116 - 17 * cond_temp_for_calc) >= 0 and (evap_temp + 20 - cond_temp_for_calc) <= 0):
                is_geometrically_out = False
    if not is_geometrically_out and ("fallback" not in geometric_status_message and geometric_status_message == "Operating point is outside defined GEOMETRIC envelopes."):
         geometric_status_message = f"Operating point is WITHIN the {envelope_type_applied_text} GEOMETRIC envelope."
    elif is_geometrically_out: 
         geometric_status_message = f"Operating point is OUT of the {envelope_type_applied_text} GEOMETRIC envelope."
    is_sdt_invalid_for_model, final_user_sdt_message = \
        check_specific_motor_sdt_and_advise_final(selected_compressor_model, cond_temp_for_calc)
    is_selection_invalid_overall_api = is_geometrically_out or is_sdt_invalid_for_model
    trigger_critical_popup_api = is_selection_invalid_overall_api
    if is_geometrically_out:
        overall_status_for_display_api = geometric_status_message
        motor_advice_for_display_api = "Point is outside the compressor family's geometric operating envelope. Adjust conditions or select a different compressor/family."
    else:
        overall_status_for_display_api = final_user_sdt_message
        motor_advice_for_display_api = final_user_sdt_message
    final_api_in_envelope_status = not is_selection_invalid_overall_api
    return {
        "in_envelope": final_api_in_envelope_status,
        "status_message": overall_status_for_display_api,  
        "higher_motor_required": trigger_critical_popup_api, 
        "motor_message": motor_advice_for_display_api, 
        "envelope_type_applied": envelope_type_applied_text
    }

# For brevity, I'll use placeholders here, but in the actual edit, all the logic from index.py will be copied as-is.

# --- Begin copied logic from index.py ---
# (Insert all the calculation functions and DISCHARGE_TEMP_COEFFS here)
# --- End copied logic ---

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == '/api/calculate_chiller':
            self.handle_api_calculate_chiller(parsed_path)
        else:
            # Serve static files (index.html, style.css, script.js, PDFs, images)
            if self.path == '/':
                self.path = '/index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def handle_api_calculate_chiller(self, parsed_path):
        try:
            query = urllib.parse.parse_qs(parsed_path.query)
            def get_param(name, default=None):
                return query.get(name, [default])[0]
            chiller_type_series = get_param('typeSeries')
            series_subtype = get_param('seriesSubtype')
            series_model_family_dd = get_param('seriesModel')
            compressor_selection_specific = get_param('compressorSelection')
            refrigerant = get_param('refrigerant')
            power_supply = get_param('powerSupply')
            evap_lwt_input_str = get_param('evaporatorLWT')
            cond_lwt_input_str = get_param('condenserLWT')
            desuperheater = get_param('desuperheater', 'No')
            required_params_map = {
                "Type of Series": chiller_type_series,
                "Series Subtype": series_subtype,
                "Compressor Family": series_model_family_dd,
                "Refrigerant": refrigerant,
                "Power Supply": power_supply,
                "Evaporator LWT": evap_lwt_input_str,
                "Condenser LWT/Ambient": cond_lwt_input_str,
                "DE Super Heater": desuperheater
            }
            missing_params = [name for name, value in required_params_map.items() if not value]
            if missing_params:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Missing: {', '.join(missing_params)}", "details": f"Received: {query}"}).encode())
                return
            try:
                evap_lwt_input = float(evap_lwt_input_str)
                cond_lwt_input = float(cond_lwt_input_str)
            except ValueError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid temperature input."}).encode())
                return
            evap_corr, cond_corr, compressor_family_for_env = apply_corrections_and_get_compressor_family(
                chiller_type_series, series_subtype, series_model_family_dd)
            evap_temp_for_calc = evap_lwt_input + evap_corr
            cond_temp_for_calc = cond_lwt_input + cond_corr
            envelope_data = check_envelope(refrigerant, compressor_family_for_env,
                compressor_selection_specific, evap_temp_for_calc, cond_temp_for_calc)
            discharge_temp, oil_cooler_advice = calculate_discharge_temp_and_advise(
                compressor_selection_specific, evap_temp_for_calc, cond_temp_for_calc)
            display_discharge_temp_str = f"{discharge_temp:.1f} °C" if discharge_temp is not None else "N/A"
            output = {
                "inputs": {
                    "chiller_type_series": chiller_type_series,
                    "series_subtype": series_subtype,
                    "series_model_family": series_model_family_dd,
                    "compressor_selection_specific": compressor_selection_specific,
                    "refrigerant": refrigerant,
                    "power_supply": power_supply,
                    "evap_lwt_input": evap_lwt_input,
                    "cond_lwt_input": cond_lwt_input,
                    "desuperheater": desuperheater
                },
                "calculated_values": {
                    "evaporator_sat_temp": evap_temp_for_calc,
                    "condenser_sat_temp": cond_temp_for_calc,
                    "evap_correction_applied": evap_corr,
                    "cond_correction_applied": cond_corr
                },
                "envelope_check": envelope_data,
                "display_chiller_type": f"{chiller_type_series.capitalize()} Cooled Chiller ({series_subtype.upper()})",
                "display_series_model_family": series_model_family_dd,
                "display_compressor_specific_model": compressor_selection_specific if compressor_selection_specific else "Not Specified",
                "display_refrigerant": refrigerant,
                "display_evap_lwt": evap_lwt_input,
                "display_cond_lwt_or_ambient": cond_lwt_input,
                "display_evap_calculated_sat_temp": evap_temp_for_calc,
                "display_cond_calculated_sat_temp": cond_temp_for_calc,
                "display_envelope_status_msg": envelope_data["status_message"],
                "display_motor_message": envelope_data["motor_message"],
                "display_envelope_type_applied": envelope_data["envelope_type_applied"],
                "display_discharge_temp": display_discharge_temp_str,
                "display_oil_cooler_advice": oil_cooler_advice
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(output).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Internal server error.", "details": str(e)}).encode())

if __name__ == '__main__':
    PORT = 5000
    logging.basicConfig(level=logging.INFO)
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
