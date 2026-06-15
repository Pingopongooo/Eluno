import random
from datetime import datetime, timedelta
from database import get_db_connection

def create_tables(cursor):
    print("Creating tables...")
    
    # Drop existing tables for a clean slate
    cursor.execute("""
        DROP TABLE IF EXISTS alerts CASCADE;
        DROP TABLE IF EXISTS order_status_history CASCADE;
        DROP TABLE IF EXISTS historical_orders CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS lens_inventory CASCADE;
        DROP TABLE IF EXISTS lens_types CASCADE;
        DROP TABLE IF EXISTS stores CASCADE;
    """)

    cursor.execute("""
        CREATE TABLE stores (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            location VARCHAR(255) NOT NULL,
            contact_email VARCHAR(255) NOT NULL
        );

        CREATE TABLE lens_types (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            sla_days INTEGER NOT NULL,
            description TEXT
        );

        CREATE TABLE lens_inventory (
            id SERIAL PRIMARY KEY,
            lens_type_id INTEGER REFERENCES lens_types(id),
            sphere_min NUMERIC NOT NULL,
            sphere_max NUMERIC NOT NULL,
            lens_index NUMERIC NOT NULL,
            quantity_in_stock INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL
        );

        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            customer_phone VARCHAR(50),
            store_id INTEGER REFERENCES stores(id),
            re_sphere NUMERIC,
            re_cylinder NUMERIC,
            re_axis INTEGER,
            re_add NUMERIC,
            le_sphere NUMERIC,
            le_cylinder NUMERIC,
            le_axis INTEGER,
            le_add NUMERIC,
            lens_type_id INTEGER REFERENCES lens_types(id),
            lens_index NUMERIC,
            coating VARCHAR(100),
            frame_details VARCHAR(255),
            status VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sla_deadline TIMESTAMP,
            predicted_delivery_date TIMESTAMP,
            breach_risk_score VARCHAR(50),
            breach_risk_reason TEXT,
            is_lens_in_stock BOOLEAN
        );

        CREATE TABLE order_status_history (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            status VARCHAR(100),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            changed_by VARCHAR(100),
            reason TEXT
        );

        CREATE TABLE alerts (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            alert_type VARCHAR(100),
            message TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            email_sent_to VARCHAR(255)
        );

        CREATE TABLE historical_orders (
            id SERIAL PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            customer_phone VARCHAR(50),
            store_id INTEGER REFERENCES stores(id),
            re_sphere NUMERIC,
            re_cylinder NUMERIC,
            re_axis INTEGER,
            re_add NUMERIC,
            le_sphere NUMERIC,
            le_cylinder NUMERIC,
            le_axis INTEGER,
            le_add NUMERIC,
            lens_type_id INTEGER REFERENCES lens_types(id),
            lens_index NUMERIC,
            coating VARCHAR(100),
            frame_details VARCHAR(255),
            status VARCHAR(100),
            created_at TIMESTAMP,
            sla_deadline TIMESTAMP,
            predicted_delivery_date TIMESTAMP,
            breach_risk_score VARCHAR(50),
            breach_risk_reason TEXT,
            is_lens_in_stock BOOLEAN
        );
    """)
    print("Tables created successfully.")

def insert_base_data(cursor):
    print("Inserting base store, lens types, and inventory...")
    
    # Insert Store
    cursor.execute("""
        INSERT INTO stores (name, location, contact_email) 
        VALUES ('Eluno', 'HSR', 'vmshreyas1@gmail.com') RETURNING id;
    """)
    store_id = cursor.fetchone()['id']

    # Insert Lens Types
    lens_data = [
        ('Single Vision', 3, 'Standard single vision lenses for distance or reading.'),
        ('Bifocal', 4, 'Lenses with two distinct viewing areas.'),
        ('Progressive', 5, 'Multifocal lenses with a seamless progression of added magnifying power.')
    ]
    lens_type_ids = []
    for name, sla, desc in lens_data:
        cursor.execute("""
            INSERT INTO lens_types (name, sla_days, description) 
            VALUES (%s, %s, %s) RETURNING id;
        """, (name, sla, desc))
        lens_type_ids.append(cursor.fetchone()['id'])

    # Insert Inventory (Simulating standard in-house stock range)
    for l_id in lens_type_ids:
        cursor.execute("""
            INSERT INTO lens_inventory (lens_type_id, sphere_min, sphere_max, lens_index, quantity_in_stock, reorder_level)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (l_id, -4.00, 2.00, 1.56, 150, 20))

    return store_id, lens_type_ids

def generate_historical_orders(cursor, store_id, lens_type_ids):
    print("Generating 100 historical orders with strict distribution constraints...")
    
    # Parameters to hit exact distribution constraints
    total_orders = 100
    qc_failure_count = 30
    sla_breach_count = 25
    
    # We create pools of booleans and shuffle them to ensure exactly X orders get Y conditions
    qc_flags = [True] * qc_failure_count + [False] * (total_orders - qc_failure_count)
    breach_flags = [True] * sla_breach_count + [False] * (total_orders - sla_breach_count)
    
    random.shuffle(qc_flags)
    random.shuffle(breach_flags)

    # Possible prescription range: -0.50 to -6.00 in 0.25 steps
    spheres = [x * -0.25 for x in range(2, 25)]
    cylinders = [0.00, -0.25, -0.50, -0.75, -1.00]
    axes = list(range(10, 181, 10))
    indices = [1.56, 1.61, 1.67, 1.74]
    coatings = ['Anti-Reflective', 'Blue Cut', 'Scratch Resistant', 'None']
    
    # Fetch SLA mapping
    cursor.execute("SELECT id, sla_days FROM lens_types")
    sla_map = {row['id']: row['sla_days'] for row in cursor.fetchall()}

    for i in range(total_orders):
        is_qc_fail = qc_flags[i]
        is_breach = breach_flags[i]
        
        lens_id = random.choice(lens_type_ids)
        sla_days = sla_map[lens_id]
        
        # Prescription data
        re_sph = random.choice(spheres)
        le_sph = random.choice(spheres)
        re_cyl = random.choice(cylinders)
        le_cyl = random.choice(cylinders)
        axis = random.choice(axes)
        
        # Timeline generation (orders placed over the last 6 months)
        days_ago = random.randint(10, 180)
        created_at = datetime.now() - timedelta(days=days_ago)
        sla_deadline = created_at + timedelta(days=sla_days)
        
        # Determine actual completion (mapped to predicted_delivery_date for historical context)
        if is_breach:
            delay = random.randint(1, 4)
            actual_delivery = sla_deadline + timedelta(days=delay)
        else:
            early = random.randint(0, sla_days - 1)
            actual_delivery = sla_deadline - timedelta(days=early)
            
        # Build the narrative string that Gemini will read
        qc_text = f"Experienced {random.randint(1, 2)} QC failures." if is_qc_fail else "Passed QC smoothly."
        breach_text = "Breached SLA." if is_breach else "Delivered on time."
        reason_summary = f"{breach_text} {qc_text}"

        cursor.execute("""
            INSERT INTO historical_orders (
                customer_name, customer_phone, store_id, 
                re_sphere, re_cylinder, re_axis, re_add, 
                le_sphere, le_cylinder, le_axis, le_add, 
                lens_type_id, lens_index, coating, frame_details, 
                status, created_at, sla_deadline, predicted_delivery_date, 
                breach_risk_score, breach_risk_reason, is_lens_in_stock
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            f"Customer_{i+1}", f"987654{i:04d}", store_id,
            re_sph, re_cyl, axis, 0.00,
            le_sph, le_cyl, axis, 0.00,
            lens_id, random.choice(indices), random.choice(coatings), "Acetate Frame",
            "Delivered", created_at, sla_deadline, actual_delivery,
            "Low" if not is_breach else "High", reason_summary, True
        ))

def main():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        create_tables(cursor)
        store_id, lens_type_ids = insert_base_data(cursor)
        generate_historical_orders(cursor, store_id, lens_type_ids)
        conn.commit()
        print("Database seeded successfully! You are ready for Phase 2.")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()