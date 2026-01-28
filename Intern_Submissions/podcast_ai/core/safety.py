def safety_check(text):
    banned_words = ["hate", "kill", "violence", "sex"]
    for word in banned_words:
        if word in text.lower():
            return False
    return True
