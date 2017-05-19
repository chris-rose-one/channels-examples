import datetime
from django.db import models
from django.utils import timezone
from django.core import serializers

# find an active poll, only one is expected
def get_active_poll():
    for question in Question.objects.all():
        if question.is_active(): return question
    else:
        return None

# used to round down start time to a second past the minute
def time_rounded_down(dt=None):
    if dt == None:
        dt = timezone.now()
    return dt + datetime.timedelta(seconds=-dt.second + 1, microseconds=-dt.microsecond)

# the poll question model
class Question(models.Model):
    question_text = models.CharField(max_length=200) # poll title
    starting_time = models.DateTimeField('start time', default=time_rounded_down) # start time
    running_time = models.IntegerField(default=15) # how long the poll is open for voting
    remain_active = models.IntegerField(default=5) # how long the poll is available for viewing after poll closure
    one_vote_only = models.BooleanField(default=False) # check box one vote only functionality
    vote_limit = models.IntegerField(default=150) # vote limit per choice not overall

    class Meta:
        ordering = ('starting_time',) # descending, admin

    def __str__(self):
        return self.question_text

    def get_end_time(self):
        return self.starting_time + datetime.timedelta(minutes=(self.running_time + self.remain_active), seconds=-1)
    # end time property for admin question list
    end_time = property(get_end_time)

    # check if the poll is open for viewing
    def is_active(self):
        if self.starting_time <= timezone.now() <= self.get_end_time():
            return True
        else:
            return False

    # check if the poll is open for voting
    def is_open(self):
        if self.starting_time <= timezone.now() <= (self.starting_time + datetime.timedelta(minutes=self.running_time)):
            for choice in self.choice_set.all():
                if choice.votes == self.vote_limit: return False
            else:
                return True

    # calculate how many seconds remain until the poll closes
    def seconds_remaining(self):
        diff = (self.starting_time + datetime.timedelta(minutes=self.running_time)) - timezone.now()
        return diff.total_seconds()

    # postgresql returns unordered data. this enoforces order of poll choice data
    def ordered_list_choices(self):
        data = []
        for choice in self.choice_set.order_by('id'):
            data.append({'id': choice.id, 'choice_text': choice.choice_text, 'votes': choice.votes})
        return data

# poll choice model
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    def __str__(self):
        return self.choice_text
