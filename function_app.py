import json
import re
import uuid
from datetime import datetime

import azure.functions as func
import azure.data.tables as tbls
import logging
import os

from ai.word_def_asst import assistant
from vocard.model import Card, Topic, Module

app = func.FunctionApp()
app.register_functions(assistant)

tbl_service = tbls.TableServiceClient.from_connection_string(os.environ['StorageConnectionString'])


def keyify(s):
    # Convert to lowercase
    s = s.lower()
    # Replace spaces with underscores
    s = s.replace(' ', '_')
    # Remove all characters that are not lowercase letters or underscores
    s = re.sub(r'[^a-z_]', '', s)
    return s


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


@app.function_name("CreateCard")
@app.route(route="cards/create", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.ANONYMOUS)
def create_new_card(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    req_body = req.get_json()
    try:
        Card.validate(req_body)
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": keyify(req_body['topic']),
                "RowKey": str(uuid.uuid4())
            }
        )
        table_client = tbl_service.get_table_client("Cards")
        result = table_client.create_entity(entity=req_body)
        return func.HttpResponse(json.dumps(result, cls=CustomJSONEncoder), status_code=200)


@app.function_name("UpdateCard")
@app.route(route="cards/{topicKey}/{cardKey}/change", methods=[func.HttpMethod.PUT], auth_level=func.AuthLevel.ANONYMOUS)
def update_card(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    partition_key = req.route_params.get('topicKey')
    row_key = req.route_params.get('cardKey')
    table_client = tbl_service.get_table_client("Cards")
    # Check if the card exists
    card = table_client.get_entity(partition_key, row_key)
    if not card:
        return func.HttpResponse("Not Found", status_code=404)
    # Log existing card
    logging.info(f"Existing card: {card}")
    req_body = req.get_json()
    try:
        Card.validate(req_body)
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": partition_key,
                "RowKey": row_key
            }
        )
        try:
            result = table_client.update_entity(entity=req_body)
        except Exception as e:
            return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
        else:
            return func.HttpResponse(json.dumps(result, cls=CustomJSONEncoder), status_code=200)


@app.function_name("DeleteCard")
@app.route(route="cards/{topicKey}/{cardKey}/delete", methods=[func.HttpMethod.DELETE], auth_level=func.AuthLevel.ANONYMOUS)
def delete_card(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    partition_key = req.route_params.get('topicKey')
    row_key = req.route_params.get('cardKey')
    table_client = tbl_service.get_table_client("Cards")
    # Check if the card exists
    card = table_client.get_entity(partition_key, row_key)
    if not card:
        return func.HttpResponse("Not Found", status_code=404)
    try:
        table_client.delete_entity(partition_key, row_key)
    except Exception as e:
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
    else:
        return func.HttpResponse(status_code=200)


@app.function_name("GetCards")
@app.route(route="cards/{topicKey}", methods=[func.HttpMethod.GET], auth_level=func.AuthLevel.ANONYMOUS)
def get_cards_by_topic(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    partition_key = req.route_params.get('topicKey')
    page_size = int(req.params.get('pageSize', 10))
    continuation_token = req.params.get('continuationToken', None)
    table_client = tbl_service.get_table_client("Cards")
    query = f"PartitionKey eq '{partition_key}'"

    # Query the table with pagination
    cards = []
    try:

        pages = table_client.query_entities(
            query_filter=query,
            results_per_page=page_size
        ).by_page(continuation_token=continuation_token)

    except Exception as e:
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
    except StopIteration:
        next_continuation_token = None
    else:
        first_page = next(pages)
        cards.extend(list(first_page))
        # Extract the continuation token for the next page, if it exists
        if 'x-ms-continuation-NextPartitionKey' in first_page.additional_properties:
            next_partition_key = first_page.additional_properties['x-ms-continuation-NextPartitionKey']
        if 'x-ms-continuation-NextRowKey' in first_page.additional_properties:
            next_row_key = first_page.additional_properties['x-ms-continuation-NextRowKey']
        if next_partition_key or next_row_key:
            next_continuation_token = {
                'PartitionKey': next_partition_key,
                'RowKey': next_row_key
            }
        else:
            next_continuation_token = None
        response = {
            'cards': cards,
            'continuationToken': next_continuation_token
        }
        return func.HttpResponse(json.dumps(response), status_code=200)


@app.function_name("CreateTopic")
@app.route(route="topics/create", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.ANONYMOUS)
def create_new_topic(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    req_body = req.get_json()
    try:
        Topic.validate(req_body)
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": keyify(req_body['module']),
                "RowKey": keyify(req_body['title'])
            }
        )
        table_client = tbl_service.get_table_client("Topics")
        result = table_client.create_entity(entity=req_body)['content']
        return func.HttpResponse(json.dumps(result), status_code=200)


@app.function_name("UpdateTopic")
@app.route(route="topics/{moduleKey}/{topicKey}/change", methods=[func.HttpMethod.PUT], auth_level=func.AuthLevel.ANONYMOUS)
def update_topic(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    partition_key = req.route_params.get('moduleKey')
    row_key = req.route_params.get('topicKey')
    table_client = tbl_service.get_table_client("Topics")
    # Check if the topic exists
    topic = table_client.get_entity(partition_key, row_key)
    if not topic:
        return func.HttpResponse("Not Found", status_code=404)
    req_body = req.get_json()
    try:
        Topic.validate(req_body)
        if req_body['title'] != row_key:
            raise ValueError("Changing topic title is not allowed.")
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": partition_key,
                "RowKey": row_key
            }
        )
        try:
            result = table_client.update_entity(entity=req_body)
        except Exception as e:
            return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
        else:
            return func.HttpResponse(json.dumps(result, cls=CustomJSONEncoder), status_code=200)


@app.function_name("DeleteTopic")
@app.route(route="topics/{moduleKey}/{topicKey}/delete", methods=[func.HttpMethod.DELETE], auth_level=func.AuthLevel.ANONYMOUS)
def delete_topic(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    partition_key = req.route_params.get('moduleKey')
    row_key = req.route_params.get('topicKey')
    table_client = tbl_service.get_table_client("Topics")
    # Check if the topic exists
    topic = table_client.get_entity(partition_key, row_key)
    if not topic:
        return func.HttpResponse("Not Found", status_code=404)
    try:
        table_client.delete_entity(partition_key, row_key)
    except Exception as e:
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
    else:
        return func.HttpResponse(status_code=200)


@app.function_name("CreateModule")
@app.route(route="modules/create", methods=[func.HttpMethod.POST], auth_level=func.AuthLevel.ANONYMOUS)
def create_new_module(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    req_body = req.get_json()
    try:
        Module.validate(req_body)
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": 'default',
                "RowKey": keyify(req_body['title'])
            }
        )
        table_client = tbl_service.get_table_client("Modules")
        result = table_client.create_entity(entity=req_body)['content']
        return func.HttpResponse(json.dumps(result), status_code=200)


@app.function_name("UpdateModule")
@app.route(route="modules/{moduleKey}/change", methods=[func.HttpMethod.PUT], auth_level=func.AuthLevel.ANONYMOUS)
def update_module(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    row_key = req.route_params.get('moduleKey')
    table_client = tbl_service.get_table_client("Modules")
    # Check if the module exists
    module = table_client.get_entity('default', row_key)
    if not module:
        return func.HttpResponse("Not Found", status_code=404)
    # Log existing module
    logging.info(f"Existing module: {module}")
    req_body = req.get_json()
    try:
        Module.validate(req_body)
    except ValueError as e:
        return func.HttpResponse(f"Bad Request: {str(e)}", status_code=400)
    else:
        req_body.update(
            {
                "PartitionKey": 'default',
                "RowKey": row_key
            }
        )
        try:
            result = table_client.update_entity(entity=req_body)
        except Exception as e:
            return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
        else:
            return func.HttpResponse(json.dumps(result, cls=CustomJSONEncoder), status_code=200)


@app.function_name("DeleteModule")
@app.route(route="modules/{moduleKey}/delete", methods=[func.HttpMethod.DELETE], auth_level=func.AuthLevel.ANONYMOUS)
def delete_module(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    row_key = req.route_params.get('moduleKey')
    table_client = tbl_service.get_table_client("Modules")
    # Check if the module exists
    module = table_client.get_entity('default', row_key)
    if not module:
        return func.HttpResponse("Not Found", status_code=404)
    try:
        table_client.delete_entity('default', row_key)
    except Exception as e:
        return func.HttpResponse(f"Internal Server Error: {str(e)}", status_code=500)
    else:
        return func.HttpResponse(status_code=200)
