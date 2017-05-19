from django.core.management.base import BaseCommand, CommandError
from polls.models import Question, get_active_poll
from channels.asgi import get_channel_layer
from channels.sessions import session_for_reply_channel
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
import time, datetime
import json

'''
The purpose of this command is remain in an infinite loop
each iteration it tests assesses the state of the poll against each users session data
before messaging relevant change in poll state to the user 
a poll could be inactive, closed or starting
'''


class Command(BaseCommand):
    def handle(self, *args, **options):

        def get_reply_channels():
            return channel_layer.group_channels('poll')

        def get_reply_channel_sessions(channel):
            channel_session = session_for_reply_channel(channel)
            http_session = SessionStore(session_key=channel_session.get('http_session_key'))
            return {
                "channel": channel_session,
                "http": http_session
            }

        # variables to help keep track of the poll status
        channel_layer = get_channel_layer()
        active_question = None
        last_active = None

        while True:

            question = get_active_poll()

            # poll inactive
            if not question:
                # poll has just finished
                if active_question is not None:
                    active_question = None
                    last_active = timezone.now()
                    for channel in reply_channels:
                        sessions = get_reply_channel_sessions(channel)
                        sessions['http']['loaded_question'] = None
                        sessions['http']['has_voted'] = False
                        sessions['http'].save()
                # poll finished a short time ago though there is a 5 minute time delay before messaging users
                elif last_active and timezone.now() >= (last_active + datetime.timedelta(minutes=5)):
                    reply_channels = get_reply_channels()
                    for channel in reply_channels:
                        sessions = get_reply_channel_sessions(channel)
                        # if the users session data says the poll is open or closed
                        # update the session data and message them the poll has ended
                        if sessions['http'].get('poll_status') == True \
                                or sessions['http'].get('poll_status') == False:
                            sessions['http']['poll_status'] = None
                            sessions['http'].save()
                            channel_layer.send(channel, {"text": json.dumps({"poll_ended": True})})

            elif question:
                # poll closing
                if question == active_question and not question.is_open():
                    reply_channels = get_reply_channels()
                    for channel in reply_channels:
                        sessions = get_reply_channel_sessions(channel)
                        # if the users session data says the poll is open
                        # update the session data and message them the poll has closed
                        if sessions['http'].get('poll_status') == True:
                            sessions['http']['poll_status'] = False
                            sessions['http'].save()
                            channel_layer.send(channel, {"text": json.dumps({"poll_closed": True})})

                # new poll starting
                elif not question == active_question:
                    # make sure there isn't a rogue question trying to start
                    if active_question is not None:
                        assert active_question.is_active(), "active poll conflict"

                    active_question = question
                    last_active = None
                    print(active_question)
                    reply_channels = get_reply_channels()
                    for channel in reply_channels:
                        sessions = get_reply_channel_sessions(channel)
                        # if the users session data says the poll is closed or there is no poll at all
                        # update the session data and message them the poll has opened
                        if sessions['http'].get('poll_status') == False \
                                or sessions['http'].get('poll_status') == None:
                            sessions['http']['loaded_question'] = question.id
                            sessions['http']['poll_status'] = True
                            sessions['http']['has_voted'] = False
                            sessions['http'].set_expiry(question.seconds_remaining() + 3600)
                            sessions['http'].save()
                            # send all the data that the poll ui needs to render a new poll
                            channel_layer.send(channel, {"text": json.dumps({"poll_opening": {
                                "question_id": question.id,
                                "question_text": question.question_text,
                                "vote_limit": question.vote_limit,
                                "one_vote_only": question.one_vote_only,
                                "choices": question.ordered_list_choices(),
                                "has_voted": sessions['http'].get('has_voted')
                            }})})

            time.sleep(1)
