from datasets import load_dataset
import pandas as pd
from typing import Optional

def load_code_to_text_dataset(
    split: str = "train",
    limit: Optional[int] = None,
    as_dataframe: bool = True
):
    """
    Loads the CodeXGlue Code-to-Text dataset for Java from Hugging Face.

    Args:
        split (str): Dataset split to load ('train', 'validation', 'test').
        limit (Optional[int]): If set, only loads the first `limit` examples.
        as_dataframe (bool): If True, returns a pandas DataFrame. Otherwise, returns Hugging Face dataset.

    Returns:
        pd.DataFrame or datasets.Dataset: Loaded dataset.
    """
    dataset = load_dataset("google/code_x_glue_ct_code_to_text", "java", cache_dir="../../data/raw/")
    
    if split not in dataset:
        raise ValueError(f"Split '{split}' not found. Available splits: {list(dataset.keys())}")

    data_split = dataset[split]

    if limit:
        data_split = data_split.select(range(limit))

    if as_dataframe:
        return pd.DataFrame(data_split)
    else:
        return data_split