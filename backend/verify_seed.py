#!/usr/bin/env python3
"""
Verification script to check if the seed data is properly created in the database.
"""

from database import SessionLocal
import models

def verify_seed_data():
    """Verify that the seed data has been created."""
    db = SessionLocal()
    
    print("=" * 60)
    print("SEED DATA VERIFICATION")
    print("=" * 60)
    
    # Count restaurants
    restaurants = db.query(models.Restaurant).all()
    print(f"\n✓ Total Restaurants: {len(restaurants)}")
    
    if len(restaurants) > 0:
        print("\n--- Restaurants ---")
        for rest in restaurants:
            user_count = db.query(models.User).filter(models.User.restaurant_id == rest.id).count()
            table_count = db.query(models.RestaurantTable).filter(models.RestaurantTable.restaurant_id == rest.id).count()
            menu_count = db.query(models.MenuItem).filter(models.MenuItem.restaurant_id == rest.id).count()
            
            print(f"\n  Restaurant: {rest.name}")
            print(f"    ID: {rest.id}")
            print(f"    Email: {rest.email}")
            print(f"    Portal URL: {rest.customer_portal_url}")
            print(f"    Users: {user_count}")
            print(f"    Tables: {table_count}")
            print(f"    Menu Items: {menu_count}")
    
    # Count system admin users
    sysadmin_count = db.query(models.User).filter(models.User.role == "sysadmin").count()
    print(f"\n✓ System Admin Users: {sysadmin_count}")
    
    if sysadmin_count > 0:
        print("\n--- System Admin ---")
        sysadmins = db.query(models.User).filter(models.User.role == "sysadmin").all()
        for admin in sysadmins:
            print(f"  Name: {admin.name}")
            print(f"  Email: {admin.email}")
            print(f"  PIN: {admin.pin}")
    
    # Count total users
    total_users = db.query(models.User).count()
    print(f"\n✓ Total Users: {total_users}")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    db.close()

if __name__ == "__main__":
    verify_seed_data()
