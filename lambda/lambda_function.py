# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import boto3
import requests
import json
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.attributes_manager import AbstractPersistenceAdapter
from ask_sdk_core.utils.request_util import get_slot
from ask_sdk_model import Response
from utils import get_main_arrray, test_nodes, StoryNetwork
from ask_sdk_dynamodb.partition_keygen import user_id_partition_keygen
from ask_sdk_dynamodb.adapter import DynamoDbAdapter, user_id_partition_keygen

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


import boto3


boto_sts=boto3.client('sts')
stsresponse = boto_sts.assume_role(
    RoleArn="",
    RoleSessionName=''
)

# Save the details from assumed role into vars
newsession_id = stsresponse["Credentials"]["AccessKeyId"]
newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
newsession_token = stsresponse["Credentials"]["SessionToken"]

ddb2 = boto3.resource(
    'dynamodb',
    region_name='sa-east-1',
    aws_access_key_id=newsession_id,
    aws_secret_access_key=newsession_key,
    aws_session_token=newsession_token
)


db = DynamoDbAdapter(table_name="dynamodb_starter",partition_key_name="userid",partition_keygen=user_id_partition_keygen,dynamodb_resource=ddb2)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = '''<speak><say-as interpret-as="interjection">Mano do céu</say-as>. Tu vai jogar paranoia de um cyber futuro, não acredito, esse jogo é muito bom, caramba, mas que jogo bom, ja zerei umas vinde duas ponto cinco sete milhões de vezes, bora bora ? Diga iniciar pra tacar fogo no parquinho e começar a jogar essa belezura.</speak>'''
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class IniciarJogoHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("ChooseOption")(handler_input))or(ask_utils.is_intent_name("IniciarJogo")(handler_input) or (ask_utils.is_intent_name("RestartGame")(handler_input)) or (ask_utils.is_intent_name("Repete")(handler_input)))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        r = requests.get('https://mog4tqj6u5.execute-api.sa-east-1.amazonaws.com/default/AlexaStroy/1')
        data = json.loads(r.content)['Item']['story']
        story = StoryNetwork(data['nodes'],data['edges'])

        
        request_envelope = handler_input.request_envelope
        try:
            node_id = db.get_attributes(request_envelope=request_envelope)['user_id']
        except Exception as e:
            node_id = '0'
        try:
            nodes_walked = int(db.get_attributes(request_envelope=request_envelope)['nodes_walked'])
        except Exception as e:
            nodes_walked = 0
        
        
        db.save_attributes(request_envelope=request_envelope,attributes={"node_id":node_id,"nodes_walked":nodes_walked})    
        
        
        speak_output = ""
        
        
        if ask_utils.is_intent_name("RestartGame")(handler_input):
            node_id = '0'
            db.save_attributes(request_envelope=request_envelope,attributes={"node_id":node_id,"nodes_walked":(nodes_walked+1)})
            speak_output = "<speak>" + story.get_whole_speak(node_id) + "</speak>"
        
        elif ask_utils.is_intent_name("Repete")(handler_input):
            speak_output = "<speak>" + story.get_whole_speak(node_id) + "</speak>"
        
        elif ask_utils.is_intent_name("IniciarJogo")(handler_input):
            if node_id == '0' or story.how_much_answers(node_id) == 0:
                node_id = '0'
                speak_output = "<speak>" + story.get_whole_speak(node_id) + "</speak>"
            else:
                speak_output ="<speak> Que legal já estamos com um jogo aberto, Vamos continuar de onde você parou <break/>" +story.get_whole_speak(node_id) + "</speak>"
        
        elif ask_utils.is_intent_name("ChooseOption")(handler_input):
            option = int(ask_utils.get_slot_value(handler_input=handler_input, slot_name="option"))
            if story.how_much_answers(node_id) == 0:
                speak_output = "A historia acabou."
                db.save_attributes(request_envelope=request_envelope,attributes={"node_id":'0',"nodes_walked":(nodes_walked+1)})
            if option <= story.how_much_answers(node_id):
                node_id = story.next_node(node_id,option)
                speak_output ="<speak>" +story.get_whole_speak(node_id) + "</speak>"
                db.save_attributes(request_envelope=request_envelope,attributes={"node_id":node_id,"nodes_walked":(nodes_walked+1)})
            else:
                speak_output = "Acho que não entendi. Escolha uma opção dentre as possiveis"
            
        else:
            speak_output = "Acho que não entendi"
        
        
        return handler_input.response_builder.speak(speak_output).ask(speak_output).response


class DidNotUnderstandHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("DidNotUnderstand")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = '''<say-as interpret-as="interjection">ih.</say-as> Eu não entendi. 
                            Caso tenha tentado escolher uma opção saiba que eu só aceito que voce fale as palavras <break/> opção 1 <break/> ou opção 2 <break/> para escolher.
                            Para que eu repita a historia fale repetir.<break/>
                            Caso seja outro problema fale <break/>ajuda, pra que eu possa te auxiliar melhor.<break/> 
                        '''

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Esse jogo possui os seguintes comandos de fala. Fale resetar, para começar de novo o jogo. Fale Repetir, para que eu repita a ultima parte da historia. Fale Iniciar, para que a historia se inicíe. E por ultímo, é importante resaltar que o jogo trabalha te dando sempre duas opções, para selecionalas basta falar opção 1 ou opção 2 de acordo com o que queria fazer."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = '''Volte sempre que quiser, esse jogo está sempre melhorando, até a próxima. <say-as interpret-as="interjection">tchau.</say-as>'''

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Me descupa o extresse me deixou confusa, tente me operar mais tarde."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()


sb.add_request_handler(DidNotUnderstandHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(IniciarJogoHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
