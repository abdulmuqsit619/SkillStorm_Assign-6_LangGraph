from langchain_aws import ChatBedrockConverse

from policy_assistant.config import AWS_REGION, BEDROCK_MODEL_ID


def get_chat_model():
    return ChatBedrockConverse(
        model=BEDROCK_MODEL_ID,
        region_name=AWS_REGION,
        temperature=0.0,
        max_tokens=500,
    )