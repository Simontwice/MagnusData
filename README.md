# Introduction

This repository contains the code and data used to generate a premise selection dataset, which is described in [Magnushammer: A Transformer-based Approach to Premise Selection](https://arxiv.org/abs/2303.04488). The premise selection model trained on this dataset achieved a state-of-the-art 71% proof rate on the [PISA](http://aitp-conference.org/2021/abstract/paper_17.pdf) benchmark and 37.3% on [miniF2F](https://arxiv.org/abs/2109.00110).

You can download the dataset used in the paper from our [Huggingface datasets](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle) page. The code in this repository and the data stored [here](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle/tree/main) can be used to generate new datasets for premise selection, proof generation, and text retrieval tasks.

# Raw data overview

The raw data used to generate the datasets is a collection of proof trajectories - sequences that contain information about the commands called to Isabelle (the proof assistant) and the corresponding proof states.

Each proof trajectory corresponds to a unique proof of a problem, written by a human expert or generated automatically with Sledgehammer. The proofs generated by Sledgehammer are alternatives to the original human proofs, so some trajectories in the raw data come from the same original problems.

## Data Structure

The raw data is structured as JSON files, and each file corresponds to a particular proof generation mode. Each JSON file contains trajectories, where a given trajectory represents the steps taken in a single proof. The example given below clarifies how a proof is transformed into a trajectory.

For the following proof:
```
theorem identity1: fixes f :: "nat \<Rightarrow> nat"
assumes fff: "\<And>n. f(f(n)) < f(Suc(n))"
shows "f(n) = n"
proof -
  { fix m n have key: "n \<le> m \<Longrightarrow> n \<le> f(m)"
    proof(induct n arbitrary: m)
      case 0 show ?case by simp
    [...]
    qed }
  hence "\<And>n. n \<le> f(n)" by simp
  hence "\<And>n. f(n) < f(Suc n)" by(metis fff order_le_less_trans)
  hence "f(n) < n+1" by (metis fff lift_Suc_mono_less_iff[of f] Suc_eq_plus1)
  with \<open>n \<le> f(n)\<close> show "f n = n" by arith
qed
```
We get the following trajectory

```
{
  'statement': 'theorem identity1: fixes f :: "nat \\<Rightarrow> nat"
assumes fff: "\\<And>n. f(f(n)) < f(Suc(n))"
shows "f(n) = n"'
  'transitions': <list_of_transitions>
}
```
where each transition in `<list_of_transitions>` corresponds to a single proof step (we do not include the full list for brevity).

A transition that corresponds to the step `by (metis fff lift_Suc_mono_less_iff[of f] Suc_eq_plus1)` called above is
```
  'state': 'proof (prove)\n using this:\n   f ?n < f (Suc ?n) \n goal (1 subgoal):\n  1. f n < n + 1'
  'step': 'by (metis fff lift_Suc_mono_less_iff[of f] Suc_eq_plus1)'
  'premises': {'fff': ['local.fff', ' fff: fixes n :: "nat" shows "f (f n) < f (Suc n)"'], 
  'lift_Suc_mono_less_iff': ['Nat.order.lift_Suc_mono_less_iff', ' lift_Suc_mono_less_iff: fixes less_eq :: "\'a \\<Rightarrow> \'a \\<Rightarrow> bool"   and less :: "\'a \\<Rightarrow> \'a \\<Rightarrow> bool"   and f :: "nat \\<Rightarrow> \'a"   and n :: "nat"   and m :: "nat" assumes "class.order less_eq less"   and "\\<And>n. less (f n) (f (Suc n))" shows "less (f n) (f m) = (n < m)"'],
  'Suc_eq_plus1': ['Nat.Suc_eq_plus1', ' Suc_eq_plus1: fixes n :: "nat" shows "Suc n = n + 1"']}
```
Hence the structure of a trajectory is:
```
Trajectory:
{
  'statement': str,
  'transitions': List[Transition]
}
```
where
```
Transition: 
{
  'state': str,
  'step': str,
  'premises': Dict[str,Tuple[str,str]]
}
```
In 'premises', the keys are names of the premises referenced in the proof step, whereas the values are lists, where the first element is the name of the premise in the lemma library, and the second element is the statement of the premise.

## Dataset generation

In order to generate your own dataset from the raw data, download the selected raw files included [here](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle/tree/main). We include a discussion of the source and extraction methods for all the raw data files below.

Next, run `setup.sh` to set up a virtual environment and install dependencies.
```
chmod +x setup.sh
./setup.sh
```
Finally, run the following script to generate the data in a `JSON` format compliant with Huggingface's [Datasets](https://huggingface.co/docs/datasets/index):
```
python generation_script.py --file-paths <paths> --out-path <out_path> --forbidden-statements-path PISA_test_theorems.json
```

### Overview of raw data files
All raw data files for this project are available for download [here](https://huggingface.co/datasets/Simontwice/premise_selection_in_isabelle/tree/main).

The data is categorized into two types: `human data` and `machine_generated_data`.

`Human data` consists of proofs that were created directly by humans. On the other hand, `machine-generated data` is composed of alternative proofs generated using [Sledgehammer](https://isabelle.in.tum.de/website-Isabelle2009-1/sledgehammer.html).

The machine-generated data is further divided into two subcategories, `gen1` and `gen2`, which differ in the Sledgehammer configurations used for mining. `Gen1` proofs use a less diverse set of tactics, but sometimes have a higher chance of producing a successful proof.

The two modes of proof generation used for machine-generated data are referred to as `mode_1` and `mode_2`. Proofs in `mode_1` were generated by replacing the last step of a successful human proof with a Sledgehammer step, while `mode_2` attempted to replace the entire proof with a single Sledgehammer step. Note that since human proofs are usually nested, both approaches considered all sub-proofs separately as well.

The last distinction, `minimal` and `non-minimal`, refers again to Sledgehammer configuration. `Minimal` proofs were found by first finding a `non-minimal` version, then trying to remove unnecessary premises. Thus, `non-minimal` proofs contain more premises, but some of them might be redundant. For batch-contrastive learning, there is a case to be made for both approaches.

### Languages

All data included in this dataset is written in English and uses the Isabelle syntax, which represents mathematical expressions using syntax similar to LaTeX.

### Source Data
The dataset was created using the proofs included in the [Archive of Formal Proofs](https://www.isa-afp.org/) and the Standard library included in the [Isabelle](https://isabelle.in.tum.de/) 2021-1 distribution.

### Known Limitations

The data included in this dataset is mostly untyped, meaning that there is little information about the objects referenced in the statement or premise statements. Adding type information would be a valuable contribution.

### Citation
If you use this dataset in your research, please cite the associated arXiv paper: [Magnushammer: A Transformer-based Approach to Premise Selection](https://arxiv.org/abs/2303.04488)

### Acknowledgements
We would like to express our gratitude to the following individuals and organizations for their contributions to this project:

* We would like to acknowledge [@jinpz](https://github.com/jinpz) for their contributions to the data mining aspect of this project. Their expertise and hard work greatly assisted us in achieving our project goals.

* PISA API: We also want to thank the developers of the [PISA](https://github.com/albertqjiang/Portal-to-ISAbelle) API for creating a powerful tool that allowed us to interact with Isabelle through Python.

* Google TRC Compute: Finally, we want to acknowledge Google's [TPU Reasearch Cloud](https://sites.research.google/trc/about/) for providing compute necessary to develop the code infrastructure needed for the mining procedure.

We are grateful for the support and contributions of each of these individuals and organizations, and we would not have been able to accomplish this project without them.
