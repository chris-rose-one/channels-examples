import json
from django.shortcuts import render
from django.template import loader

from .models import get_active_poll

# page request
def poll(request):
    question = get_active_poll()
    if question:
        # set the users session variables and return poll data
        if not question.id == request.session.get('loaded_question'):
            request.session['loaded_question'] = question.id
            request.session['has_voted'] = False
        request.session['poll_status'] = question.is_open()
        request.session.set_expiry(question.seconds_remaining() + 3600)
        return render(request, 'polls/poll.html', {
            'question': question,
            'choices': json.dumps(question.ordered_list_choices()),
            'has_voted': request.session['has_voted']
        })
    else:
        # set the user session variables and return an error message
        # the session variables are important for the fluidpoll management command
        request.session['loaded_question'] = None
        request.session['poll_status'] = None
        return render(request, 'polls/poll.html', {
            'error_message': "There isn't a poll running at the moment!"})
