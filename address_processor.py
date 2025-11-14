import logging
import pandas as pd
from geopy.geocoders import Nominatim

from address_utils import (
    normalize_address_df,
    normalize_rag_address,
    strip_address_postfixes
)
from llm_extractor import LLMExtractor
from address_matcher import AddressMatcher

class AddressProcessor:
    def __init__(self, df_addr: pd.DataFrame, llm_model: str = 'gemma3:1b'):
        self.llm_extractor = LLMExtractor(model=llm_model)
        self.df_addr_optimized = normalize_address_df(df_addr)
        self.address_matcher = AddressMatcher(self.df_addr_optimized)
        self.geolocator = Nominatim(user_agent="my_geocoder")

    def process_text(self, text_content: str) -> dict:
        result_dict = {
            'original_text': text_content,
            'address': None, 'who': None, 'when': None, 'where': None, 'what': None, 'other': None,
            'matched_address_display': None, 'match_score': None, 'matched_full_address_df': None,
            'matched_lv0': None, 'matched_lv1': None, 'matched_lv2': None, 'matched_lv3': None, 'matched_lv4': None,
            'latitude': None, 'longitude': None, 'geocoded_address': None
        }

        text = text_content # Assuming sa.clean_text is not needed here or handled elsewhere

        rag_json = self.llm_extractor.extract_info(text=text)

        if rag_json:
            result_dict['address'] = rag_json.get('address')
            result_dict['who'] = rag_json.get('who')
            result_dict['when'] = rag_json.get('when')
            result_dict['where'] = rag_json.get('where')
            result_dict['what'] = rag_json.get('what')
            result_dict['other'] = rag_json.get('other')

            if 'address' in rag_json and rag_json['address']:
                rag_address = rag_json['address']
                normalized_rag_addr = normalize_rag_address(rag_address)

                best_match, score, matched_row = self.address_matcher.find_matching_address(normalized_rag_addr)

                if best_match:
                    result_dict['match_score'] = score
                    result_dict['matched_full_address_df'] = matched_row['full_address']
                    result_dict['matched_lv0'] = matched_row['lv0']
                    result_dict['matched_lv1'] = matched_row['lv1']
                    result_dict['matched_lv2'] = matched_row['lv2']
                    result_dict['matched_lv3'] = matched_row['lv3']
                    result_dict['matched_lv4'] = matched_row['lv4']

                    # Determine matched levels and construct the best_match_display string
                    best_match_display_components = []
                    lv0_added = False

                    for i, level_col in enumerate(['lv0', 'lv1', 'lv2', 'lv3', 'lv4']):
                        component = matched_row[level_col]
                        if pd.notna(component) and component:
                            normalized_component = strip_address_postfixes(component)
                            if normalized_component in normalized_rag_addr:
                                if level_col == 'lv0':
                                    best_match_display_components.append(component)
                                    lv0_added = True
                                elif level_col == 'lv1':
                                    if lv0_added and best_match_display_components and best_match_display_components[-1] == strip_address_postfixes(component):
                                        best_match_display_components[-1] = component
                                    else:
                                        best_match_display_components.append(component)
                                else:
                                    best_match_display_components.append(component)
                    
                    best_match_display = " ".join(best_match_display_components)
                    if not best_match_display:
                        best_match_display = best_match
                    result_dict['matched_address_display'] = best_match_display

                    location = self.geolocator.geocode(best_match_display)
                    if location:
                        result_dict['latitude'] = location.latitude
                        result_dict['longitude'] = location.longitude
                        result_dict['geocoded_address'] = location.address
        
        return result_dict