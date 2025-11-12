import logging
import pandas as pd
from fuzzywuzzy import fuzz

from address_utils import (
    strip_address_postfixes,
    normalize_rag_address,
    extract_lv0_from_rag_address
)

# --- Configuration Constants ---
FUZZY_MATCH_THRESHOLD = 80
STRONG_FULL_MATCH_THRESHOLD = 90
LV0_COMPOSITE_BONUS = 20
EXACT_WORD_MATCH_BONUS = 10
# --- End Configuration Constants ---

class AddressMatcher:
    def __init__(self, df_addr_optimized: pd.DataFrame):
        self.df_addr_optimized = df_addr_optimized

    def find_matching_address(self, rag_address: str) -> tuple[str | None, float, pd.Series | None]:
        logging.debug(f"Entering find_matching_address function with rag_address: '{rag_address}'")

        # --- Hierarchical Search Logic ---
        target_df = self.df_addr_optimized.copy()
        identified_lv0 = extract_lv0_from_rag_address(rag_address, self.df_addr_optimized, FUZZY_MATCH_THRESHOLD)

        if identified_lv0:
            target_df = self.df_addr_optimized[self.df_addr_optimized['lv0'] == identified_lv0].copy()
            if target_df.empty:
                target_df = self.df_addr_optimized.copy() # Fallback if filter results in empty DF
        # --- End Hierarchical Search Logic ---

        best_match = None
        best_score = 0
        matched_row = None

        # Stage 1: Initial Full Fuzzy Match Attempt
        for index, row in target_df.iterrows():
            current_full_address = row['full_address']
            score = fuzz.ratio(rag_address, current_full_address)
            if score > best_score and score >= FUZZY_MATCH_THRESHOLD:
                best_score = score
                best_match = current_full_address
                matched_row = row
        
        # If a strong full match is found, return it immediately
        if best_score >= STRONG_FULL_MATCH_THRESHOLD:
            logging.debug(f"  Strong full match found: '{best_match}' with score {best_score}")
            return best_match, best_score, matched_row

        # Stage 2: Component-wise Matching and Composite Scoring (if no strong full match)
        # Reset best_score and related variables for composite scoring
        best_score = 0 
        best_match = None
        matched_row = None

        normalized_rag_addr_for_partial = normalize_rag_address(rag_address)

        for index, row in target_df.iterrows():
            composite_score = 0
            current_full_address = row['full_address'] # For logging/return if this becomes the best

            # Score for lv0 match (already used for filtering, but can contribute to composite score)
            # If lv0 was identified and matched, give it a base score
            if identified_lv0 and row['lv0'] == identified_lv0:
                composite_score += LV0_COMPOSITE_BONUS

            # Iterate through lv1 to lv4 components
            for level_col in ['lv1', 'lv2', 'lv3', 'lv4']:
                component = row[level_col]
                if pd.notna(component) and component:
                    normalized_component = strip_address_postfixes(component)
                    
                    if len(normalized_component) > 1:
                        # Use fuzz.WRatio for more robust component matching
                        component_score = fuzz.WRatio(normalized_component, normalized_rag_addr_for_partial)
                        
                        # If component matches well, add to composite score, prioritizing longer matches
                        if component_score >= FUZZY_MATCH_THRESHOLD:
                            # Add score, weighted by length to prioritize more specific matches
                            composite_score += component_score * (len(normalized_component) / len(normalized_rag_addr_for_partial))
                            
                            # Add a bonus for exact word matches (using a simpler check for now)
                            if normalized_component in normalized_rag_addr_for_partial:
                                composite_score += EXACT_WORD_MATCH_BONUS

            # Update best composite score
            if composite_score > best_score:
                best_score = composite_score
                best_match = current_full_address
                matched_row = row

        if best_match:
            logging.debug(f"  Best composite match found: '{best_match}' with score {best_score}")
            return best_match, best_score, matched_row

        return None, 0, None