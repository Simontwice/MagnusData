import json
import random
import re
from typing import List, Dict

import datasets
import pandas as pd
from absl import logging


class CreateDeduplicatedDsJob:
    def __init__(
        self,
        file_paths,
        out_path,
        forbidden_statements_path,
        generation_mode,
        deduplication_features,
    ):
        """

        Args:
            file_paths: iterable of file paths containing source raw data
            out_path: path to save
            forbidden_statements_path: path to file containing all statements used in the test file in the PISA benchmark
        """
        self.out_path = out_path
        self.file_paths = file_paths
        self.forbidden_statements_path = forbidden_statements_path
        self.seen_forbidden_theorems = {}
        self.generation_mode = generation_mode
        self.deduplication_features = deduplication_features
        with open(self.forbidden_statements_path, "r") as f:
            values = json.load(f).values()
            self.forbidden_statements = trim_all([thm["lemma"] for thm in values])

    def execute(self):
        """
        generates datapoints from trajectories
        Returns:

        """
        self.create_examples_from_proof = (
            create_examples_from_proof_for_premise_selection
            if self.generation_mode == "premise_selection"
            else create_examples_from_proof_for_proof_step_generation
        )
        (
            all_datapoints,
            num_of_failed_to_load,
            failed_files,
        ) = self.dataset_from_multiple_filenames(self.file_paths)

        logging.info(
            f"During processing, {num_of_failed_to_load} failed to load. The jsons are most likely corrupted."
        )
        dedup_datapoints = deduplicate_data(all_datapoints, features=self.deduplication_features)
        random.seed(0)
        random.shuffle(dedup_datapoints)
        with open(self.out_path, "w") as f:
            json.dump(dedup_datapoints, f, indent=2)
            dataset = datasets.Dataset.from_pandas(pd.DataFrame(data=dedup_datapoints))
            dataset.to_json("/home/szymon/Downloads/HF_PSM_data/full_dataset.json")

    def dataset_from_filename(self, fname):
        with open(fname) as ds_json:
            logging.info(fname)
            try:
                ds_fragment = json.load(ds_json)
            except json.decoder.JSONDecodeError:
                logging.info(f"Failed to load {fname}")
                return [], True
            datapoints_from_file = self.create_examples_from_file_ds(ds_fragment)
        return datapoints_from_file, False

    def dataset_from_multiple_filenames(self, fnames):
        all_datapoints = []

        json_failed_files = []
        jsons_failed_to_load = 0

        for idx, fname in enumerate(fnames):
            datapoints_from_single_file, failed = self.dataset_from_filename(fname)
            all_datapoints += datapoints_from_single_file
            if failed:
                jsons_failed_to_load += 1
                json_failed_files.append(fname)

        return all_datapoints, jsons_failed_to_load, json_failed_files

    def create_examples_from_file_ds(self, ds_fragment: Dict) -> list:
        proofs_unraveled = []

        for name_of_file, proofs in ds_fragment.items():
            for trajectory in proofs:
                if not trim(trajectory["statement"]) in self.forbidden_statements:
                    proofs_unraveled += self.create_examples_from_proof(trajectory)
                else:
                    logging.info(
                        f"A proof from universal_test_theorems was filtered! name:{trajectory['statement'].split(':')[0]}"
                    )
        return proofs_unraveled


def create_examples_from_proof_for_premise_selection(proof_trajectory: dict):
    res = []
    for transition in proof_trajectory["transitions"]:
        premises = discard_library_premise_name(transition["premises"])
        for name, stmt in premises.items():
            res.append(
                {
                    "statement": proof_trajectory["statement"],
                    "state": transition["state"],
                    "step": transition["step"],
                    "premise_name": name,
                    "premise_statement": stmt,
                }
            )
    return res


def create_examples_from_proof_for_proof_step_generation(proof_trajectory: dict):
    res = []
    for transition in proof_trajectory["transitions"]:
        res.append(
            {
                "statement": proof_trajectory["statement"],
                "state": transition["state"],
                "step": transition["step"],
            }
        )
    return res


def discard_library_premise_name(premise_dict):
    """
    Args:
        premise_dict: dict of the form {name_of_premise_in_step: [name_of_premise_in_library,statement]

    Returns:

    """
    return {key: value[1] for key, value in premise_dict.items()}


def deduplicate_data(all_data, features=("state", "statement", "premise_statement")):
    """
    Deduplicates identical datapoints, according to the list of features supplied
    Args:
        all_data: list of datapoints
        features: iterable of features to take into account when checking for datapoint uniqueness
    Returns:

    """
    deduplicated_data = []
    seen_datapoints = set()
    for datapoint in all_data:
        signature = (trim(datapoint[feature]) for feature in features)
        if signature in seen_datapoints:
            continue
        else:
            seen_datapoints.add(signature)
            deduplicated_data.append(datapoint)
    return deduplicated_data


def trim(string):
    nonewline = re.sub("\n", " ", string)
    return re.sub(" +", " ", nonewline).strip()


def trim_all(strings: List[str]):
    return [trim(s) for s in strings]