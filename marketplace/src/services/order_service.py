# src/services/order_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from src.models import (
    Order, OrderItem, Product, PromoCode, UserOperation,
    OrderStatusEnum, ProductStatusEnum, User
)
from src.core.exceptions import create_error
from src.config import settings


class OrderService:
    def __init__(self, db, current_user):
        self.db = db
        self.user = current_user

    def _check_rate_limit(self, op_type):
        last_op = self.db.query(UserOperation).filter(
            UserOperation.user_id == self.user.id,
            UserOperation.operation_type == op_type
        ).order_by(UserOperation.created_at.desc()).first()
        
        if last_op:
            delta = datetime.utcnow() - last_op.created_at
            if delta < timedelta(minutes=settings.RATE_LIMIT_MINUTES):
                raise create_error("ORDER_LIMIT_EXCEEDED")

    def _check_active_orders(self):
        active = self.db.query(Order).filter(
            Order.user_id == self.user.id,
            Order.status.in_([OrderStatusEnum.CREATED, OrderStatusEnum.PAYMENT_PENDING])
        ).first()
        if active:
            raise create_error("ORDER_HAS_ACTIVE")

    def _validate_and_lock_products(self, items_data):
        products = []
        insufficient = []
        
        for item in items_data:
            prod = self.db.query(Product).filter(
                Product.id == item['product_id']
            ).with_for_update().first()
            
            if not prod:
                raise create_error("PRODUCT_NOT_FOUND", details={"product_id": item['product_id']})
            if prod.status != ProductStatusEnum.ACTIVE:
                raise create_error("PRODUCT_INACTIVE", details={"product_id": item['product_id']})
            if prod.stock < item['quantity']:
                insufficient.append({
                    "product_id": item['product_id'],
                    "requested": item['quantity'],
                    "available": prod.stock
                })
            products.append(prod)
        
        if insufficient:
            raise create_error("INSUFFICIENT_STOCK", details={"items": insufficient})
        
        return products

    def _calculate_total(self, items_data, products):
        total = 0.0
        for i, item in enumerate(items_data):
            total += float(products[i].price) * item['quantity']
        return total

    def _apply_promo(self, total, promo_code):
        if not promo_code:
            return total, 0.0, None
        
        promo = self.db.query(PromoCode).filter(
            PromoCode.code == promo_code
        ).with_for_update().first()
        
        if not promo or not promo.active:
            raise create_error("PROMO_CODE_INVALID")
        if promo.current_uses >= promo.max_uses:
            raise create_error("PROMO_CODE_INVALID")
        if promo.valid_from and datetime.utcnow() < promo.valid_from:
            raise create_error("PROMO_CODE_INVALID")
        if promo.valid_until and datetime.utcnow() > promo.valid_until:
            raise create_error("PROMO_CODE_INVALID")
        if total < float(promo.min_order_amount):
            raise create_error("PROMO_CODE_MIN_AMOUNT")
        
        discount = 0.0
        if promo.discount_type == 'PERCENTAGE':
            discount = total * float(promo.discount_value) / 100
            if discount > total * 0.7:
                discount = total * 0.7
        else:
            discount = min(float(promo.discount_value), total)
        
        promo.current_uses += 1
        
        return total - discount, discount, promo

    def _log_operation(self, op_type):
        op = UserOperation(
            user_id=self.user.id,
            operation_type=op_type
        )
        self.db.add(op)

    def create_order(self, items_data, promo_code_str=None):
        # 1. Сначала проверка активных заказов (быстрая)
        self._check_active_orders()
        
        # 2. Проверка товаров и остатков (без блокировки)
        products = self._validate_and_lock_products(items_data)
        
        # 3. Расчет стоимости
        total = self._calculate_total(items_data, products)
        
        # 4. Применение промокода
        final_total, discount, promo = self._apply_promo(total, promo_code_str)
        
        # 5. ТОЛЬКО ТЕПЕРЬ rate limit (перед фиксацией!)
        self._check_rate_limit("CREATE_ORDER")
        
        # 6. Резервирование остатков (в транзакции)
        for i, item in enumerate(items_data):
            products[i].stock -= item['quantity']
        
        # 7. Создание заказа
        order = Order(
            user_id=self.user.id,
            status=OrderStatusEnum.CREATED,
            total_amount=final_total,
            discount_amount=discount,
            promo_code_id=promo.id if promo else None
        )
        self.db.add(order)
        self.db.flush()
        
        # 8. Позиции заказа
        for i, item in enumerate(items_data):
            order_item = OrderItem(
                order_id=order.id,
                product_id=products[i].id,
                quantity=item['quantity'],
                price_at_order=products[i].price
            )
            self.db.add(order_item)
        
        # 9. Лог операции
        self._log_operation("CREATE_ORDER")
        
        self.db.commit()
        self.db.refresh(order)
        return order

    def update_order(self, order_id, items_data):
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise create_error("ORDER_NOT_FOUND")
        
        if order.user_id != self.user.id and self.user.role.value != "ADMIN":
            raise create_error("ORDER_OWNERSHIP_VIOLATION")
        
        if order.status != OrderStatusEnum.CREATED:
            raise create_error("INVALID_STATE_TRANSITION")
        
        self._check_rate_limit("UPDATE_ORDER")
        
        for item in order.items:
            prod = self.db.query(Product).filter(
                Product.id == item.product_id
            ).with_for_update().first()
            if prod:
                prod.stock += item.quantity
        
        products = self._validate_and_lock_products(items_data)
        for i, item in enumerate(items_data):
            products[i].stock -= item['quantity']
        
        total = self._calculate_total(items_data, products)
        
        if order.promo_code_id:
            promo = self.db.query(PromoCode).filter(
                PromoCode.id == order.promo_code_id
            ).with_for_update().first()
            
            if promo and total >= float(promo.min_order_amount):
                if promo.discount_type == 'PERCENTAGE':
                    discount = total * float(promo.discount_value) / 100
                    if discount > total * 0.7:
                        discount = total * 0.7
                else:
                    discount = min(float(promo.discount_value), total)
                order.discount_amount = discount
                order.total_amount = total - discount
            else:
                if promo:
                    promo.current_uses -= 1
                order.promo_code_id = None
                order.discount_amount = 0
                order.total_amount = total
        else:
            order.total_amount = total
        
        self.db.query(OrderItem).filter(
            OrderItem.order_id == order.id
        ).delete()
        
        for i, item in enumerate(items_data):
            order_item = OrderItem(
                order_id=order.id,
                product_id=products[i].id,
                quantity=item['quantity'],
                price_at_order=products[i].price
            )
            self.db.add(order_item)
        
        self._log_operation("UPDATE_ORDER")
        
        self.db.commit()
        self.db.refresh(order)
        return order

    def cancel_order(self, order_id):
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise create_error("ORDER_NOT_FOUND")
        
        if order.user_id != self.user.id and self.user.role.value != "ADMIN":
            raise create_error("ORDER_OWNERSHIP_VIOLATION")
        
        if order.status not in [OrderStatusEnum.CREATED, OrderStatusEnum.PAYMENT_PENDING]:
            raise create_error("INVALID_STATE_TRANSITION")
        
        for item in order.items:
            prod = self.db.query(Product).filter(
                Product.id == item.product_id
            ).with_for_update().first()
            if prod:
                prod.stock += item.quantity
        
        if order.promo_code_id:
            promo = self.db.query(PromoCode).filter(
                PromoCode.id == order.promo_code_id
            ).with_for_update().first()
            if promo and promo.current_uses > 0:
                promo.current_uses -= 1
        
        order.status = OrderStatusEnum.CANCELED
        
        self.db.commit()
        self.db.refresh(order)
        return order