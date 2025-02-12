import pandas as pd
import re

def clean_column_names(df) -> pd.DataFrame:
    """Renames columns using a manual map, and cleans the rest automatically."""
    column_map = {
        'OBJECTID': 'object_id',
        '* Damage': 'damage',
        '* Street Number': 'street_number',
        '* Street Name': 'street_name',
        '* Street Type (e.g. road, drive, lane, etc.)': 'street_type',
        'Street Suffix (e.g. apt. 23, blding C)': 'street_suffix',
        '* City': 'city',
        'State': 'state',
        'Zip Code': 'zip_code',
        '* CAL FIRE Unit': 'cal_fire_unit',
        'County': 'county',
        'Community': 'community',
        'Battalion': 'battalion',
        '* Incident Name': 'incident_name',
        'Incident Number (e.g. CAAEU 123456)': 'incident_number',
        'Incident Start Date': 'incident_start_date',
        'Hazard Type': 'hazard_type',
        'If Affected 1-9% - Where did fire start?': 'fire_start_location',
        'If Affected 1-9% - What started fire?': 'fire_cause',
        'Structure Defense Actions Taken': 'defense_actions',
        '* Structure Type': 'structure_type',
        'Structure Category': 'structure_category',
        '# Units in Structure (if multi unit)': 'num_units',
        '# of Damaged Outbuildings < 120 SQFT': 'damaged_outbuildings',
        '# of Non Damaged Outbuildings < 120 SQFT': 'non_damaged_outbuildings',
        '* Roof Construction': 'roof_construction',
        '* Eaves': 'eaves',
        '* Vent Screen': 'vent_screen',
        '* Exterior Siding': 'exterior_siding',
        '* Window Pane': 'window_pane',
        '* Deck/Porch On Grade': 'deck_on_grade',
        '* Deck/Porch Elevated': 'deck_elevated',
        '* Patio Cover/Carport Attached to Structure': 'patio_carport_attached',
        '* Fence Attached to Structure': 'fence_attached',
        'Distance - Propane Tank to Structure': 'distance_to_propane_tank',
        'Distance - Residence to Utility/Misc Structure &gt; 120 SQFT': 'distance_to_utility_structure',
        'Fire Name (Secondary)': 'fire_name_secondary',
        'APN (parcel)': 'apn',
        'Assessed Improved Value (parcel)': 'assessed_value',
        'Year Built (parcel)': 'built_in',
        'Site Address (parcel)': 'site_address',
        'GLOBALID': 'global_id',
        'Latitude': 'latitude',
        'Longitude': 'longitude',
        'x': 'x_coord',
        'y': 'y_coord'
    }

    cleaned_columns = []
    for col in df.columns:
        if col in column_map:
            cleaned_columns.append(column_map[col])  # Use manual mapping
        else:
            cleaned_col = re.sub(r'[^a-zA-Z0-9]', '_', col).lower().strip('_')  # Clean others
            cleaned_columns.append(cleaned_col)

    # ✅ 3. Apply cleaned column names
    df.columns = cleaned_columns
    
    return df