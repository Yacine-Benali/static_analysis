import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


class AccountDeletionAnalyser:
    def __init__(self, model_name="microsoft/phi-2"):
        """Initialise the analyser with a pre-trained language model."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)

    def analyse_code_snippet(self, smali_code, strings_xml, max_length=1024):
        """Analyze code snippet for likelihood of account deletion functionality."""
        # Construct a comprehensive prompt for analysis
        prompt = f"""Analyze the following code snippets for account deletion functionality:

Smali Code:
{smali_code}

Strings XML:
{strings_xml}

Task: Determine the likelihood (0-100%) that this code relates to user account
deletion. 
Respond in the following format where you replace the <likelihood> with your
determined likelihood and <reason> with a detailed explanation of your reasoning: 

"Likelihood of Account Deletion Functionality: <insert likelihood here>.
The reason for this is: <reason>"
"""

        # Tokenize the prompt
        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=max_length
        ).to(self.device)

        # Generate response
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=max_length + 100,
            num_return_sequences=1,
            temperature=0.7,
        )

        # Decode the generated text
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract likelihood percentage (basic parsing)
        try:
            likelihood = float(
                response.split("Likelihood of Account Deletion Functionality:")[-1]
                .split("%")[0]
                .strip()
            )
        except (ValueError, IndexError):
            likelihood = None

        return {"full_analysis": response, "likelihood_percentage": likelihood}
