"""
Fine-tune CodeT5 on CodeSearchNet for code comment generation.
Run this once — saves the model locally for use in your app.
"""
import json
from pathlib import Path
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    T5ForConditionalGeneration,
    AdamW,
    get_linear_schedule_with_warmup,
)

import torch

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME    = "Salesforce/codet5-base"  # pre-trained CodeT5 base model
DATA_PATH     = "data/evaluation/csn_train.jsonl"            # your existing dataset
OUTPUT_DIR    = "models/codet5-finetuned"
MAX_INPUT     = 512
MAX_TARGET    = 128
BATCH_SIZE    = 4     # safe for CPU — increase to 8 if you have 16GB+ RAM
EPOCHS        = 3     # 3 epochs is enough for a meaningful improvement
LR            = 5e-5
# ─────────────────────────────────────────────────────────────────────────────


class CodeCommentDataset(Dataset):
    def __init__(self, filepath, tokenizer, max_input, max_target):
        self.samples = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                if item.get("code") and item.get("doc"):
                    self.samples.append(item)

        self.tokenizer  = tokenizer
        self.max_input  = max_input
        self.max_target = max_target

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        language = sample.get("language", "python")
        prompt  = f"Generate a concise docstring for this {language} code: {sample['code']}"
        target  = sample["doc"]

        inputs = self.tokenizer(
            prompt,
            max_length=self.max_input,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        targets = self.tokenizer(
            target,
            max_length=self.max_target,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        labels = targets["input_ids"].squeeze()
        # Replace padding token id with -100 so loss ignores it
        labels[labels == self.tokenizer.pad_token_id] = -100

        return {
            "input_ids":      inputs["input_ids"].squeeze(),
            "attention_mask": inputs["attention_mask"].squeeze(),
            "labels":         labels,
        }


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model     = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.to(device)

    dataset    = CodeCommentDataset(DATA_PATH, tokenizer, MAX_INPUT, MAX_TARGET)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    optimizer = AdamW(model.parameters(), lr=LR)
    total_steps = len(dataloader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=total_steps // 10,
        num_training_steps=total_steps
    )

    print(f"Dataset size: {len(dataset)} samples")
    print(f"Steps per epoch: {len(dataloader)}")
    print(f"Total steps: {total_steps}\n")

    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for step, batch in enumerate(dataloader):
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels         = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )
            loss = outputs.loss
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            total_loss += loss.item()

            if (step + 1) % 10 == 0:
                avg = total_loss / (step + 1)
                print(f"Epoch {epoch+1} | Step {step+1}/{len(dataloader)} | Loss: {avg:.4f}")

        epoch_loss = total_loss / len(dataloader)
        print(f"\n✅ Epoch {epoch+1} complete — Avg Loss: {epoch_loss:.4f}\n")

    # Save fine-tuned model
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    train()