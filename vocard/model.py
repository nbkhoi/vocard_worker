class Module:
    def __init__(self, title: str, description: str = None, **kwargs):
        self.title = title
        self.description = description
        self.__dict__.update(kwargs)

    @staticmethod
    def validate(data):
        required_keys = {'title'}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - set(data.keys())}")
        if not isinstance(data['title'], str):
            raise ValueError(f"title must be a string")
        if 'description' in data and not isinstance(data['description'], str):
            raise ValueError(f"description must be a string")


class Topic:
    def __init__(self, module: str, title: str, description: str = None, **kwargs):
        self.module = module
        self.title = title
        self.description = description
        self.__dict__.update(kwargs)

    @staticmethod
    def validate(data):
        required_keys = {'module', 'title'}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - set(data.keys())}")
        if not isinstance(data['module'], str):
            raise ValueError(f"module must be a string")
        if not isinstance(data['title'], str):
            raise ValueError(f"title must be a string")
        if 'description' in data and not isinstance(data['description'], str):
            raise ValueError(f"description must be a string")


class Card:
    def __init__(self, topic: str, word: str, partOfSpeech: str, definition: str, ipaUk: str = None, ipaUs: str = None,
                 pronUk: str = None, pronUs: str = None, meaningVi: str = None, exampleSentence: str = None, **kwargs):
        self.topic = topic
        self.word = word
        self.partOfSpeech = partOfSpeech
        self.definition = definition
        self.ipaUk = ipaUk
        self.ipaUs = ipaUs
        self.pronUk = pronUk
        self.pronUs = pronUs
        self.meaningVi = meaningVi
        self.exampleSentence = exampleSentence
        self.__dict__.update(kwargs)

    @staticmethod
    def validate(data):
        required_keys = {'topic', 'word', 'partOfSpeech', 'definition'}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - set(data.keys())}")
        if not isinstance(data['word'], str):
            raise ValueError(f"word must be a string")
        if not isinstance(data['partOfSpeech'], str):
            raise ValueError(f"partOfSpeech must be a string")
        if not isinstance(data['definition'], str):
            raise ValueError(f"definition must be a string")
        if 'partitionKey' in data and not isinstance(data['partitionKey'], str):
            raise ValueError(f"partitionKey must be a string")
        if 'rowKey' in data and not isinstance(data['rowKey'], str):
            raise ValueError(f"rowKey must be a string")
        if 'ipaUk' in data and not isinstance(data['ipaUk'], str):
            raise ValueError(f"ipaUk must be a string")
        if 'ipaUs' in data and not isinstance(data['ipaUs'], str):
            raise ValueError(f"ipaUs must be a string")
        if 'pronUk' in data and not isinstance(data['pronUk'], str):
            raise ValueError(f"pronUk must be a string")
        if 'pronUs' in data and not isinstance(data['pronUs'], str):
            raise ValueError(f"pronUs must be a string")
        if 'meaningVi' in data and not isinstance(data['meaningVi'], str):
            raise ValueError(f"meaningVi must be a string")
        if 'exampleSentence' in data and not isinstance(data['exampleSentence'], str):
            raise ValueError(f"exampleSentence must be a string")
