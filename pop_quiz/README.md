# Pop Quiz
## Description
This is a polling app with a dynamically created and updated bar graph as representation and a status panel to guide you every step of the way.
It leverages the batteries included in the <a href="https://www.djangoproject.com">Django</a> web framework to build a database backend and provide a CRUD (create, read, update, delete) administration system.

The real work horse of the application is <a href="https://channels.readthedocs.io">Django Channels</a>, in particular the websocket capabilities that they bring.
After the http page request and response is complete, messages between the server and client of poll updates,
vote choices or changes of mind are sent via websockets as an event requires them to be.<br/>
Essentially providing the bones of a live multi-user poll.

The bar graph is rendered using a javascript library <a href="https://d3js.org">d3.js</a> (data driven documentation)

The poll has two different modes<br/>
<ol>
<li>free for all, unlimited votes &#42;<br/></li>
<li>one vote only &#42;<br/></li>
&#42; until a choice caps or voting closes.
</ol>

Polls are created using the Django admin interface, here you may set the following parameters:
- question text
- starting time
	- will always round down to a second past the minute
	- to avoid poll time conflict a second will be shaved from the end time property
- running time (voting period)
- remain active (for end result viewing)
- one vote only mode checkbox (enough said)
	- although, it does incorporate an undo button for the chance of mind changers.
- vote limit
	- this applies to the max votes any one choice may receive. not the overall poll
- and then there are the choices of answers
	- 4-5 choices fit nicely in free for all mode&#42;&#42;
	- 3-4 choices fit with the undo button, when in one vote only mode &#42;&#42;<br/>
    &#42;&#42; tends to be the lesser when scaled up to a PC screen.

It is possible to queue up a number of polls ahead of time. A pre save signal wont allow poll times to overlap

A server side session store keeps poll users honest.

Repository settings are configured for local deployment and using two main processes
- Daphne http/websocket server
- Django worker

It requires the support of
- Redis

As time elapses, polls go through a series of changes; polls close, they end and new ones begin.
these changes rely on time fields within the model and a third process to assess if one has come to pass before messaging these changes in state to clients.
It is required to automate transitions in the queue but this process is optional.
- fluidpoll management command

### Manual Installation Local
Make a new vitualenv for the project, and run:</br>
- pip install -r requirements.txt</br>
- python manage.py makemigrations polls</br>
- python manage.py migrate

### Usage
Make yourself a super user account:</br>
- python manage.py createsuperuser
Then, login to http//localhost:8000/admin and create a few poll Questions

run at least the worker and web processes found in the Procfile, or python manage.py runserver</br>
run a fluidpoll process found in the Procfile to give the users real time updates on poll state
