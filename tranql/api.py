"""
Provide a standard protocol for asking graph oriented questions of Translator data sources.
"""
import copy
import argparse
import json
import logging
import os
import traceback
import yaml
import jsonschema
import requests
from flask import Flask, request, abort, Response, send_from_directory
from flask_restful import Api, Resource
from flasgger import Swagger
from flask_cors import CORS
from tranql.concept import ConceptModel
from tranql.main import TranQL
import networkx as nx
from tranql.util import JSONKit
from tranql.concept import BiolinkModelWalker
from tranql.exception import TranQLException
#import flask_monitoringdashboard as dashboard

logger = logging.getLogger (__name__)

web_app_root = os.path.join (os.path.dirname (__file__), "..", "web", "build")

app = Flask(__name__, static_folder=web_app_root)
#dashboard.bind(app)

api = Api(app)
CORS(app)

app.config['SWAGGER'] = {
    'title': 'TranQL API',
    'description': 'Translator Query Language (TranQL) API',
    'uiversion': 3
}
swagger = Swagger(app) #, template=template)

class StandardAPIResource(Resource):
    def validate (self, request):
        with open(filename, 'r') as file_obj:
            specs = yaml.load(file_obj)
        to_validate = specs["components"]["schemas"]["Message"]
        to_validate["components"] = specs["components"]
        to_validate["components"].pop("Message", None)
        try:
            jsonschema.validate(request.json, to_validate)
        except jsonschema.exceptions.ValidationError as error:
            logging.error (f"ERROR: {str(error)}")
            abort(Response(str(error), 400))

class WebAppRoot(Resource):
    def get(self):
        """
        webapp root
        ---
        consumes': [ 'text/plain' ]
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string
        """
        return send_from_directory(web_app_root, 'index.html')
api.add_resource(WebAppRoot, '/', endpoint='webapp_root')

class WebAppPath(Resource):
    def get(self, path):
        """
        webapp
        ---
        parameters:
            - in: path
              name: path
              type: string
              required: true
              description: Resource path.
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string
        """
        resource_path = os.path.join (os.path.dirname (__file__), os.path.sep, path)
        logger.debug (f"--path: {resource_path}")
        if path != "" and os.path.exists(web_app_root + "/" + path):
            return send_from_directory(web_app_root, path)
        else:
            abort (404)
api.add_resource(WebAppPath, '/<path:path>', endpoint='webapp_path')


class Configuration(StandardAPIResource):
    """ Configuration """
    def get(self):
        """
        configuration
        ---
        tag: validation
        description: TranQL Query
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string

        """
        return {
            "api_url" : config['API_URL'],
            "robokop_url" : config['ROBOKOP_URL']
        }

class TranQLQuery(StandardAPIResource):
    """ TranQL Resource. """

    def __init__(self):
        super().__init__()
        
    def post(self):
        """
        query
        ---
        tag: validation
        description: TranQL Query
        requestBody:
            description: Input message
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            query:
                                type: string
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string

        """
        #self.validate (request)
        result = {}
        try:
            tranql = TranQL ()
            logging.debug (request.json)
            query = request.json['query'] if 'query' in request.json else ''
            logging.debug (f"----------> query: {query}")
            context = tranql.execute (query) #, cache=True)
            result = context.mem.get ('result', {})
            logger.debug (f" -- backplane: {context.mem.get('backplane', '')}")
        except TranQLException as e:
            result = {
                "status" : "error",
                "message" : str(e),
                "details" : e.details
            }
        except Exception as e:
            traceback.print_exc (e)
            result = {
                "status" : "error",
                "message" : str(e),
                "details" : ''
            }
        return result

class ModelConceptsQuery(StandardAPIResource):
    """ Query model concepts. """

    def __init__(self):
        super().__init__()
        
    def post(self):
        """
        query
        ---
        tag: validation
        description: TranQL Query
        requestBody:
            description: Input message
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            query:
                                type: string
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string

        """
        concept_model = ConceptModel ("biolink-model")
        concepts = sorted (list(concept_model.by_name.keys ()))
        logging.debug (concepts)
        return concepts


class ModelRelationsQuery(StandardAPIResource):
    """ Query model relations. """

    def __init__(self):
        super().__init__()
        
    def post(self):
        """
        query
        ---
        tag: validation
        description: TranQL concept model relations query.
        requestBody:
            description: Input message
            required: true
            content:
                application/json:
                    schema:
                        type: object
                        properties:
                            query:
                                type: string
        responses:
            '200':
                description: Success
                content:
                    text/plain:
                        schema:
                            type: string
                            example: "Successfully validated"
            '400':
                description: Malformed message
                content:
                    text/plain:
                        schema:
                            type: string

        """
        concept_model = ConceptModel ("biolink-model")
        relations = sorted (list(concept_model.relations_by_name.keys ()))
        logging.debug (relations)
        return relations

###############################################################################################
#
# Define routes.
#
###############################################################################################

api.add_resource(TranQLQuery, '/tranql/query')
api.add_resource(ModelConceptsQuery, '/tranql/model/concepts')
api.add_resource(ModelRelationsQuery, '/tranql/model/relations')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('-port', action="store", dest="port", default=8001, type=int)
    args = parser.parse_args()
    server_host = '0.0.0.0'
    server_port = args.port
    app.run(
        host=server_host,
        port=server_port,
        debug=False,
        use_reloader=True
    )
