from src.utilities.inference2 import call_llm, call_openai


async def peer_review_service(original, style, persona, model):
    prompt = ("INSTRUCTIONS:"
              "1. You are a peer reviewer."
              f"2. You will peer review the article based on {style} style of writing."
              f"3. List instructions on how to improve and fix the text for the requested style."
              f"4. Article to review: {original}")
    if model == "oai":
        response = await call_llm(prompt, 6000, "/ask_an_expert")
    else:
        response = await call_openai(prompt)
    return response


async def final_draft(original, style, persona, review, model):
    prompt = ("INSTRUCTIONS:"
              f"1. You are an expert {style} writer."
              f"2. You will peer review the feedback and improve the original based on {review}."
              f"3. Respond with only the final draft of the revised and improved original."
              f"4. Original to review: {original}")
    if model == "oai":
        response = await call_llm(prompt, 6000, "/ask_an_expert")
    else:
        response = await call_openai(prompt)
    return response
