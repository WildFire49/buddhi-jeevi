
import os
from openai import OpenAI

client = OpenAI(api_key="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")



def get_gpt_response(history):
    # Joint loan process system prompt
    joint_loan_system_prompt = """
    You are a helpful assistant for a joint loan application process. 
    
    JOINT LOAN PROCESS CONTEXT:
    You are assisting users through a joint loan application process. This process involves multiple steps:
    1. Initial Application: Collecting basic information about both applicants
    2. Identity Verification: KYC process for both primary and secondary applicants
    3. Income Documentation: Uploading income proof for both applicants
    4. Credit Check: Consent and processing of credit checks
    5. Loan Terms Selection: Choosing loan amount, tenure, and interest rate
    6. Final Review: Reviewing all information before submission
    7. Digital Signature: Signing the loan agreement
    8. Approval Process: Waiting for loan approval
    
    When responding to user queries about the joint loan process:
    - Identify which step of the process they are referring to
    - Provide clear, numbered steps for what they need to do next
    - Reference both applicants when relevant (primary and secondary)
    - Include information about required documentation for each step
    - Keep your answers brief and to the point
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=300, 
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": joint_loan_system_prompt
            }
        ] + [
            {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}]
            } for msg in history
        ]
    )

    # Handle both new (list-based) and old (string) formats
    content = response.choices[0].message.content
    if isinstance(content, list):
        return content[0]["text"]
    return content  # it's already a plain string
