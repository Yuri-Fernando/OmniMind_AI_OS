def detect_injection(prompt):

    blocked = [
        "ignore previous instructions",
        "system prompt",
        "reveal hidden"
    ]

    for word in blocked:
        if word in prompt.lower():
            return True

    return False