import sys

sys.path.append('../')

import time

import numpy as np
import pandas as pd
from cfbench.cfbench import BenchmarkCF, TOTAL_FACTUAL

import test_lore
from benchmark.utils import timeout, TimeoutError

# Get initial and final index if provided
if len(sys.argv) == 3:
    initial_idx = sys.argv[1]
    final_idx = sys.argv[2]
else:
    initial_idx = 0
    final_idx = TOTAL_FACTUAL

# Create Benchmark Generator
benchmark_generator = BenchmarkCF(
    output_number=1,
    show_progress=True,
    disable_tf2=True,
    disable_gpu=True,
    initial_idx=int(initial_idx),
    final_idx=int(final_idx),
    get_tf_session=False).create_generator()

# The Benchmark loop
for benchmark_data in benchmark_generator:
    # Get factual array
    factual_array = benchmark_data['factual_oh']
    factual_not_oh = benchmark_data['factual']

    # Get train data
    train_data = benchmark_data['df_oh_train']
    train_data_not_oh = benchmark_data['df_train']

    # Get columns info
    columns = list(train_data.columns)[:-1]

    # Get factual row as pd.Series
    factual_row = pd.Series(benchmark_data['factual_oh'], index=columns)

    # Get factual class
    fc = benchmark_data['factual_class']

    # Get Keras TensorFlow model
    model = benchmark_data['model']

    # Get Evaluator
    evaluator = benchmark_data['cf_evaluator']

    # Categorical features
    cat_feats = benchmark_data['cat_feats']


    @timeout(600)
    def generate_cf():
        try:
            # Create CF using LORE's explainer and measure generation time
            start_generation_time = time.time()
            cf_generation_output = test_lore.main(
                train_data_not_oh, cat_feats, 'output', list(train_data.columns), model,
                pd.DataFrame([[*factual_not_oh, 0]], columns=list(train_data_not_oh.columns)))
            cf_generation_time = time.time() - start_generation_time

            if len(cf_generation_output) > 0:
                cf = cf_generation_output.to_numpy()[0].tolist()
            else:
                cf = factual_array

            if factual_array != cf:
                print('CF generated')

        except Exception as e:
            print('Error generating CF')
            print(e)
            # In case the CF generation fails, return same as factual
            cf = factual_row.to_list()
            cf_generation_time = np.NaN

        # Evaluate CF
        evaluator(
            cf_out=cf,
            algorithm_name='lore',
            cf_generation_time=cf_generation_time,
            save_results=True)

    try:
        generate_cf()
    except TimeoutError:
        print('Timeout generating CF')
        # If CF generation time exceeded the limit
        evaluator(
            cf_out=factual_row.to_list(),
            algorithm_name='lore',
            cf_generation_time=np.NaN,
            save_results=True)
