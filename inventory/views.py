from decimal import Decimal, InvalidOperation

from django.db.models import Q, F
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Category, Item, Store, Stock, StockMovement, StockCount, StockCountItem
from .serializers import (
    CategorySerializer, ItemSerializer, StoreSerializer,
    StockSerializer, StockMovementSerializer,
    StockCountSerializer, StockCountItemSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class


class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]
    pagination_class = None

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        parent = self.request.query_params.get('parent', None)

        if parent:
            if parent == 'root':
                queryset = queryset.filter(parent_category__isnull=True)
            else:
                queryset = queryset.filter(parent_category_id=parent)

        return queryset


class CategoryDetailView(generics.RetrieveUpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [make_permission_class('INVENTORY_MANAGE')]


class ItemListView(generics.ListCreateAPIView):
    queryset = Item.objects.filter(is_active=True)
    serializer_class = ItemSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]
    pagination_class = None

    def get_queryset(self):
        queryset = Item.objects.filter(is_active=True)
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        item_type = self.request.query_params.get('type', None)
        medication = self.request.query_params.get('medication', None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        if category:
            queryset = queryset.filter(category_id=category)

        if item_type:
            if item_type == 'medication':
                queryset = queryset.filter(is_medication=True)
            elif item_type == 'consumable':
                queryset = queryset.filter(is_consumable=True)
            elif item_type == 'equipment':
                queryset = queryset.filter(is_equipment=True)

        if medication:
            queryset = queryset.filter(medication_id=medication)

        return queryset


class ItemDetailView(generics.RetrieveUpdateAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [make_permission_class('INVENTORY_MANAGE')]


class StoreListView(generics.ListCreateAPIView):
    queryset = Store.objects.filter(is_active=True)
    serializer_class = StoreSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]
    pagination_class = None


class StoreDetailView(generics.RetrieveUpdateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [make_permission_class('INVENTORY_MANAGE')]


class StockListView(generics.ListAPIView):
    serializer_class = StockSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]

    def get_queryset(self):
        queryset = Stock.objects.filter(item__is_active=True)
        store = self.request.query_params.get('store', None)
        item = self.request.query_params.get('item', None)

        if store:
            queryset = queryset.filter(store_id=store)
        if item:
            queryset = queryset.filter(item_id=item)

        return queryset


class StockDetailView(generics.RetrieveUpdateAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [make_permission_class('INVENTORY_MANAGE')]


class StockMovementListView(generics.ListAPIView):
    serializer_class = StockMovementSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]

    def get_queryset(self):
        queryset = StockMovement.objects.all()
        item = self.request.query_params.get('item', None)
        store = self.request.query_params.get('store', None)
        movement_type = self.request.query_params.get('type', None)

        if item:
            queryset = queryset.filter(item_id=item)
        if store:
            queryset = queryset.filter(store_id=store)
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)

        return queryset


class StockMovementDetailView(generics.RetrieveAPIView):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('STOCK_MOVE')])
def receive_stock(request):
    from decimal import InvalidOperation
    from django.db import transaction

    item_id = request.data.get('item_id')
    store_id = request.data.get('store_id')
    quantity = request.data.get('quantity')
    batch_lot_number = request.data.get('batch_lot_number', '')
    expiry_date = request.data.get('expiry_date', None)
    unit_cost = request.data.get('unit_cost', None)
    notes = request.data.get('notes', '')

    if not item_id or not store_id or not quantity:
        return Response(
            {'error': 'item_id, store_id, and quantity required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantity = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    if unit_cost:
        try:
            unit_cost = Decimal(str(unit_cost))
        except (InvalidOperation, TypeError, ValueError):
            return Response({'error': 'Invalid unit cost'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        item = Item.objects.get(id=item_id)
        store = Store.objects.get(id=store_id)
    except (Item.DoesNotExist, Store.DoesNotExist):
        return Response({'error': 'Item or Store not found'}, status=status.HTTP_404_NOT_FOUND)

    # Atomic stock update with select_for_update to prevent race conditions
    with transaction.atomic():
        stock, created = Stock.objects.select_for_update().get_or_create(
            item=item,
            store=store,
            batch_lot_number=batch_lot_number,
            defaults={
                'expiry_date': expiry_date,
                'quantity_on_hand': quantity,
                'unit_cost': unit_cost
            }
        )

        if not created:
            stock.quantity_on_hand += quantity
            if unit_cost:
                stock.unit_cost = unit_cost
            if expiry_date:
                stock.expiry_date = expiry_date
            stock.last_received_date = timezone.now().date()
            stock.save()

    # Create movement record
    movement = StockMovement.objects.create(
        item=item,
        store=store,
        movement_type='receipt',
        quantity=quantity,
        unit_cost=unit_cost,
        total_cost=quantity * unit_cost if unit_cost else None,
        batch_lot_number=batch_lot_number,
        expiry_date=expiry_date,
        notes=notes or f'GRN - Goods Received',
        performed_by=request.user if request.user.is_authenticated else None
    )

    return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('STOCK_MOVE')])
def issue_stock(request):
    from decimal import InvalidOperation
    from django.db import transaction

    item_id = request.data.get('item_id')
    store_id = request.data.get('store_id')
    quantity = request.data.get('quantity')
    batch_lot_number = request.data.get('batch_lot_number', '')
    reference_type = request.data.get('reference_type', None)
    reference_id = request.data.get('reference_id', None)

    if not item_id or not store_id or not quantity:
        return Response(
            {'error': 'item_id, store_id, and quantity required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantity = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    # Atomic stock deduction with select_for_update to prevent race conditions
    with transaction.atomic():
        try:
            stock = Stock.objects.select_for_update().get(
                item_id=item_id,
                store_id=store_id,
                batch_lot_number=batch_lot_number
            )
        except Stock.DoesNotExist:
            return Response({'error': 'Stock not found'}, status=status.HTTP_404_NOT_FOUND)

        if stock.quantity_on_hand < quantity:
            return Response(
                {'error': f'Insufficient stock. Available: {stock.quantity_on_hand}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stock.quantity_on_hand -= quantity
        stock.last_issued_date = timezone.now().date()
        stock.save()

    # Create movement record
    movement = StockMovement.objects.create(
        item=stock.item,
        store=stock.store,
        movement_type='issue',
        quantity=quantity,
        unit_cost=stock.unit_cost,
        total_cost=quantity * stock.unit_cost if stock.unit_cost else None,
        batch_lot_number=batch_lot_number,
        reference_type=reference_type,
        reference_id=reference_id,
        performed_by=request.user if request.user.is_authenticated else None
    )

    return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('STOCK_MOVE')])
def transfer_stock(request):
    from decimal import InvalidOperation
    from django.db import transaction

    item_id = request.data.get('item_id')
    from_store_id = request.data.get('from_store_id')
    to_store_id = request.data.get('to_store_id')
    quantity = request.data.get('quantity')
    batch_lot_number = request.data.get('batch_lot_number', '')

    if not item_id or not from_store_id or not to_store_id or not quantity:
        return Response(
            {'error': 'item_id, from_store_id, to_store_id, and quantity required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantity = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

    if quantity <= 0:
        return Response({'error': 'Quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    if from_store_id == to_store_id:
        return Response(
            {'error': 'Cannot transfer to the same store'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Atomic transfer with select_for_update on source stock
    with transaction.atomic():
        try:
            from_stock = Stock.objects.select_for_update().filter(
                item_id=item_id,
                store_id=from_store_id,
            ).order_by('expiry_date', 'created_at').first()
            if not from_stock:
                raise Stock.DoesNotExist
            to_store = Store.objects.get(id=to_store_id)
        except (Stock.DoesNotExist, Store.DoesNotExist):
            return Response({'error': 'Stock or Store not found'}, status=status.HTTP_404_NOT_FOUND)

        if from_stock.quantity_on_hand < quantity:
            return Response(
                {'error': f'Insufficient stock. Available: {from_stock.quantity_on_hand}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from_stock.quantity_on_hand -= quantity
        from_stock.save()

        to_stock, created = Stock.objects.select_for_update().get_or_create(
            item=from_stock.item,
            store=to_store,
            batch_lot_number=batch_lot_number,
            defaults={
                'expiry_date': from_stock.expiry_date,
                'quantity_on_hand': quantity,
                'unit_cost': from_stock.unit_cost
            }
        )

        if not created:
            to_stock.quantity_on_hand += quantity
            to_stock.save()

    # Create movement record
    movement = StockMovement.objects.create(
        item=from_stock.item,
        store=from_stock.store,
        movement_type='transfer',
        quantity=quantity,
        unit_cost=from_stock.unit_cost,
        total_cost=quantity * from_stock.unit_cost if from_stock.unit_cost else None,
        batch_lot_number=batch_lot_number,
        from_store=from_stock.store,
        to_store=to_store,
        performed_by=request.user if request.user.is_authenticated else None
    )

    return Response(StockMovementSerializer(movement).data, status=status.HTTP_201_CREATED)


class StockCountListView(generics.ListCreateAPIView):
    serializer_class = StockCountSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]

    def get_queryset(self):
        queryset = StockCount.objects.all()
        store = self.request.query_params.get('store', None)

        if store:
            queryset = queryset.filter(store_id=store)

        return queryset


class StockCountDetailView(generics.RetrieveUpdateAPIView):
    queryset = StockCount.objects.all()
    serializer_class = StockCountSerializer
    permission_classes = [make_permission_class('INVENTORY_MANAGE')]


class StockCountItemListView(generics.ListCreateAPIView):
    serializer_class = StockCountItemSerializer
    permission_classes = [make_permission_class('INVENTORY_VIEW')]

    def get_queryset(self):
        return StockCountItem.objects.filter(stock_count_id=self.kwargs['count_id'])


@api_view(['GET'])
@permission_classes([make_permission_class('INVENTORY_VIEW')])
def low_stock_items(request):
    store_id = request.query_params.get('store', None)

    queryset = Stock.objects.filter(
        item__is_active=True,
        item__reorder_level__gt=0
    ).filter(
        quantity_on_hand__lte=F('item__reorder_level')
    ).select_related('item', 'store')

    if store_id:
        queryset = queryset.filter(store_id=store_id)

    results = []
    for stock in queryset:
        results.append({
            'item_id': str(stock.item.id),
            'item_name': stock.item.name,
            'item_code': stock.item.code,
            'store_id': str(stock.store.id),
            'store_name': stock.store.name,
            'quantity_on_hand': stock.quantity_on_hand,
            'reorder_level': stock.item.reorder_level,
            'status': 'OUT_OF_STOCK' if stock.quantity_on_hand <= 0 else 'LOW_STOCK'
        })

    return Response(results)


@api_view(['GET'])
@permission_classes([make_permission_class('INVENTORY_VIEW')])
def expiring_items(request):
    try:
        days = int(request.query_params.get('days', 90))
    except (TypeError, ValueError):
        return Response({'error': 'days must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

    if days < 1 or days > 365:
        return Response({'error': 'days must be between 1 and 365'}, status=status.HTTP_400_BAD_REQUEST)

    store_id = request.query_params.get('store', None)

    from datetime import timedelta
    expiry_threshold = timezone.now().date() + timedelta(days=days)

    queryset = Stock.objects.filter(
        item__is_active=True,
        expiry_date__isnull=False,
        expiry_date__lte=expiry_threshold,
        quantity_on_hand__gt=0
    ).select_related('item', 'store')

    if store_id:
        queryset = queryset.filter(store_id=store_id)

    results = []
    for stock in queryset:
        results.append({
            'item_id': str(stock.item.id),
            'item_name': stock.item.name,
            'item_code': stock.item.code,
            'batch_lot_number': stock.batch_lot_number,
            'expiry_date': stock.expiry_date,
            'quantity_on_hand': stock.quantity_on_hand,
            'store_name': stock.store.name,
            'days_until_expiry': (stock.expiry_date - timezone.now().date()).days
        })

    return Response(results)


@api_view(['GET'])
@permission_classes([make_permission_class('INVENTORY_VIEW')])
def stock_summary(request):
    from django.db.models import Sum, Count

    store_id = request.query_params.get('store')
    category_id = request.query_params.get('category')

    queryset = Stock.objects.filter(item__is_active=True, quantity_on_hand__gt=0).select_related('item', 'store')

    if store_id:
        queryset = queryset.filter(store_id=store_id)
    if category_id:
        queryset = queryset.filter(item__category_id=category_id)

    total_items = queryset.count()
    total_units = queryset.aggregate(total=Sum('quantity_on_hand'))['total'] or 0
    total_value = queryset.aggregate(total=Sum(F('quantity_on_hand') * F('unit_cost')))['total'] or 0

    low_stock_count = queryset.filter(
        quantity_on_hand__lte=F('item__reorder_level'),
        item__reorder_level__gt=0
    ).count()

    return Response({
        'total_stock_lines': total_items,
        'total_units': total_units,
        'total_value': str(total_value),
        'low_stock_items': low_stock_count,
    })
