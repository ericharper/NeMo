"""
This code were adapted from 
https://github.com/google-research/google-research/tree/master/schema_guided_dst
"""

import os

import numpy as np
import torch
from torch.utils.data import Dataset

from nemo import logging

__all__ = ['SGDDataset']


class SGDDataset(Dataset):
    """ 
    TODO: Update here
    """

    def __init__(
        self,
        task_name,
        dialogues_example_dir,
        overwrite_dial_file,
        dataset_split,
        schema_emb_processor,
        dialogues_processor,
    ):

        # Generate the dialogue examples if needed or specified.
        dial_file_name = f"{task_name}_{dataset_split}_examples.processed"
        dial_file = os.path.join(dialogues_example_dir, dial_file_name)

        schema_pkl_files = dialogues_processor.schema_pkl_files
        schema_pkl_exist = dataset_split in schema_pkl_files and os.path.exists(schema_pkl_files[dataset_split])

        if os.path.exists(dial_file) and not overwrite_dial_file and schema_pkl_exist:
            logging.info(f"Loading dialogue examples from {dial_file}.")
            with open(dial_file, "rb") as f:
                self.features = np.load(f, allow_pickle=True)
                f.close()
        else:
            logging.info("Start generating the dialogue examples.")
            self.features = dialogues_processor.get_dialog_examples(dataset_split)

            master_device = not torch.distributed.is_initialized() or torch.distributed.get_rank() == 0
            if master_device:
                if not os.path.exists(dialogues_example_dir):
                    os.makedirs(dialogues_example_dir)
                with open(dial_file, "wb") as f:
                    np.save(f, self.features)
                    f.close()
                logging.info(f"The dialogue examples saved at {dial_file}")
                logging.info("Finish generating the dialogue examples.")
        self.schema_data_dict = schema_emb_processor.get_schema_embeddings(dataset_split)

    def __get_ids_to_service_names_dict():
        return

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        ex = self.features[idx]
        service_id = ex.service_schema.service_id
        return (
            np.array(ex.example_id_num),
            np.array(service_id),
            np.array(ex.is_real_example, dtype=int),
            np.array(ex.utterance_ids),
            np.array(ex.utterance_segment),
            np.array(ex.utterance_mask, dtype=np.long),
            np.array(ex.num_categorical_slots),
            np.array(ex.categorical_slot_status),
            np.array(ex.num_categorical_slot_values),
            np.array(ex.categorical_slot_values),
            np.array(ex.num_noncategorical_slots),
            np.array(ex.noncategorical_slot_status),
            np.array(ex.noncategorical_slot_value_start),
            np.array(ex.noncategorical_slot_value_end),
            np.array(ex.start_char_idx),  # noncat_alignment_start
            np.array(ex.end_char_idx),  # noncat_alignment_end
            np.array(ex.num_slots),  # num_requested_slots
            np.array(ex.requested_slot_status, dtype=np.float32),
            np.array(ex.num_intents),
            np.array(ex.intent_status),
            np.array(self.schema_data_dict['cat_slot_emb'][service_id], dtype=np.float32),
            np.array(self.schema_data_dict['cat_slot_value_emb'][service_id], dtype=np.float32),
            np.array(self.schema_data_dict['noncat_slot_emb'][service_id], dtype=np.float32),
            np.array(self.schema_data_dict['req_slot_emb'][service_id], dtype=np.float32),
            np.array(self.schema_data_dict['intent_emb'][service_id], dtype=np.float32),
        )
