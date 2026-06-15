import os
import re
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import crud
from email_service import send_alert_email
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    'gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)


# -------------------------------------------------------------------
# HELPER: Build a readable timeline string from status history rows
# -------------------------------------------------------------------
def build_timeline_narrative(history: list) -> str:
    """
    Converts order_status_history rows into a plain English timeline
    that Gemini can read and reason about.

    Example output:
      - [2024-01-01 10:00] Order Placed — by System. Note: Initial Order Intake
      - [2024-01-01 14:00] Coating — by Store Staff. Note: No delay reported.
      - [2024-01-02 09:00] QC Failed — by Store Staff. Note: Air bubble on left lens.
    """
    if not history:
        return "No status history available."

    lines = []
    for row in history:
        changed_at = (
            row['changed_at'].strftime('%Y-%m-%d %H:%M')
            if row['changed_at'] else 'Unknown time'
        )
        lines.append(
            f"  - [{changed_at}] {row['status']} — by {row['changed_by']}. "
            f"Note: {row['reason']}"
        )
    return "\n".join(lines)


# -------------------------------------------------------------------
# HELPER: Check if a stage has a staff-reported delay in history
# -------------------------------------------------------------------
def get_stage_delay_reason(history: list, stage: str) -> str | None:
    """
    Looks through status history for a specific stage.
    Returns the staff reason if it was not the default neutral note.
    Returns None if no delay was reported for that stage.
    """
    for row in history:
        if (
            row['status'] == stage
            and row['reason']
            and row['reason'] != "No delay reported."
            and row['changed_by'] != "System"
        ):
            return row['reason']
    return None


# -------------------------------------------------------------------
# HELPER: Extract total reported delay days from status history
# -------------------------------------------------------------------
def calculate_reported_delay_days(history: list) -> int:
    """
    Scans all staff notes in the history for mentions of day delays.
    Looks for patterns like '1 day delay', '2 day delay', 'delayed by 3 days'.
    Returns the total number of delay days reported by staff across all stages.
    This is used to calculate effective hours remaining for Gemini's assessment.
    """
    total_days = 0
    for row in history:
        if row['changed_by'] == "System":
            continue
        reason_text = (row['reason'] or '').lower()
        matches = re.findall(r'(\d+)\s*day', reason_text)
        if matches:
            total_days += sum(int(m) for m in matches)
    return total_days


# -------------------------------------------------------------------
# EMAIL GENERATOR: Uses Gemini to write professional alert emails
# -------------------------------------------------------------------
def generate_alert_email(order: dict, alert_context: str) -> dict:
    """
    Asks Gemini to write a professional alert email.
    Only generates the EMAIL TEXT. All decisions are made in Python.
    """
    prompt = f"""
    You are an AI assistant for an eyewear order management system.
    Write a professional, concise alert email to the store manager.

    Order Details:
    - Order ID: #{order['id']}
    - Customer: {order['customer_name']}
    - Lens Type: {order['lens_type_name']}
    - Current Status: {order['status']}
    - SLA Deadline: {order['sla_deadline']}
    - Alert Reason: {alert_context}

    Keep the email under 150 words. Be direct and actionable.
    Do not make up any information not provided above.

    Respond STRICTLY in JSON with exactly two keys: "subject" and "body".
    """
    response = model.generate_content(prompt)
    return json.loads(response.text)


# -------------------------------------------------------------------
# STAGE DELAY HANDLER: Sends one email per stage per order, ever
# -------------------------------------------------------------------
def handle_stage_delay(order_id: int, stage: str, delay_reason: str):
    """
    Called by the hourly agent when it detects a staff-reported delay
    at a specific stage.

    Alert types:
    - Procurement_Delay
    - Coating_Delay
    - Edging_Fitting_Delay

    One email per alert type per order, forever. No repeats.
    """
    stage_to_alert_type = {
        "Lens Procurement": "Procurement_Delay",
        "Coating":          "Coating_Delay",
        "Edging & Fitting": "Edging_Fitting_Delay"
    }

    alert_type = stage_to_alert_type.get(stage)
    if not alert_type:
        return

    # Already sent this exact alert for this order — stop
    if crud.check_alert_sent(order_id, alert_type):
        print(f"[Stage Delay] {alert_type} already sent for Order #{order_id}. Skipping.")
        return

    order = crud.get_order_by_id(order_id)
    if not order:
        return

    alert_context = (
        f"Staff reported a delay at the {stage} stage. "
        f"Reason given: {delay_reason}"
    )

    try:
        email_content = generate_alert_email(order, alert_context)
        recipient = os.getenv("GMAIL_USER")
        sent = send_alert_email(recipient, email_content['subject'], email_content['body'])
        if sent:
            crud.log_alert(order_id, alert_type, email_content['body'], recipient)
            print(f"[Stage Delay] {alert_type} email sent for Order #{order_id}.")
    except Exception as e:
        print(f"[Stage Delay] Failed to send email for Order #{order_id}: {e}")


# -------------------------------------------------------------------
# QC FAILURE HANDLER: Called immediately when staff marks QC Failed
# Python calculates the new date. Gemini only writes the message.
# -------------------------------------------------------------------
def handle_qc_failure(order_id: int):
    """
    Called as a FastAPI background task when staff marks QC Failed.

    Python handles : predicted delivery date recalculation (timedelta)
    Gemini handles : escalation message text ONLY

    One QC_Failure_Escalation email per order, ever.
    """
    order = crud.get_order_by_id(order_id)
    if not order:
        return

    qc_fails = crud.get_qc_failure_count(order_id)

    # Python does the date math — each QC failure adds 36 hours
    current_predicted = order['predicted_delivery_date'] or order['sla_deadline']
    new_predicted_date = current_predicted + timedelta(hours=36)

    # Gemini writes the escalation message text only
    prompt = f"""
    An eyewear order has failed Quality Control. Write a brief escalation message
    explaining the situation to the store manager. Be factual and concise.

    Facts:
    - Order ID: #{order['id']}
    - Customer: {order['customer_name']}
    - Lens Type: {order['lens_type_name']}
    - QC Failure number: {qc_fails} (on this order)
    - Original SLA Deadline: {order['sla_deadline']}
    - New Predicted Delivery: {new_predicted_date.strftime('%Y-%m-%d %H:%M')}

    Write 2 to 3 sentences maximum. Do not make up information.

    Respond STRICTLY in JSON with one key: "escalation_message"
    """

    try:
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text)
        escalation_message = ai_data.get(
            'escalation_message',
            f"Order #{order['id']} has failed QC {qc_fails} time(s). "
            f"Predicted delivery pushed to {new_predicted_date.strftime('%Y-%m-%d')}."
        )
    except Exception as e:
        print(f"[QC Failure] Gemini call failed, using fallback message: {e}")
        escalation_message = (
            f"Order #{order['id']} has failed QC {qc_fails} time(s). "
            f"Predicted delivery pushed to {new_predicted_date.strftime('%Y-%m-%d')}."
        )

    # Update order with new predicted date and High risk
    crud.update_order_prediction(order_id, new_predicted_date, "High", escalation_message)

    # Send email only if not already sent for this order — ever
    if not crud.check_alert_sent(order_id, "QC_Failure_Escalation"):
        try:
            email_content = generate_alert_email(order, escalation_message)
            recipient = os.getenv("GMAIL_USER")
            sent = send_alert_email(recipient, email_content['subject'], email_content['body'])
            if sent:
                crud.log_alert(order_id, "QC_Failure_Escalation", email_content['body'], recipient)
                print(f"[QC Failure] Alert email sent for Order #{order_id}.")
        except Exception as e:
            print(f"[QC Failure] Failed to send email for Order #{order_id}: {e}")
    else:
        print(f"[QC Failure] Alert already sent for Order #{order_id}. Skipping email.")

    return {
        "new_predicted_date": new_predicted_date.isoformat(),
        "escalation_message": escalation_message
    }


# -------------------------------------------------------------------
# HOURLY AGENT: Runs every hour via APScheduler
# -------------------------------------------------------------------
def run_hourly_agent():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] ── AI Agent Hourly Run Started ──")

    try:
        orders = crud.get_all_active_orders()
    except Exception as e:
        print(f"[Agent] Failed to fetch orders: {e}")
        return

    if not orders:
        print("[Agent] No active orders to process.")
        return

    print(f"[Agent] Processing {len(orders)} active order(s)...")

    for order in orders:
        order_id = order['id']
        print(f"\n[Agent] Evaluating Order #{order_id} ({order['customer_name']}) "
              f"— Status: {order['status']}")

        try:
            # Step 1: Fetch full status history for this order
            history = crud.get_order_status_history(order_id)
            timeline = build_timeline_narrative(history)

            # Step 2: Fetch supporting context
            qc_fails = crud.get_qc_failure_count(order_id)
            history_summary = crud.get_historical_context_summary(order['lens_type_id'])

            # Step 3: Check for staff-reported stage delays and send emails
            stages_to_monitor = ["Lens Procurement", "Coating", "Edging & Fitting"]
            for stage in stages_to_monitor:
                delay_reason = get_stage_delay_reason(history, stage)
                if delay_reason:
                    handle_stage_delay(order_id, stage, delay_reason)

            # Step 4: Calculate time values for Gemini context
            now = datetime.now()
            sla_deadline = order['sla_deadline']
            time_remaining = sla_deadline - now
            hours_remaining = int(time_remaining.total_seconds() / 3600)
            is_breached = time_remaining.total_seconds() < 0

            # Step 5: Calculate effective hours remaining after reported delays
            # This is done in Python so Gemini does not have to do date math
            reported_delay_days = calculate_reported_delay_days(history)
            effective_hours_remaining = hours_remaining - (reported_delay_days * 24)
            is_effectively_breached = effective_hours_remaining < 0

            # Step 6: Ask Gemini for overall breach risk assessment
            prompt = f"""
            You are an AI agent assessing SLA breach risk for an eyewear order.
            Reason carefully using all the facts below. Do not guess or exaggerate.

            ORDER DETAILS:
            - Order ID: #{order_id}
            - Customer: {order['customer_name']}
            - Lens Type: {order['lens_type_name']}
            - Current Status: {order['status']}
            - Created At: {order['created_at']}
            - SLA Deadline: {sla_deadline}
            - Hours Remaining on SLA: {hours_remaining} {'(ALREADY BREACHED)' if is_breached else ''}
            - Staff Reported Delay Days (total across all stages): {reported_delay_days} day(s)
            - Effective Hours Remaining after reported delays: {effective_hours_remaining} hours {'(EFFECTIVELY BREACHED)' if is_effectively_breached else ''}
            - QC Failures on this order: {qc_fails}

            FULL ORDER TIMELINE (with staff notes and exact timestamps):
            {timeline}

            HISTORICAL CONTEXT for this lens type:
            {history_summary}

            ASSESSMENT RULES (follow strictly):
            - If SLA is already breached: always High
            - If effective hours remaining is negative: always High
            - If less than 12 hours remaining AND in an active manufacturing stage: High
            - A single QC failure with more than 48 effective hours remaining should NOT alone justify High risk
            - Multiple QC failures significantly increase risk regardless of time remaining
            - If staff noted delays, use effective hours remaining, not raw SLA hours, to assess risk
            - If effective hours remaining is above 48, a single stage delay alone does not justify High risk
            - Timestamps in the timeline matter: if all stage changes happened within minutes of each other, the order is likely being tested, not genuinely delayed — do not inflate risk based on rapid stage changes
            - Consider the current stage: later stages with little time left are riskier than early stages

            Respond STRICTLY in JSON with exactly two keys:
            1. "risk_score": one of ["Low", "Medium", "High"]
            2. "reason": one sentence explaining your assessment using specific facts from above.
            """

            response = model.generate_content(prompt)
            ai_data = json.loads(response.text)

            risk = ai_data.get('risk_score', 'Low')
            reason = ai_data.get('reason', 'Assessed by AI.')

            # Clamp to valid values in case of unexpected Gemini output
            if risk not in ['Low', 'Medium', 'High']:
                risk = 'Medium'

            crud.update_order_risk(order_id, risk, reason)
            print(f"[Agent] Order #{order_id}: {risk} Risk — {reason}")

            # Step 7: Send breach alert email if High risk
            # One Hourly_High_Risk_Breach email per order, ever. No spam.
            if risk == "High":
                if not crud.check_alert_sent(order_id, "Hourly_High_Risk_Breach"):
                    try:
                        alert_context = f"AI breach risk assessment: {reason}"
                        email_content = generate_alert_email(order, alert_context)
                        recipient = os.getenv("GMAIL_USER")
                        sent = send_alert_email(
                            recipient,
                            email_content['subject'],
                            email_content['body']
                        )
                        if sent:
                            crud.log_alert(
                                order_id,
                                "Hourly_High_Risk_Breach",
                                email_content['body'],
                                recipient
                            )
                            print(f"[Agent] High Risk alert email sent for Order #{order_id}.")
                    except Exception as e:
                        print(f"[Agent] Failed to send breach alert for Order #{order_id}: {e}")
                else:
                    print(f"[Agent] Order #{order_id} is High Risk but alert already sent. Skipping.")

        except Exception as e:
            print(f"[Agent] Error processing Order #{order_id}: {e}")
            continue

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] ── AI Agent Hourly Run Complete ──\n")


if __name__ == "__main__":
    print("Testing AI Agent in isolation...")
    run_hourly_agent()