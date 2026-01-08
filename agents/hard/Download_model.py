# Run this once with internet:
from transformers import T5ForConditionalGeneration, T5Tokenizer

print("Downloading t5-base...")
model = T5ForConditionalGeneration.from_pretrained("t5-base")
tokenizer = T5Tokenizer.from_pretrained("t5-base")

# Save locally
model.save_pretrained("./models/t5-base")
tokenizer.save_pretrained("./models/t5-base")
print("✅ Downloaded to ./models/t5-base")
