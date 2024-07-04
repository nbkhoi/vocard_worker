# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(ai/word_def_asst)
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints
import json

import azure.functions as func
import logging
from vocabulary_worker import VocabularyWorker as worker

assistant = func.Blueprint()


@assistant.route(route="definitions/gen", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.ANONYMOUS)
def generate_definitions(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    req_body = req.get_json()
    if req_body is None:
        return func.HttpResponse("Please pass a JSON object in the request body", status_code=400)
    if 'word' not in req_body:
        return func.HttpResponse("Please provide a word in the request body", status_code=400)
    word = req_body.get('word')
    topic = req_body.get('topic')
    worker_instance = worker()
    response = worker_instance.get_word_definition(word, topic)

    return func.HttpResponse(json.dumps(response), status_code=200)