from sqlalchemy.orm import Session

from src.models import Product, ProductStatusEnum, User
from src.core.exceptions import create_error


class ProductService:
    def __init__(self, db, current_user):
        self.db = db
        self.user = current_user

    def list_products(self, page=0, size=20, status_filter=None, category=None):
        query = self.db.query(Product)
        
        if status_filter:
            query = query.filter(Product.status == status_filter)
        if category:
            query = query.filter(Product.category == category)
        
        total = query.count()
        items = query.offset(page * size).limit(size).all()
        
        return {
            "items": items,
            "totalElements": total,
            "page": page,
            "size": size
        }

    def get_product(self, product_id):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise create_error("PRODUCT_NOT_FOUND")
        return product

    def create_product(self, product_data, seller_id=None):
        if not product_data.get("name") or len(product_data["name"]) > 255:
            raise create_error("VALIDATION_ERROR", details={"name": "1-255 chars required"})
        if product_data.get("price", 0) <= 0:
            raise create_error("VALIDATION_ERROR", details={"price": "must be > 0"})
        if product_data.get("stock", -1) < 0:
            raise create_error("VALIDATION_ERROR", details={"stock": "must be >= 0"})
        
        new_product = Product(
            name=product_data["name"],
            description=product_data.get("description"),
            price=product_data["price"],
            stock=product_data["stock"],
            category=product_data["category"],
            status=ProductStatusEnum[product_data.get("status", "ACTIVE")],
            seller_id=seller_id
        )
        
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        
        return new_product

    def update_product(self, product_id, product_data, seller_id=None):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise create_error("PRODUCT_NOT_FOUND")
        
        if seller_id and product.seller_id != seller_id:
            raise create_error("ACCESS_DENIED")
        
        for field in ["name", "description", "price", "stock", "category", "status"]:
            if field in product_data:
                value = product_data[field]
                if field == "status":
                    value = ProductStatusEnum[value]
                setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product

    def soft_delete_product(self, product_id, seller_id=None):
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise create_error("PRODUCT_NOT_FOUND")
        
        if seller_id and product.seller_id != seller_id:
            raise create_error("ACCESS_DENIED")
        
        product.status = ProductStatusEnum.ARCHIVED
        self.db.commit()
        
        return product
