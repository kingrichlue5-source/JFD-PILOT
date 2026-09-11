from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<uuid:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Items
    path('items/', views.ItemListView.as_view(), name='item-list'),
    path('items/<uuid:pk>/', views.ItemDetailView.as_view(), name='item-detail'),

    # Stores
    path('stores/', views.StoreListView.as_view(), name='store-list'),
    path('stores/<uuid:pk>/', views.StoreDetailView.as_view(), name='store-detail'),

    # Stock
    path('stock/', views.StockListView.as_view(), name='stock-list'),
    path('stock/<uuid:pk>/', views.StockDetailView.as_view(), name='stock-detail'),

    # Stock Movements
    path('movements/', views.StockMovementListView.as_view(), name='movement-list'),
    path('movements/<uuid:pk>/', views.StockMovementDetailView.as_view(), name='movement-detail'),
    path('receive/', views.receive_stock, name='receive-stock'),
    path('issue/', views.issue_stock, name='issue-stock'),
    path('transfer/', views.transfer_stock, name='transfer-stock'),

    # Stock Counts
    path('counts/', views.StockCountListView.as_view(), name='count-list'),
    path('counts/<uuid:pk>/', views.StockCountDetailView.as_view(), name='count-detail'),
    path('counts/<uuid:count_id>/items/', views.StockCountItemListView.as_view(), name='count-item-list'),

    # Reports
    path('low-stock/', views.low_stock_items, name='low-stock'),
    path('expiring/', views.expiring_items, name='expiring'),
    path('stock-summary/', views.stock_summary, name='stock-summary'),
]
