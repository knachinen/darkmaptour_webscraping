# Standard library imports
import logging
from datetime import datetime

# Third-party library imports
import pandas as pd
from tqdm import tqdm
# from geopy.geocoders import Nominatim # No longer needed here

# Local application imports
from address_processor.utils.custom_utils import load_var, save_var
from address_processor.utils.text_utils import clean_text
# from address_processor.address_utils import ( # No longer needed here
#     normalize_address_df,
#     normalize_rag_address,
#     strip_address_postfixes
# )
# from address_processor.llm_extractor import LLMExtractor # No longer needed here
# from address_processor.address_matcher import AddressMatcher # No longer needed here
from address_processor.address_processor import AddressProcessor # Import AddressProcessor

# --- Data Loading ---
df_addr = pd.read_parquet('address_processor/address/df_addr.parquet.gzip')
df_text = pd.read_parquet('address_processor/dataframe/flasher_hk_20130101_20220307_loc.parquet.gzip')
# --- End Data Loading ---

# --- Main Execution ---
if __name__ == "__main__":
    # Configure logging
    log_filename = datetime.now().strftime("address_matching_%Y%m%d_%H%M%S.log")
    log_directory = f"address_processor/log/"
    log_path = f"{log_directory}{log_filename}"
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_path,
        filemode='w'
    )
    logger = logging.getLogger(__name__)
    logging.debug("Logging configured and working!")

    # Initialize Address Processor
    address_processor = AddressProcessor(df_addr=df_addr, llm_model='gemma3:1b')

    results_list = [] # Initialize list to store results

    # Process a range of indices for testing
    start_index = 11
    end_index = 20 # Process up to (but not including) 10

    for index_iter, text_content in tqdm(zip(df_text.index[start_index:end_index], df_text.loc[start_index:end_index, 'content']), total=end_index-start_index, desc="Processing texts"):
        text = clean_text(text_content)
        # print(f"\nProcessing index: {index_iter}")

        # Process text using AddressProcessor
        result_dict = address_processor.process_text(text_content=text)
        result_dict['index'] = index_iter # Add index to the result_dict

        results_list.append(result_dict)

    # --- End of loop ---

    # Convert results to DataFrame and save
    results_df = pd.DataFrame(results_list)
    results_df.to_parquet('address_processor/address/matched_addresses.parquet.gzip', compression='gzip')
    print(f"\nResults saved to address/matched_addresses.parquet.gzip")
