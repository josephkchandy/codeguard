import re


class BugTools:

    @staticmethod
    def tokenize(text: str):

        text = text.lower()

        words = re.findall(r"[a-zA-Z_]+", text)

        return set(words)