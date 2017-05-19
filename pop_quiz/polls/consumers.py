import json
from channels import Group
from channels.sessions import channel_session
from channels.auth import http_session
from django.contrib.sessions.backends.db import SessionStore
from .models import Question, Choice


# Connected to websocket.connect
@http_session
@channel_session
def ws_connect(message):
    message.reply_channel.send({"accept": True})
    # keep a reference to the http session in the channel session
    # channel sessions change with each new browser session
    # so important client variables will be kept in the http session
    if message.http_session: message.channel_session['http_session_key'] = message.http_session.session_key
    Group("poll").add(message.reply_channel)


# Connected to websocket.receive
@channel_session
def ws_receive(message):
    data = json.loads(message['text'])
    # make a reference to the http session using the saved key
    http_session = SessionStore(session_key=message.channel_session.get('http_session_key'))
    question = Question.objects.get(pk=data.get('question_id'))
    # if any of these asserts go off I expect someone got left behind or the site is under attack
    assert isinstance(question, Question), "question does not exist"
    assert question.is_active(), "question is not active"

    # the message is then handled one of two ways based on the parent key sent within the message data

    if 'vote' in data:
        selected_choice = question.choice_set.get(pk=data.get('choice_id'))
        assert isinstance(selected_choice, Choice), "choice does not exist"

        # tell the group that the poll has closed if a poll choice reaches its limit or the poll is already closed
        if selected_choice.votes >= question.vote_limit or not question.is_open():
            Group("poll").send({"text": json.dumps({"poll_closed": True}), })
        # when one vote only allowed the users vote choice is stored to maybe be undone before the poll closes
        # it also returns a vote confirmation message to the individual user
        elif question.one_vote_only and http_session.get('has_voted') == False:
            http_session['has_voted'] = True
            http_session['vote_choice'] = selected_choice.id
            http_session.save()
            selected_choice.votes += 1
            selected_choice.save()
            Group("poll").send({"text": json.dumps({"poll_update": question.ordered_list_choices()}), })
            message.reply_channel.send({"text": json.dumps({"vote_confirm": True}), })
        # when not one vote only all votes are counted
        elif not question.one_vote_only:
            selected_choice.votes += 1
            selected_choice.save()
            Group("poll").send({"text": json.dumps({"poll_update": question.ordered_list_choices()}), })

    # the undo key is intended for when one vote only allowed
    # to safe guard against accidental choices or changes of mind
    elif 'undo' in data:
        if question.one_vote_only == True and http_session.get('has_voted') == True:
            selected_choice = question.choice_set.get(pk=http_session['vote_choice'])
            assert isinstance(selected_choice, Choice), "choice does not exist"

            http_session['has_voted'] = False
            http_session['vote_choice'] = None
            http_session.save()
            selected_choice.votes -= 1
            selected_choice.save()
            Group("poll").send({"text": json.dumps({"poll_update": question.ordered_list_choices()}), })
            message.reply_channel.send({"text": json.dumps({"undo_confirm": True}), })


# Connected to websocket.disconnect
def ws_disconnect(message):
    Group("poll").discard(message.reply_channel)
