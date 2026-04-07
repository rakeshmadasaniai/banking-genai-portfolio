# Banking & Finance QA Dataset

 This project contains the banking and finance instruction dataset used for downstream fine-tuning.

## Dataset
[banking-finance-qa-dataset](https://huggingface.co/datasets/RakeshMadasani/banking-finance-qa-dataset)

## Screenshot
Published dataset page with train and validation splits:

![Dataset on Hugging Face](screenshots/dataset-hf-splits.png)

## Summary
- 3,002 instruction-response pairs
- 2,701 train samples
- 301 validation samples
- Alpaca-style format
- English language
- Banking and finance domain

## Coverage
- AML / KYC
- CDD / EDD
- FDIC
- Basel III
- RBI
- SAR / CTR
- compliance topics
- finance fundamentals

## What it demonstrates
- domain data curation
- instruction dataset creation
- validation and split design
- Hugging Face dataset publishing

## Data Methodology

The dataset was built by turning curated banking and compliance material into instruction-style examples intended for downstream fine-tuning. The focus was not just on volume, but on having a usable spread of topics, clean formatting, and a validation pass before publishing.

In practice, that meant:

- selecting questions that map naturally to banking, compliance, and regulatory supervision
- structuring examples in Alpaca-style `instruction`, `input`, and `output` fields
- validating the finished dataset for structural consistency and duplicate issues before upload

## Example Schema

```json
{
  "instruction": "What is the FDIC deposit insurance limit in the United States?",
  "input": "",
  "output": "The FDIC insures deposits up to $250,000 per depositor, per insured bank, per account ownership category."
}
```

## Code Entry Points
- `generate_dataset.py` - builds banking instruction-response pairs from curated source material
- `validate_dataset.py` - runs duplicate and structural checks on the generated dataset
- `upload_to_hf.py` - publishes the dataset and dataset card to Hugging Face

## Why it stands out
This project turns raw banking and compliance material into a reusable ML asset rather than stopping at prompt experimentation. It shows the data layer behind the model and application work in the rest of the portfolio.

## Limitations

- instruction-style datasets can still inherit phrasing bias from the source material used to create them
- U.S. and India banking topics are useful together, but not always perfectly balanced in representation
- the dataset is a strong domain adaptation asset, but it should not be treated as formal regulatory ground truth
