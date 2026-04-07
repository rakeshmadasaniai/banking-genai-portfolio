"""
Banking Q&A Dataset Generator
Project 2: Banking Domain Dataset for QLoRA Fine-tuning
Author: Rakesh Madasani
Description: Generates instruction-response pairs from banking documents
             using LangChain + OpenAI for QLoRA fine-tuning
"""

import os
import json
import time
import random
from pathlib import Path
from typing import List, Dict

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME     = "gpt-3.5-turbo"
CHUNK_SIZE     = 1000
CHUNK_OVERLAP  = 150
PAIRS_PER_CHUNK = 5        # how many Q&A pairs to generate per chunk
OUTPUT_DIR     = Path("data")
OUTPUT_DIR.mkdir(exist_ok=True)

QUESTION_TYPES = [
    "factual",       # direct fact from the text
    "conceptual",    # explain or compare concepts
    "calculation",   # numerical / formula based
    "application",   # real-world banking scenario
    "scenario",      # AML / NPA / risk case study
]

GENERATION_PROMPT = PromptTemplate(
    input_variables=["context", "question_type", "num_pairs"],
    template="""
You are a banking and finance expert creating a training dataset for fine-tuning an LLM.

Given the following banking/finance context, generate exactly {num_pairs} high-quality
question-answer pairs of type: {question_type}

Rules:
- Questions must be answerable ONLY from the given context
- Answers must be detailed, accurate, and educational
- For calculation type: include numbers and formulas
- For scenario type: describe a realistic banking situation
- For factual type: ask about specific rates, ratios, definitions
- Do NOT repeat questions
- Return ONLY valid JSON, no extra text

Context:
{context}

Return this exact JSON format:
[
  {{
    "instruction": "question here",
    "input": "",
    "output": "detailed answer here"
  }}
]
"""
)

def load_documents(file_path: str) -> List:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(file_path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


def chunk_documents(docs: List) -> List:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )
    return splitter.split_documents(docs)


def generate_qa_pairs(
    chunks: List,
    llm: ChatOpenAI,
    target_pairs: int = 5000
) -> List[Dict]:

    chain = LLMChain(llm=llm, prompt=GENERATION_PROMPT)
    all_pairs = []
    seen_questions = set()
    chunk_idx = 0

    print(f"\n Generating Q&A pairs from {len(chunks)} chunks...")
    print(f" Target: {target_pairs} pairs\n")

    while len(all_pairs) < target_pairs and chunk_idx < len(chunks):
        chunk = chunks[chunk_idx]
        context = chunk.page_content.strip()

        if len(context) < 100:
            chunk_idx += 1
            continue

        q_type = QUESTION_TYPES[chunk_idx % len(QUESTION_TYPES)]

        try:
            result = chain.run(
                context=context,
                question_type=q_type,
                num_pairs=PAIRS_PER_CHUNK
            )

            # Clean and parse JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            result = result.strip()

            pairs = json.loads(result)

            for pair in pairs:
                q = pair.get("instruction", "").strip()
                if q and q not in seen_questions:
                    seen_questions.add(q)
                    all_pairs.append({
                        "instruction": q,
                        "input": pair.get("input", ""),
                        "output": pair.get("output", "").strip(),
                        "metadata": {
                            "source": chunk.metadata.get("source", "unknown"),
                            "type": q_type,
                            "chunk_id": chunk_idx
                        }
                    })

            print(f"  Chunk {chunk_idx+1}/{len(chunks)} | Type: {q_type:12s} | Total pairs: {len(all_pairs)}")

        except json.JSONDecodeError as e:
            print(f"  [WARN] JSON parse error at chunk {chunk_idx}: {e}")
        except Exception as e:
            print(f"  [ERROR] chunk {chunk_idx}: {e}")
            time.sleep(2)

        chunk_idx += 1
        time.sleep(0.5)   # rate limit buffer

    print(f"\n Done! Generated {len(all_pairs)} unique Q&A pairs.")
    return all_pairs

def save_dataset(pairs: List[Dict], name: str = "banking"):
    # 1. Alpaca format (for QLoRA training)
    alpaca = [{"instruction": p["instruction"],
               "input": p["input"],
               "output": p["output"]} for p in pairs]

    alpaca_path = OUTPUT_DIR / f"{name}_alpaca.json"
    with open(alpaca_path, "w", encoding="utf-8") as f:
        json.dump(alpaca, f, indent=2, ensure_ascii=False)

    # 2. JSONL format (for OpenAI fine-tuning)
    jsonl_path = OUTPUT_DIR / f"{name}_openai.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for p in pairs:
            msg = {
                "messages": [
                    {"role": "system", "content": "You are a banking and finance expert assistant."},
                    {"role": "user",   "content": p["instruction"]},
                    {"role": "assistant", "content": p["output"]}
                ]
            }
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    # 3. Full metadata JSON (for analysis)
    meta_path = OUTPUT_DIR / f"{name}_full.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(pairs, f, indent=2, ensure_ascii=False)

    # 4. Train/Val split (90/10)
    random.shuffle(pairs)
    split = int(len(pairs) * 0.9)
    train, val = pairs[:split], pairs[split:]

    train_alpaca = [{"instruction": p["instruction"], "input": p["input"], "output": p["output"]} for p in train]
    val_alpaca   = [{"instruction": p["instruction"], "input": p["input"], "output": p["output"]} for p in val]

    with open(OUTPUT_DIR / f"{name}_train.json", "w", encoding= "utf-8") as f:
        json.dump(train_alpaca, f, indent=2, ensure_ascii=False)
    with open(OUTPUT_DIR / f"{name}_val.json", "w", encoding="utf-8") as f:
        json.dump(val_alpaca, f, indent=2, ensure_ascii=False)

    print(f"\n Files saved to '{OUTPUT_DIR}/':")
    print(f"   {alpaca_path.name}   ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â QLoRA training (Alpaca format)")
    print(f"   {jsonl_path.name}  ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â OpenAI fine-tuning (JSONL format)")
    print(f"   {meta_path.name}     ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Full dataset with metadata")
    print(f"   {name}_train.json     ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Train split ({len(train)} pairs)")
    print(f"   {name}_val.json       ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Val split ({len(val)} pairs)")

    return {
        "total": len(pairs),
        "train": len(train),
        "val":   len(val),
        "alpaca_path": str(alpaca_path),
        "jsonl_path":  str(jsonl_path),
    }

def print_stats(pairs: List[Dict]):
    type_counts = {}
    for p in pairs:
        t = p.get("metadata", {}).get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    avg_q_len = sum(len(p["instruction"]) for p in pairs) / len(pairs)
    avg_a_len = sum(len(p["output"])      for p in pairs) / len(pairs)

    print("\n Dataset Statistics:")
    print(f"  Total pairs     : {len(pairs)}")
    print(f"  Avg question len: {avg_q_len:.0f} chars")
    print(f"  Avg answer len  : {avg_a_len:.0f} chars")
    print(f"\n  By question type:")
    for t, c in sorted(type_counts.items()):
        bar = "ÃƒÂ¢Ã¢â‚¬â€œÃ‹â€ " * (c // 2)
        print(f"    {t:12s}: {c:4d}  {bar}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Banking Q&A Dataset Generator")
    parser.add_argument("--files",   nargs="+", required=True, help="Input PDF or TXT files")
    parser.add_argument("--target",  type=int,  default=500,   help="Target number of pairs")
    parser.add_argument("--name",    type=str,  default="banking", help="Output file prefix")
    args = parser.parse_args()

    if not OPENAI_API_KEY:
        raise ValueError("Set OPENAI_API_KEY in your .env file")

    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENAI_API_KEY,
        temperature=0.3,
    )

    all_docs = []
    for f in args.files:
        print(f" Loading: {f}")
        docs = load_documents(f)
        all_docs.extend(docs)
        print(f"   Loaded {len(docs)} pages/sections")

    chunks = chunk_documents(all_docs)
    print(f"\n Total chunks: {len(chunks)}")

    pairs = generate_qa_pairs(chunks, llm, target_pairs=args.target)
    print_stats(pairs)
    save_dataset(pairs, name=args.name)


if __name__ == "__main__":
    main()
