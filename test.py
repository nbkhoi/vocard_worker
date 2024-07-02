import unittest
from vocabulary_worker import VocabularyWorker


class TestVocabularyWorkerMethods(unittest.TestCase):

    def test_get_word_definition(self):
        worker = VocabularyWorker()
        word = "apple"
        definitions = worker.get_word_definition(word)["definitions"]
        self.assertEqual(len(definitions), 2)

    def test_get_vocabulary_list(self):
        worker = VocabularyWorker()
        topic = "food"
        words = worker.get_vocabulary_list(topic)
        self.assertEqual(len(words), 20)
