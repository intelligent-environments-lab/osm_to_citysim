import pyarrow.parquet as pq
import numpy as np
import pandas as pd
import pdb

df = pq.read_table('TX_baseline_metadata_and_annual_results.parquet')

df = df.to_pandas()

print(df.columns)
print(df)
# df.to_csv('TX_baseline_metadata_and_annual_results.csv', index=False)
pdb.set_trace()