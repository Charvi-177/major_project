import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

print("Loading model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float32
)

print("Model loaded successfully!")

# Load dashboard
with open("dashboard_config_enriched.json", "r", encoding="utf-8") as f:
    dashboard = json.load(f)

# Keep the prompt reasonably small
dashboard_text = json.dumps(
    dashboard,
    indent=2,
    ensure_ascii=False
)

prompt = f"""
You are a dashboard analysis assistant.

Analyze this dashboard configuration and generate a concise report.

Include:
1. Dashboard purpose
2. Important KPIs
3. Charts
4. Tables
5. Key observations

Only use information present in the dashboard.
Do not invent values.

Dashboard:
{dashboard_text}
"""

messages = [
    {
        "role": "user",
        "content": prompt
    }
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

inputs = tokenizer(
    text,
    return_tensors="pt",
    truncation=True,
    max_length=4096
)

print("Generating report...")

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=300,
        do_sample=False
    )

new_tokens = outputs[0][inputs["input_ids"].shape[1]:]

response = tokenizer.decode(
    new_tokens,
    skip_special_tokens=True
)

print("\n========== GENERATED REPORT ==========\n")
print(response)
print("\n======================================")