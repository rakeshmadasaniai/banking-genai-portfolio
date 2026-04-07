# Banking Finance QLoRA Fine-Tuned Model

This project contains the fine-tuning workflow for adapting a Mistral-based LLM to banking and finance question answering.

## Model
[banking-finance-mistral-qlora](https://huggingface.co/RakeshMadasani/banking-finance-mistral-qlora)

## Base Model
`mistralai/Mistral-7B-Instruct-v0.3`

## Fine-Tuning Summary
- Method: QLoRA
- Quantization: 4-bit NF4
- LoRA rank: 16
- LoRA alpha: 32
- LoRA dropout: 0.05
- Training samples: 2,701
- Validation samples: 301
- Global steps: 676
- Final train loss: 1.13

## What it demonstrates
- parameter-efficient fine-tuning
- PEFT/LoRA configuration
- domain adaptation using custom data
- Hugging Face model publishing
