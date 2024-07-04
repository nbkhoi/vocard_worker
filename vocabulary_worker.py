# This is Vocabulary Worker, an AI-powered Python script that can help users generate English vocabulary data.
import asyncio
import concurrent.futures
import logging
import multiprocessing
import os
import threading
import datetime
from openai import OpenAI
import json
from dotenv import load_dotenv

from prompt_engineer import Prompt


# Define a VocabularyWorker static class
class VocabularyWorker:
    LOGGER = logging.getLogger(__name__)

    def __init__(self):
        load_dotenv()
        self.client = OpenAI()

    def get_word_definition(self, word, context=None):
        prompt = Prompt("get_word_definition") if not context else Prompt("get_word_definition_in_context")
        # start time tracking
        start_time = datetime.datetime.now()
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt.content()},
                {"role": "user", "content": f"Word: {word}"} if not context else
                {"role": "user", "content": f"Word: {word}, Context: {context}"}
            ]
        )

        json_string = completion.choices[0].message.content
        return json.loads(json_string)

    def get_vocabulary_list(self, topic):
        prompt = Prompt("get_vocabulary_list")
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt.content()},
                {"role": "user", "content": f"Theme: {topic}"}
            ]
        )

        # print(completion.choices[0].message)
        # extract the JSON string from the completion.choices[0].message
        json_string = completion.choices[0].message.content
        # convert the JSON string to a Python dictionary
        return json.loads(json_string)["vocabularies"]


def write_data_to_file(data, filename, encoding='utf-8'):
    # check if the output folder exists. Otherwise, create it
    if not os.path.exists("output"):
        os.makedirs("output")
    with open(f"output/{filename}", "w", encoding=encoding) as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def generate(topic):
    worker = VocabularyWorker()
    words = worker.get_vocabulary_list(topic)
    data = {"title": topic, "vocabularies": []}
    for word in words:
        definitions = worker.get_word_definition(word, topic)["definitions"]
        data["vocabularies"].extend(definitions)
    filename = f"{topic.replace(' ', '_').lower()}.json"
    thread = threading.Thread(target=write_data_to_file, args=(data, filename))
    thread.start()


def add_element_to_list(lock, shared_list, word):
    # Log the word being processed
    print(f"Processing word: {word}")
    start_time = datetime.datetime.now()
    worker = VocabularyWorker()
    word_definitions = worker.get_word_definition(word)
    definitions = word_definitions["definitions"]
    with lock:
        shared_list.extend(definitions)
        # Sort the shared_list by the word, alphabetically ascending
        shared_list.sort(key=lambda x: x["word"])
    end_time = datetime.datetime.now()
    # Log the time taken to process the word
    print(f"Time taken to process word: {word}: {end_time - start_time}")
    return f'Added {word}'


def generate_from_file(filename: str):
    path: str = f"input/{filename}"
    words = []
    with open(path, "r", encoding='utf-8') as f:
        json_data = json.load(f)
        title = filename.replace(".json", "").replace("_", " ").title()
        words = json_data["words"]
    return_data = {"title": title, "vocabularies": []}
    # queue = multiprocessing.Queue()
    # processes = []
    # for word in words:
    #     process = multiprocessing.Process(target=add_element_to_list, args=(queue, word))
    #     processes.append(process)
    #     process.start()
    # start_wait_time = datetime.datetime.now()
    # for process in processes:
    #     process.join()
    # end_wait_time = datetime.datetime.now()
    # print(f"Time taken to wait for all processes to finish: {end_wait_time - start_wait_time}")
    # start_queue_check_out_time = datetime.datetime.now()
    # while not queue.empty():
    #     return_data["vocabularies"].append(queue.get())
    # end_queue_check_out_time = datetime.datetime.now()
    # print(f"Time taken to check out all elements from the queue: {end_queue_check_out_time - start_queue_check_out_time}")
    # start_time = datetime.datetime.now()
    # # Sort the vocabularies by the word, alphabetically ascending
    # return_data["vocabularies"].sort(key=lambda x: x["word"])
    # end_time = datetime.datetime.now()
    # print(f"Time taken to sort the vocabularies: {end_time - start_time}")
    lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(add_element_to_list, lock, return_data["vocabularies"], word) for word in words]

        for future in concurrent.futures.as_completed(futures):
            print(future.result())
    # await asyncio.gather(*[add_element_to_list(return_data["vocabularies"], word) for word in words])
    # for word in words:
    #     definitions = worker.get_word_definition(word)["definitions"]
    #     data["vocabularies"].extend(definitions)
    #     processed_words += 1
    #     completion_percentage = (processed_words / total_words) * 100
    #     print(f"Completion: {completion_percentage:.2f}%")
    return return_data


if __name__ == "__main__":
    # while True:
    #     topic = input("Enter a topic (leave empty to break): ")
    #     if not topic:
    #         break
    #     thread1 = threading.Thread(target=generate, args=(topic,))
    #     thread1.start()

    data = generate_from_file("oxford_3000_-_the_most_important_words_to_learn_in_english.json")
    write_data_to_file(data, "oxford_3000_-_the_most_important_words_to_learn_in_english.json")
