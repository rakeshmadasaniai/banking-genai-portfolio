import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
ADAPTER_MODEL = "RakeshMadasani/banking-finance-mistral-qlora"
SYSTEM_PROMPT = (
    "You are a banking and finance expert assistant with deep knowledge of "
    "Indian banking regulations (RBI, PMLA, KYC, Basel norms) and U.S. banking regulations "
    "(BSA, FinCEN, FDIC, OCC, CFPB, Dodd-Frank). Provide accurate, detailed, and professional answers."
)


def load_model():
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
    )

    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_MODEL)
    tokenizer.pad_token = tokenizer.eos_token

    model = PeftModel.from_pretrained(base_model, ADAPTER_MODEL)
    model.eval()
    return model, tokenizer


def generate_answer(model, tokenizer, question, max_new_tokens=180):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


if __name__ == "__main__":
    model, tokenizer = load_model()
    prompts = [
        "What is the FDIC deposit insurance limit in the United States?",
        "What are the three stages of money laundering?",
        "What is the difference between AML and KYC?",
    ]
    for prompt in prompts:
        print(f"\nQ: {prompt}")
        print(f"A: {generate_answer(model, tokenizer, prompt)}")
