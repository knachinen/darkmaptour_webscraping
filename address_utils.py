import re
import json
import pandas as pd
from fuzzywuzzy import fuzz

# --- Constants ---
# ADDRESS_POSTFIXES = ['특별시', '광역시', '도', '시', '군', '구', '읍', '면', '동', '가', '리', '로']
ADDRESS_POSTFIXES = ['특별시', '광역시', '시', '경찰서', '지법']
# --- End Constants ---

def get_json(json_text: str, verbose: bool = False) -> dict:
    """Parse JSON text into a Python dictionary.
    Strips markdown code block indicators if present, and attempts to extract
    the first valid JSON object from the string.

    Args:
        json_text (str): JSON text to parse.
        verbose (bool, optional): If True, print JSON text. Defaults to False.

    Returns:
        dict: Parsed JSON data as a dictionary, or None if parsing fails.
    """
    if verbose:
        print("Input JSON text:")
        print(json_text)

    # Strip markdown code block indicators if present
    if json_text.strip().startswith('```json') and json_text.strip().endswith('```'):
        json_text = json_text.strip()[len('```json'):-len('```')].strip()
    elif json_text.strip().startswith('```') and json_text.strip().endswith('```'):
        json_text = json_text.strip()[len('```'):-len('```')].strip()

    # Attempt to find and extract the first JSON object using a non-greedy regex
    # This handles cases where there's extra text before or after the JSON,
    # or if the LLM outputs multiple JSON-like structures.
    match = re.search(r'\{(.*?)\}', json_text, re.DOTALL)
    if not match:
        print("Error: No JSON object found in the text.")
        return None
    
    json_candidate = match.group(0)

    try:
        json_data = json.loads(json_candidate)
    except json.JSONDecodeError as e:
        print(f"Error loading JSON from candidate '{json_candidate[:100]}...': {e}")
        return None
    except Exception as e:
        print("An unknown error occurred:", e)
        return None

    return json_data

def strip_address_postfixes(address_string: str) -> str:
    """
    Removes common Korean address postfixes from the end of an address string.
    """
    for postfix in ADDRESS_POSTFIXES:
        if address_string.endswith(postfix):
            return address_string[:-len(postfix)]
    return address_string

def normalize_address_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes address columns in the DataFrame for better matching.
    Drops 'lv5' and converts 'object' columns to 'category'.
    Creates a 'full_address' column by concatenating lv1-lv4.
    """
    df_copy = df.copy()

    # Drop 'lv5' if it exists and is all NaN
    if 'lv5' in df_copy.columns and df_copy['lv5'].isnull().all():
        df_copy = df_copy.drop(columns=['lv5'])

    # Fill NaN values with empty string BEFORE converting to category
    # This ensures '' is a valid category if it's introduced by fillna
    for col in ['lv1', 'lv2', 'lv3', 'lv4']:
        if col in df_copy.columns:
            # Ensure the column is of object type before filling with string,
            # otherwise fillna on category might still cause issues if '' is not a category
            if df_copy[col].dtype != 'object':
                df_copy[col] = df_copy[col].astype(str)
            df_copy[col] = df_copy[col].fillna('')

    # Create a 'full_address' column
    df_copy['full_address'] = df_copy[['lv1', 'lv2', 'lv3', 'lv4']].agg(' '.join, axis=1).str.strip().str.replace(r'\s+', ' ', regex=True)

    # Convert object columns to category dtype for memory efficiency
    # Now, if '' was introduced by fillna, it will be a category
    for col in ['lv0', 'lv1', 'lv2', 'lv3', 'lv4']:
        if col in df_copy.columns and df_copy[col].dtype == 'object': # Check dtype again in case it changed
            df_copy[col] = df_copy[col].astype('category')

    return df_copy

def normalize_rag_address(rag_address_string: str) -> str:
    """
    Normalizes the address string extracted from RAG output.
    This includes stripping common address postfixes and extra spaces.
    """
    # First, strip common address postfixes
    stripped_address = strip_address_postfixes(rag_address_string)
    # Then, remove extra spaces
    normalized_address = re.sub(r'\s+', ' ', stripped_address.strip())
    return normalized_address

def extract_lv0_from_rag_address(rag_address: str, df_addr_normalized: pd.DataFrame, threshold: int) -> str | None:
    """
    Attempts to extract a matching lv0 (province/city) from the rag_address
    by comparing it against unique lv0 values in df_addr_normalized.
    """
    unique_lv0s = df_addr_normalized['lv0'].unique()
    
    best_lv0_match = None
    best_lv0_score = 0

    for lv0_name in unique_lv0s:
        # Use partial_ratio as lv0 might be part of a larger string in rag_address
        score = fuzz.partial_ratio(lv0_name, rag_address)
        if score > best_lv0_score and score >= threshold: # Use FUZZY_MATCH_THRESHOLD for lv0 matching
            best_lv0_score = score
            best_lv0_match = lv0_name
            
    return best_lv0_match
