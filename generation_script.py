import argparse

from generation_job_and_utils import CreateDeduplicatedDsJob

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create deduplicated dataset job")
    parser.add_argument(
        "--file-paths",
        nargs="+",
        required=True,
        help="List of file paths containing source raw data",
    )
    parser.add_argument(
        "--out-path",
        required=True,
        help="Path to save the generated dataset",
    )
    parser.add_argument(
        "--forbidden-statements-path",
        required=True,
        help="Path to file containing all statements used in the test file in the PISA benchmark",
    )
    parser.add_argument(
        "--generation-mode",
        default="premise_selection",
        choices=["premise_selection", "proof_generation"],
        help="Generation mode: premise selection generates datapoints from all steps that contain premises, "
             "while proof_generation generates datapoints from all steps. The latter is suitable "
             "for training a Language Model for proof step generation.",
    )
    parser.add_argument(
        "--deduplication-features",
        nargs="+",
        default=["state", "statement", "step"],
        choices=["state", "statement", "step"],
        help="Deduplication features",
    )
    args = parser.parse_args()

    job = CreateDeduplicatedDsJob(
        args.file_paths,
        args.out_path,
        args.forbidden_statements_path,
        args.generation_mode,
        args.deduplication_features,
    )
    job.execute()

