# Standard library imports
import logging
from datetime import datetime

# Third-party library imports
import pandas as pd
from tqdm import tqdm

# Local application imports
from text_utils import clean_text
from address_processor import AddressProcessor

# --- Data Loading ---
df_addr = pd.read_parquet('data/address.parquet.gzip')
df_text = pd.read_parquet('data/sample.parquet.gzip')
# --- End Data Loading ---

# --- Main Execution ---
if __name__ == "__main__":
    # Configure logging
    log_filename = datetime.now().strftime("address_matching_%Y%m%d_%H%M%S.log")
    log_directory = f"log/"
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
    start_index = 0
    # end_index = len(df_text) # Process up to (but not including) 
    end_index = 100

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
    results_df.to_parquet('data/matched_addresses.parquet.gzip', compression='gzip')
    print(f"\nResults saved to data/matched_addresses.parquet.gzip")
