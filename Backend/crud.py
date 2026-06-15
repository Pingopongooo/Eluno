from database import get_db_connection
from datetime import datetime, timedelta

def get_all_active_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT o.*, l.name as lens_type_name, s.contact_email as store_email, s.location as store_location
            FROM orders o
            JOIN lens_types l ON o.lens_type_id = l.id
            JOIN stores s ON o.store_id = s.id
            WHERE o.status != 'Delivered' 
            ORDER BY o.created_at DESC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT i.*, l.name as lens_type_name 
            FROM lens_inventory i
            JOIN lens_types l ON i.lens_type_id = l.id
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_lens_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM lens_types")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def create_order(order_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sla_days FROM lens_types WHERE id = %s", (order_data.lens_type_id,))
        lens_type = cursor.fetchone()
        sla_days = lens_type['sla_days'] if lens_type else 3
        
        created_at = datetime.now()
        sla_deadline = created_at + timedelta(days=sla_days)
        predicted_delivery_date = sla_deadline

        re_sph = order_data.re_sphere or 0.0
        le_sph = order_data.le_sphere or 0.0
        
        cursor.execute("""
            SELECT id, quantity_in_stock FROM lens_inventory 
            WHERE lens_type_id = %s 
              AND lens_index = %s 
              AND sphere_min <= %s AND sphere_max >= %s
              AND sphere_min <= %s AND sphere_max >= %s
              AND quantity_in_stock > 0
        """, (order_data.lens_type_id, order_data.lens_index, re_sph, re_sph, le_sph, le_sph))
        
        inventory_item = cursor.fetchone()
        is_lens_in_stock = bool(inventory_item)
        initial_status = "Order Placed" if is_lens_in_stock else "Lens Procurement"

        cursor.execute("""
            INSERT INTO orders (
                customer_name, customer_phone, store_id, 
                re_sphere, re_cylinder, re_axis, re_add, 
                le_sphere, le_cylinder, le_axis, le_add, 
                lens_type_id, lens_index, coating, frame_details, 
                status, created_at, sla_deadline, predicted_delivery_date, is_lens_in_stock
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """, (
            order_data.customer_name, order_data.customer_phone, order_data.store_id,
            order_data.re_sphere, order_data.re_cylinder, order_data.re_axis, order_data.re_add,
            order_data.le_sphere, order_data.le_cylinder, order_data.le_axis, order_data.le_add,
            order_data.lens_type_id, order_data.lens_index, order_data.coating, order_data.frame_details,
            initial_status, created_at, sla_deadline, predicted_delivery_date, is_lens_in_stock
        ))
        
        order_id = cursor.fetchone()['id']

        if is_lens_in_stock:
            cursor.execute("""
                UPDATE lens_inventory SET quantity_in_stock = quantity_in_stock - 1 WHERE id = %s
            """, (inventory_item['id'],))

        cursor.execute("""
            INSERT INTO order_status_history (order_id, status, changed_by, reason)
            VALUES (%s, %s, %s, %s)
        """, (order_id, initial_status, "System", "Initial Order Intake"))

        conn.commit()
        return {
            "order_id": order_id,
            "status": initial_status,
            "is_lens_in_stock": is_lens_in_stock,
            "sla_deadline": sla_deadline.isoformat()
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def update_status(order_id: int, status_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (status_data.status, order_id))
        
        # If reason is empty, log a neutral system note
        reason = status_data.reason if status_data.reason and status_data.reason.strip() else "No delay reported."
        
        cursor.execute("""
            INSERT INTO order_status_history (order_id, status, changed_by, reason)
            VALUES (%s, %s, %s, %s)
        """, (order_id, status_data.status, status_data.changed_by, reason))
        conn.commit()
        return {"order_id": order_id, "new_status": status_data.status}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def delete_order(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM order_status_history WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM alerts WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        conn.commit()
        return {"success": True, "message": f"Order #{order_id} successfully deleted."}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM alerts ORDER BY sent_at DESC")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_order_by_id(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT o.*, s.contact_email as store_email, l.name as lens_type_name, l.sla_days
            FROM orders o 
            JOIN stores s ON o.store_id = s.id
            JOIN lens_types l ON o.lens_type_id = l.id
            WHERE o.id = %s
        """, (order_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

def get_order_status_history(order_id: int):
    """
    Fetches the full status history for an order including timestamps and staff reasons.
    This timeline is passed to Gemini as context for breach risk assessment.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT status, changed_at, changed_by, reason
            FROM order_status_history
            WHERE order_id = %s
            ORDER BY changed_at ASC
        """, (order_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def get_historical_context_summary(lens_type_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN breach_risk_score = 'High' THEN 1 ELSE 0 END) as breaches,
                SUM(CASE WHEN breach_risk_reason ILIKE '%%QC fail%%' THEN 1 ELSE 0 END) as qc_fails
            FROM historical_orders WHERE lens_type_id = %s
        """, (lens_type_id,))
        data = cursor.fetchone()
        return f"Out of {data['total']} past orders for this lens type, {data['breaches']} breached SLA and {data['qc_fails']} involved QC failures."
    finally:
        cursor.close()
        conn.close()

def get_qc_failure_count(order_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) as fails FROM order_status_history 
            WHERE order_id = %s AND status = 'QC Failed'
        """, (order_id,))
        return cursor.fetchone()['fails']
    finally:
        cursor.close()
        conn.close()

def check_alert_sent(order_id: int, alert_type: str) -> bool:
    """
    Checks if a specific alert type has EVER been sent for this order.
    One email per order per alert type, forever. No spam.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM alerts 
            WHERE order_id = %s AND alert_type = %s
        """, (order_id, alert_type))
        return cursor.fetchone()['cnt'] > 0
    finally:
        cursor.close()
        conn.close()

def update_order_risk(order_id: int, score: str, reason: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE orders SET breach_risk_score = %s, breach_risk_reason = %s 
            WHERE id = %s
        """, (score, reason, order_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def update_order_prediction(order_id: int, predicted_date: datetime, score: str, reason: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE orders SET predicted_delivery_date = %s, breach_risk_score = %s, breach_risk_reason = %s 
            WHERE id = %s
        """, (predicted_date, score, reason, order_id))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def log_alert(order_id: int, alert_type: str, message: str, email_to: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO alerts (order_id, alert_type, message, email_sent_to)
            VALUES (%s, %s, %s, %s)
        """, (order_id, alert_type, message, email_to))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
