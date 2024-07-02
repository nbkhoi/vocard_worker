class Prompt:
    def __init__(self, name: str):
        self._name = name
        self._content = Prompt._load_content(name)

    def content(self):
        return self._content

    def name(self):
        return self._name

    @staticmethod
    def _load_content(name: str):
        content = ""
        with open(f"prompts/{name.lower()}.txt", encoding='utf-8') as f:
            content = f.read()
        return content
