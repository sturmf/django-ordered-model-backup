from django.db import models
from ordered_model.models import OrderedModel


class Item(OrderedModel):
    name = models.CharField(max_length=100)


class Question(models.Model):
    pass


class Answer(OrderedModel):
    question = models.ForeignKey(Question, related_name='answers')
    order_with_respect_to = 'question'

    class Meta:
        ordering = ('question', 'order')

    def __unicode__(self):
        return u"Answer #%d of question #%d" % (self.order, self.question_id)


class Topping(models.Model):
    name = models.CharField(max_length=100)


class Pizza(models.Model):
    name = models.CharField(max_length=100)
    toppings = models.ManyToManyField(Topping, through='PizzaToppingsThroughModel')


class PizzaToppingsThroughModel(OrderedModel):
    pizza = models.ForeignKey(Pizza)
    topping = models.ForeignKey(Topping)
    order_with_respect_to = 'pizza'

    class Meta:
        ordering = ('pizza', 'order')