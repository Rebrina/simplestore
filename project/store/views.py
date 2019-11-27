from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, ListView, DetailView, CreateView
from django import forms
#from django.http import HttpResponseRedirect


from .forms import ReviewForm
from .models import Category, Section, Product, Review, Article, Order, OrderLine, User


def add_to_cart(request):
    if 'add_to_cart' in request.POST:
        request.session.setdefault('just_store_cart', {})
        product_id = request.POST['add_to_cart']
        if product_id in request.session['just_store_cart']:
            request.session['just_store_cart'][product_id] = request.session['just_store_cart'][product_id] + 1
        else:
            request.session['just_store_cart'][product_id] = 1
        request.session.modified = True


class MenuMixin:
    @staticmethod
    def add_menu_data(context, session):
        context['categories'] = Category.objects.all()
        context['sections'] = Section.objects.all()
        if 'just_store_cart' in session:
            context['items_in_cart'] = sum(session['just_store_cart'].values())
        return context


class IndexView(TemplateView, MenuMixin):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_menu_data(context, self.request.session)
        context['articles'] = Article.objects.all().prefetch_related('products')
        return context

    def post(self, request, *args, **kwargs):
        add_to_cart(request)
        return super().get(self, request, *args, **kwargs)


class StoreLoginView(TemplateView):
    template_name = 'login.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        guests = User.objects.filter(email=request.POST['username'])
        if not guests.exists():
            context['login_error'] = 'Пользователя с указанной почтой и паролем не найдено'
            return self.render_to_response(context)
        if len(guests) > 1:
            context['login_error'] = 'Обнаружено несколько пользователей с указанной почтой'
            return self.render_to_response(context)
        guest = guests.first()
        user = authenticate(request, username=guest.username, password=request.POST['password'])
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        context['login_error'] = 'Пользователя с указанной почтой и паролем не найдено'
        return self.render_to_response(context)


class StoreLogoutView(LogoutView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['articles'] = Article.objects.all().prefetch_related('products')
        return context


class SectionView(ListView, MenuMixin):
    template_name = 'section.html'
    model = Product
    paginate_by = 1

    def get_queryset(self):
        return Product.objects.filter(section=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_menu_data(context, self.request.session)
        context['current_section'] = Section.objects.get(pk=self.kwargs['pk'])
        return context

    def post(self, request, *args, **kwargs):
        add_to_cart(request)
        return super().get(self, request, *args, **kwargs)


class ProductView(DetailView, MenuMixin, CreateView):
    template_name = 'product.html'
    model = Product
    context_object_name = 'product'
    form_class = ReviewForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_menu_data(context, self.request.session)
        form = ReviewForm(initial={ 'product': self.object })
        form.fields['product'].widget = forms.HiddenInput()
        context['form'] = form 
        return context
        
    def post(self, request, *args, **kwargs):
        add_to_cart(request)
        CreateView.post(self, request, *args, **kwargs)
        #return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        return super().get(self, request, *args, **kwargs)


class CartView(TemplateView, MenuMixin):
    template_name = 'cart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_menu_data(context, self.request.session)
        context['products'] = Product.objects.all()
        if 'just_store_cart' in self.request.session:
            context['cart'] = {}
            for product_id, quantity in self.request.session['just_store_cart'].items():
                product = Product.objects.get(id=product_id)
                context['cart'][product] = quantity
        return context

    def post(self, request, *args, **kwargs):
        request.session.setdefault('new_order', False)
        request.session['new_order'] = True
        order = Order(user=request.user)
        order.save()
        products = []
        for product_id, quantity in self.request.session['just_store_cart'].items():
            product = Product.objects.get(id=product_id)
            order_line = OrderLine(product=product, quantity=quantity)
            order_line.save()
            products.append(order_line)
        order.products.set(products)
        order.save()
        self.request.session['just_store_cart'].clear()
        return HttpResponseRedirect(reverse('order'))


class OrderView(ListView, MenuMixin):
    template_name = 'order.html'
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_menu_data(context, self.request.session)
        if self.request.user.is_authenticated:
            self.request.session.setdefault('new_order', False)
            if self.request.session['new_order']:
                context['is_new_order'] = True
                self.request.session['new_order'] = False
            context['orders'] = Order.objects.filter(user=self.request.user).prefetch_related('products').order_by("-pk")
        context['show_money_count'] = self.request.user.show_money_count
        return context