from dotenv import load_dotenv
from datetime import datetime
import os

# Import namespaces
import azure.cognitiveservices.speech as speech_sdk

def main():
    try:
        global speech_config

        # Get Configuration Settings
        load_dotenv()
        speech_key = os.getenv('SPEECH_KEY')
        speech_region = os.getenv('SPEECH_REGION')
        speech_language = 'es-ES'

        # Configure speech service
        speech_config = speech_sdk.SpeechConfig(speech_key, speech_region, speech_recognition_language=speech_language)

        speech_config.set_property(speech_sdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
        speech_config.set_property(speech_sdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "2000")
        speech_config.set_property(speech_sdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "5000")

        print('Ready to use speech service in:', speech_config.region)

        # Get spoken input
        transcription = speech_recognize_continuous()
        texto_final = ""
        print('-------------- FULL TRANSCRIPCION --------------')
        for text in transcription:
            print(text)
            texto_final = texto_final + text + " "
        print('----------------------------------------------------')
        print(openai_functions(texto_final))

    except Exception as ex:
        print(ex)

     
def speech_recognize_continuous():
    import time
    
    # Performs continuous speech recognition from microphone
    audio_config = speech_sdk.AudioConfig(use_default_microphone=True)
    speech_recognizer = speech_sdk.SpeechRecognizer(speech_config, audio_config)
    done = False

    def stop_cb(evt: speech_sdk.SessionEventArgs):
        """callback that signals to stop continuous recognition upon receiving an event `evt`"""
        print('CLOSING')
        nonlocal done
        done = True
    
    def speech_recognizer_recognition_canceled_cb(evt: speech_sdk.SessionEventArgs):
        print('Canceled event')

    def speech_recognizer_session_stopped_cb(evt: speech_sdk.SessionEventArgs):
        print('SessionStopped event')

    def speech_recognizer_transcribed_cb(evt: speech_sdk.SpeechRecognitionEventArgs):
        print('TRANSCRIBED:')
        if evt.result.reason == speech_sdk.ResultReason.RecognizedSpeech:
            print(f'\tText: {evt.result.text}')
        elif evt.result.reason == speech_sdk.ResultReason.NoMatch:
            print(f'\tNOMATCH: Speech could not be TRANSCRIBED: {evt.result.no_match_details}')
            stop_cb(evt)

    def speech_recognizer_session_started_cb(evt: speech_sdk.SessionEventArgs):
        print('SessionStarted event')

    # Connect callbacks to the events fired by the speech recognizer
    speech_recognizer.recognized.connect(speech_recognizer_transcribed_cb)
    all_results = []
    def handle_final_result(evt):
        all_results.append(evt.result.text)
    speech_recognizer.recognized.connect(handle_final_result)
    speech_recognizer.session_started.connect(speech_recognizer_session_started_cb)
    speech_recognizer.session_stopped.connect(speech_recognizer_session_stopped_cb)
    speech_recognizer.canceled.connect(speech_recognizer_recognition_canceled_cb)
    # stop transcribing on either session stopped or canceled events
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)

    # Start continuous speech recognition
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)

    speech_recognizer.stop_continuous_recognition()

    return all_results

def openai_functions(text):
    # Add OpenAI library
    import os
    from openai import AzureOpenAI
    from dotenv import load_dotenv

    try:
        load_dotenv()
        my_api_key=os.getenv("AZURE_OPENAI_KEY")
        my_azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')

        client = AzureOpenAI(
            api_key=my_api_key,
            api_version="2023-12-01-preview", #2023-03-15-preview
            azure_endpoint =my_azure_endpoint
        )

        message_text = [
                {"role": "system", "content": "Eres un agente experto en hacer resumenes de conversaciones, identificar entidades y clasificar el sentimiento en positivo, negativo o neutro."},
                {"role": "user", "content": "Resume la siguiente conversación de una llamada a un contact center marcado entre triple comillas, extrae las entidades clave e identifica el sentimiento general '''" + text + "'''"}
            ]

        response = client.chat.completions.create(
            model=deployment_name,
            messages = message_text
        )

        return(response.choices[0].message.content)
        #print(response.choices[0].message.content)

    except Exception as ex:
        print(ex)

if __name__ == "__main__":
    main()