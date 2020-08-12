import logging
import os
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from ast import literal_eval as make_tuple

class Node():
    def __init__(self,obj_id, text, a_answer, b_answer):
        self.obj_id = int(obj_id)
        self.text = text
        self.a_answer = make_tuple(a_answer)
        self.b_answer = make_tuple(b_answer)
        
    def __repr__(self):
        return str(self.obj_id)
        
    def speak_text(self):
        return self.text
        
    def get_answer_options(self):
        return (self.a_answer,self.b_answer)
        
    def get_whole_speak(self):
        speak_output = self.speak_text() + self.speak_answer_options()
        return speak_output
        
    def speak_answer_options(self):
        if not(self.a_answer[1] == "" and self.a_answer[1] == ""): 
            return '<break time="1s"/>  Opção um <break/>'+ self.a_answer[1] +'<break time="1s"/> Opção dois <break/>'+ self.b_answer[1]
        else:
            return ""
    def next_node(self, option):
        if option == 1:
            return self.a_answer[0]
        elif option == 2:
            return self.b_answer[0]
        else:
            return 0

def get_main_arrray():
    all_nodes = []
    history = pd.read_csv("story.csv",delimiter=';')
    for index, row in history.iterrows():
        all_nodes.append(Node(obj_id=row["id"],text=row["text"],a_answer=row["a_answer"],b_answer=row["b_answer"]))
    return all_nodes


def test_nodes(main_arrray):
    speak_output = ""
    for node in main_arrray:
        speak_output = speak_output + node.get_whole_speak()
    return speak_output

def create_presigned_url(object_name):
    """Generate a presigned URL to share an S3 object with a capped expiration of 60 seconds

    :param object_name: string
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4',s3={'addressing_style': 'path'}))
    try:
        bucket_name = os.environ.get('S3_PERSISTENCE_BUCKET')
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=60*1)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response


class StoryNetwork():
    def __init__(self,nodes,edges):
        self.story_dict = {}
        for n in nodes:
            self.story_dict[n['id']] = {'text':n['label'],'edges':[]}
            for e in edges:
                if(e['from'] == n['id']):
                    self.story_dict[n['id']]['edges'].append((e['to'],e['label']))
    
    
    def speak_text(self,obj_id):
        return self.story_dict[obj_id]['text']
    
    def speak_answer_options(self,obj_id):
        answer_string = ""
        if(self.story_dict[obj_id]['edges'] == []):
            return '<break time="1s"/>O jogo acabou, mas não fique triste, você pode jogar de novo, basta falar reiniciar, mas se quiser sair fale, parar jogo'
        
        for i, answer in enumerate(self.story_dict[obj_id]['edges']):
            answer_string = answer_string + '<break time="1s"/>  Opção {} <break/>'.format(i+1)+ answer[1] +'<break time="1s"/>'
        return answer_string
    
    def get_whole_speak(self,obj_id):
        speak_output = self.speak_text(obj_id) +' '+ self.speak_answer_options(obj_id)
        return speak_output
    
    def next_node(self, obj_id,option):
        for i,answer in enumerate(self.story_dict[obj_id]['edges']):
            if option == (i+1):
                return answer[0]
        return 0
    def how_much_answers(self, obj_id):
        return len(self.story_dict[obj_id]['edges'])
