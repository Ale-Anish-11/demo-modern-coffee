from django import forms
from products.models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'name', 'description', 'price',
            'image', 'image_url', 'stock', 'available',
            'rating', 'reviews_count', 'is_featured', 'is_popular',
            'calories', 'brew_time'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'placeholder': 'e.g. Vanilla Hazelnut Latte'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'rows': 3, 'placeholder': 'Describe aroma, roast, tasting notes...'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white'}),
            'image_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'placeholder': 'https://images.unsplash.com/...'}),
            'rating': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'step': '0.1'}),
            'reviews_count': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white'}),
            'calories': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white'}),
            'brew_time': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'placeholder': 'e.g. 3-4 mins'}),
            'available': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded text-amber-700 focus:ring-amber-500 border-stone-300'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded text-amber-700 focus:ring-amber-500 border-stone-300'}),
            'is_popular': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded text-amber-700 focus:ring-amber-500 border-stone-300'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'rows': 2}),
            'icon': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 rounded-xl border border-stone-300 focus:border-amber-700 focus:ring-2 focus:ring-amber-200 outline-none text-stone-800 bg-white', 'placeholder': 'fa-coffee'}),
        }
