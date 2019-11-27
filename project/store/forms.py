from django import forms
from .models import Review

CHOICES=(('1','1'),
         ('2','2'),
         ('3','3'),
         ('4','4'),
         ('5','5'))


class ReviewForm(forms.ModelForm):
    name= forms.CharField(widget= forms.TextInput(attrs={
        'id': 'name',
        'aria-describedby': 'nameHelp',
        'placeholder': 'Введите ваше имя',
        'data-cip-id': 'name'}
    ), label='Имя', label_suffix='')
    description = forms.CharField(widget= forms.Textarea(attrs={
        'id': 'content',
        'placeholder': 'Введите отзыв',
        'rows': 3}
    ), label='Содержание', label_suffix='')
    mark = forms.TypedChoiceField(
        widget=forms.RadioSelect,
        label='Оценка',
        choices=((1, '1',), (2, '2',), (3, '3',), (4, '4',), (5, '5',))
    )

    class Meta(object):
        model = Review
        exclude = ('id', 'published_at')