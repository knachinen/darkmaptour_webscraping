# Standard library imports
import json
import logging
# from datetime import datetime

# Third-party library imports
import pandas as pd
from tqdm import tqdm

# Local application imports
from text_utils import clean_text, save_json_data, load_json_data, get_timestamp
from address_processor import AddressProcessor

# --- Data Loading ---
df_addr = pd.read_parquet('data/address.parquet.gzip')
df_text = pd.read_parquet('data/sample.parquet.gzip')
# --- End Data Loading ---

# --- Main Execution ---
if __name__ == "__main__":
    # Configure logging
    timestamp = get_timestamp()
    log_filename = f"address_matching_{timestamp}.log"
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
    print(f"TOTAL SAMPLE: {len(df_text)}")
    start_index = 200
    # end_index = len(df_text) # Process up to (but not including) 
    end_index = 300
    
    # --- Setup ---
    SAVE_FREQUENCY = 10  # Save every 10 iterations
    TEMP_SAVE_FILE = f'temp_results_checkpoint__{timestamp}.json'
    TEMP_SAVE_DIRECTORY = "tmp/"
    TEMP_SAVE_PATH = f"{TEMP_SAVE_DIRECTORY}{TEMP_SAVE_FILE}"
    results_list = []
    # --- Setup ---

    # for i, (index_iter, text_content) in tqdm(zip(df_text.index[start_index:end_index], df_text.loc[start_index:end_index, 'content']), total=end_index-start_index, desc="Processing texts"):
    for i, (index_iter, text_content) in tqdm(
        enumerate(
            zip(df_text.index[start_index:end_index], 
                df_text.loc[start_index:end_index, 'content'])), 
        total=end_index-start_index, 
        desc="Processing texts"
):
        
        try:
            if text_content is None:
                continue
            text = clean_text(text_content)
            # print(f"\nProcessing index: {index_iter}")

            # Process text using AddressProcessor
            result_dict = address_processor.process_text(text_content=text)
            result_dict['index'] = index_iter # Add index to the result_dict

            results_list.append(result_dict)
            
        except Exception as e:
            print(f"\nError at index {index_iter}: {e}. Saving accumulated results.")
            # Save the list before the error happens
            save_json_data(results_list, TEMP_SAVE_PATH)
            continue
        
        # Check for the checkpoint
        if (i + 1) % SAVE_FREQUENCY == 0:
            print(f"\n--- Checkpoint: Saving {len(results_list)} results ---")
            save_json_data(results_list, TEMP_SAVE_PATH)

    # --- End of loop ---
    
    save_json_data(results_list, TEMP_SAVE_PATH)

    # Convert results to DataFrame and save
    results_df = pd.DataFrame(results_list)
    output_filename = f"data/matched_addresses_{timestamp}_idx_{start_index}_to_{end_index}.parquet.gzip"
    results_df.to_parquet(output_filename, compression='gzip')
    print(f"\nResults saved to {output_filename}")
