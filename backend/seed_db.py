from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import uuid

def seed_database():
    db = SessionLocal()
    try:
        # Clear existing data for a clean seed
        print("Clearing existing data...")
        db.query(models.Notification).delete()
        db.query(models.OrderItem).delete()
        db.query(models.Order).delete()
        db.query(models.MenuItem).delete()
        db.query(models.RestaurantTable).delete()
        db.query(models.User).delete()
        db.query(models.Restaurant).delete()
        db.commit()

        # Create SysAdmin
        print("Creating SysAdmin...")
        sysadmin = models.User(
            id="5c230f7b-2390-4e5e-9e4f-ab408201ff71",
            name="Super Admin",
            username="sysadmin",
            email="sysadmin@platform.com",
            role="sysadmin",
            hashed_password="password",
            pin="9999"
        )
        db.add(sysadmin)
        db.commit() # Commit sysadmin

        # Create Default Restaurant
        print("Creating default restaurant...")
        restaurant_id = "d663b23a-09d4-45de-9cf5-8810196fdc13"
        rest = models.Restaurant(
            id=restaurant_id,
            name="Demo Restaurant",
            email="admin@demorestaurant.com",
            phone="555-0001",
            address="123 Example Street",
            customer_portal_url="demo-restaurant"
        )
        db.add(rest)
        db.commit() # Commit restaurant FIRST so foreign keys work

        # Create Second Restaurant
        print("Creating second restaurant...")
        restaurant_id_2 = "a8f3c45b-7d2e-4c9a-b1e2-9c7d6e5f3a2b"
        rest2 = models.Restaurant(
            id=restaurant_id_2,
            name="Gourmet Cafe",
            email="admin@gourmetcafe.com",
            phone="555-0002",
            address="456 Cuisine Avenue",
            customer_portal_url="gourmet-cafe"
        )
        db.add(rest2)
        db.commit() # Commit second restaurant

        # 1. Seed Users (attached to Demo Restaurant)
        print("Seeding users for Demo Restaurant...")
        users = [
            models.User(id="629fc2a5-979f-45ff-a2c2-d7312dfad44b", restaurant_id=restaurant_id, name="Admin User", username="admin", email="admin@demo.com", role="admin", hashed_password="password", pin="1234"),
            models.User(id="ce63ccc5-db8b-4399-9e5c-fbb23a1ef3d5", restaurant_id=restaurant_id, name="Reception Desk", username="reception", email="reception@demo.com", role="reception", hashed_password="password", pin="1111"),
            models.User(id="4bf7b2fe-f6ca-4e7b-8240-52d69d8afe77", restaurant_id=restaurant_id, name="Kitchen Display", username="kitchen", email="kitchen@demo.com", role="kitchen", hashed_password="password", pin="2222"),
            models.User(id="customer-demo-001", restaurant_id=restaurant_id, name="John Customer", username="customer1", email="customer@demo.com", role="customer", hashed_password="password", phone="555-0123")
        ]
        db.add_all(users)

        # Seed Users for Gourmet Cafe
        print("Seeding users for Gourmet Cafe...")
        users_cafe = [
            models.User(id="a1b2c3d4-e5f6-4a5b-8c9d-e0f1a2b3c4d5", restaurant_id=restaurant_id_2, name="Cafe Admin", username="cafe_admin", email="admin@gourmetcafe.com", role="admin", hashed_password="password", pin="5678"),
            models.User(id="b2c3d4e5-f6a7-4b5c-9d0e-f1a2b3c4d5e6", restaurant_id=restaurant_id_2, name="Cafe Reception", username="cafe_reception", email="reception@gourmetcafe.com", role="reception", hashed_password="password", pin="5555"),
            models.User(id="c3d4e5f6-a7b8-4c5d-0e1f-a2b3c4d5e6f7", restaurant_id=restaurant_id_2, name="Barista", username="barista", email="barista@gourmetcafe.com", role="kitchen", hashed_password="password", pin="6666"),
            models.User(id="customer-cafe-001", restaurant_id=restaurant_id_2, name="Sarah Visitor", username="customer_cafe", email="customer@gourmetcafe.com", role="customer", hashed_password="password", phone="555-0456")
        ]
        db.add_all(users_cafe)
        db.commit() # Commit users

        # 2. Seed Restaurant Tables (attached to Demo Restaurant)
        print("Seeding tables for Demo Restaurant...")
        tables = [
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Table 1", capacity=2, status="available", position_row=0, position_col=0, seats=2),
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Table 2", capacity=4, status="available", position_row=0, position_col=1, seats=4),
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Table 3", capacity=6, status="available", position_row=1, position_col=0, seats=6)
        ]
        db.add_all(tables)

        # Seed Tables for Gourmet Cafe
        print("Seeding tables for Gourmet Cafe...")
        tables_cafe = [
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Window Seat 1", capacity=2, status="available", position_row=0, position_col=0, seats=2),
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Bar Counter", capacity=5, status="available", position_row=0, position_col=1, seats=5),
            models.RestaurantTable(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Corner Nook", capacity=4, status="available", position_row=1, position_col=0, seats=4)
        ]
        db.add_all(tables_cafe)
        db.commit() # Commit tables

        # 3. Seed Menu Items (attached to Demo Restaurant)
        print("Seeding menu items for Demo Restaurant...")
        menu_items = [
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Premium Burger", price=14.99, category="main", description="Angus beef patty with secret sauce", image_url="https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="House Salad", price=8.99, category="appetizer", description="Fresh greens with balsamic", image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Truffle Fries", price=6.99, category="side", description="Crispy fries with truffle oil", image_url="https://images.unsplash.com/photo-1530016555861-110c8f411605?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id, name="Craft Cola", price=3.99, category="beverage", description="Local craft cola", image_url="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?auto=format&fit=crop&q=80&w=800")
        ]
        db.add_all(menu_items)

        # Seed Menu Items for Gourmet Cafe
        print("Seeding menu items for Gourmet Cafe...")
        menu_items_cafe = [
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Espresso", price=4.99, category="beverage", description="Single shot of premium espresso", image_url="https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Cappuccino", price=5.99, category="beverage", description="Espresso with steamed milk and foam", image_url="https://images.unsplash.com/photo-1517668808822-9ebb02ae2a0e?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Croissant", price=4.49, category="pastry", description="Buttery French pastry", image_url="https://images.unsplash.com/photo-1585080876282-87c1e92e4a8d?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Blueberry Muffin", price=5.49, category="pastry", description="Fresh blueberry muffin", image_url="https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?auto=format&fit=crop&q=80&w=800"),
            models.MenuItem(id=str(uuid.uuid4()), restaurant_id=restaurant_id_2, name="Greek Salad", price=9.99, category="main", description="Fresh feta, olives, and tomatoes", image_url="https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&q=80&w=800")
        ]
        db.add_all(menu_items_cafe)

        db.commit()

        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
