import datetime
from django.contrib import admin, messages
from .models import Choice, Question

# will display each choice on its own line
class ChoiceInline(admin.TabularInline):
    model = Choice

    # aiming to display only 3 choices in the admin until specifically adding another choice
    def get_extra(self, request, obj=None, **kwargs):
        extra = 3
        if obj and obj.choice_set.count() > extra:
            return 0
        elif obj:
            return extra - obj.choice_set.count()
        return extra

# specify the parameters of the questions admin
class QuestionAdmin(admin.ModelAdmin):
    # question objects fieldset
    fieldsets = [
        (None, {'fields': ['question_text', 'starting_time', 'running_time', 'remain_active', 'vote_limit',
                           'one_vote_only']}),
    ]
    # add choices to the display
    inlines = [ChoiceInline]
    # when viewing question list show these parameters
    list_display = ('question_text', 'starting_time', 'running_time', 'remain_active', 'end_time')
    # attemp to save model or catch error and display as message
    def save_model(self, request, *args, **kwargs):
        try:
            return super(QuestionAdmin, self).save_model(request, *args, **kwargs)
        except Exception as e:
            messages.set_level(request, messages.ERROR)
            self.message_user(request, e, messages.ERROR)

# register question in the admin
admin.site.register(Question, QuestionAdmin)
