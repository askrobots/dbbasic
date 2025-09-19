#!/usr/bin/env python3
"""
AI-Generated Service: detect_fraud
Description: Score orders for fraud risk using multiple signals
Generated: 2025-09-19T10:32:00.000000
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
import hashlib
import random

async def detect_fraud(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze transaction data for fraud indicators and return a risk score.

    Inputs: order_data, customer_data, payment_data, shipping_data
    Outputs: fraud_score, risk_level, signals_detected, action_recommended, reason_codes
    """

    try:
        # Extract inputs
        order_data = data.get('order_data', {})
        customer_data = data.get('customer_data', {})
        payment_data = data.get('payment_data', {})
        shipping_data = data.get('shipping_data', {})

        # Initialize fraud scoring
        fraud_score = 0
        signals_detected = []
        reason_codes = []

        # 1. Check order value anomalies
        order_total = order_data.get('total', 0)
        avg_order_value = customer_data.get('average_order_value', 100)

        if order_total > avg_order_value * 5:
            fraud_score += 25
            signals_detected.append('High order value')
            reason_codes.append('HIGH_ORDER_VALUE')
        elif order_total > avg_order_value * 3:
            fraud_score += 15
            signals_detected.append('Elevated order value')
            reason_codes.append('ELEVATED_ORDER_VALUE')

        # 2. Check customer history
        account_age_days = customer_data.get('account_age_days', 0)
        previous_orders = customer_data.get('previous_orders', 0)

        if account_age_days < 1:
            fraud_score += 30
            signals_detected.append('New account')
            reason_codes.append('NEW_ACCOUNT')
        elif account_age_days < 7:
            fraud_score += 15
            signals_detected.append('Recent account')
            reason_codes.append('RECENT_ACCOUNT')

        if previous_orders == 0 and order_total > 500:
            fraud_score += 20
            signals_detected.append('First order high value')
            reason_codes.append('FIRST_ORDER_HIGH_VALUE')

        # 3. Check payment method risks
        payment_method = payment_data.get('method', 'card')
        card_verification_failed = payment_data.get('cvv_verification_failed', False)
        billing_zip_mismatch = payment_data.get('billing_zip_mismatch', False)

        if payment_method == 'prepaid_card':
            fraud_score += 15
            signals_detected.append('Prepaid card used')
            reason_codes.append('PREPAID_CARD')

        if card_verification_failed:
            fraud_score += 35
            signals_detected.append('Card verification failed')
            reason_codes.append('CVV_FAILED')

        if billing_zip_mismatch:
            fraud_score += 25
            signals_detected.append('Billing ZIP mismatch')
            reason_codes.append('ZIP_MISMATCH')

        # 4. Check shipping address risks
        billing_shipping_mismatch = shipping_data.get('different_from_billing', False)
        po_box_address = shipping_data.get('is_po_box', False)
        high_risk_country = shipping_data.get('country') in ['NG', 'RO', 'PK', 'ID']

        if billing_shipping_mismatch:
            fraud_score += 10
            signals_detected.append('Billing/shipping mismatch')
            reason_codes.append('ADDRESS_MISMATCH')

        if po_box_address and order_total > 200:
            fraud_score += 15
            signals_detected.append('PO Box for high value order')
            reason_codes.append('PO_BOX_HIGH_VALUE')

        if high_risk_country:
            fraud_score += 30
            signals_detected.append('High risk country')
            reason_codes.append('HIGH_RISK_COUNTRY')

        # 5. Check velocity patterns
        orders_last_hour = customer_data.get('orders_last_hour', 0)
        orders_last_day = customer_data.get('orders_last_day', 0)

        if orders_last_hour > 3:
            fraud_score += 40
            signals_detected.append('High order velocity')
            reason_codes.append('VELOCITY_HOUR')
        elif orders_last_day > 10:
            fraud_score += 25
            signals_detected.append('Elevated daily orders')
            reason_codes.append('VELOCITY_DAY')

        # 6. Check device fingerprint
        device_data = data.get('device_data', {})
        vpn_detected = device_data.get('vpn_detected', False)
        multiple_accounts_same_device = device_data.get('multiple_accounts', False)

        if vpn_detected:
            fraud_score += 20
            signals_detected.append('VPN detected')
            reason_codes.append('VPN_DETECTED')

        if multiple_accounts_same_device:
            fraud_score += 35
            signals_detected.append('Multiple accounts on device')
            reason_codes.append('MULTI_ACCOUNT_DEVICE')

        # 7. Email analysis
        email = customer_data.get('email', '')
        if email:
            disposable_email = any(domain in email.lower() for domain in ['tempmail', 'guerrillamail', '10minutemail'])
            if disposable_email:
                fraud_score += 25
                signals_detected.append('Disposable email')
                reason_codes.append('DISPOSABLE_EMAIL')

        # Cap fraud score at 100
        fraud_score = min(fraud_score, 100)

        # Determine risk level and action
        if fraud_score >= 75:
            risk_level = 'critical'
            action_recommended = 'block'
        elif fraud_score >= 50:
            risk_level = 'high'
            action_recommended = 'manual_review'
        elif fraud_score >= 30:
            risk_level = 'medium'
            action_recommended = 'additional_verification'
        elif fraud_score >= 15:
            risk_level = 'low'
            action_recommended = 'monitor'
        else:
            risk_level = 'minimal'
            action_recommended = 'approve'

        result = {
            'fraud_score': fraud_score,
            'risk_level': risk_level,
            'signals_detected': signals_detected,
            'action_recommended': action_recommended,
            'reason_codes': reason_codes,
            'confidence': round(0.7 + (len(signals_detected) * 0.03), 2),  # Higher confidence with more signals
            'review_priority': 'urgent' if fraud_score >= 75 else ('high' if fraud_score >= 50 else 'normal'),
            'estimated_loss_prevented': round(order_total * (fraud_score / 100), 2) if fraud_score >= 50 else 0
        }

        # Add detailed breakdown
        result['score_breakdown'] = {
            'order_risk': min(40, sum(1 for code in reason_codes if 'ORDER' in code or 'VALUE' in code) * 15),
            'customer_risk': min(30, sum(1 for code in reason_codes if 'ACCOUNT' in code) * 15),
            'payment_risk': min(35, sum(1 for code in reason_codes if 'CARD' in code or 'CVV' in code or 'ZIP' in code) * 15),
            'shipping_risk': min(25, sum(1 for code in reason_codes if 'ADDRESS' in code or 'PO_BOX' in code or 'COUNTRY' in code) * 10),
            'velocity_risk': min(40, sum(1 for code in reason_codes if 'VELOCITY' in code) * 25),
            'device_risk': min(35, sum(1 for code in reason_codes if 'VPN' in code or 'DEVICE' in code) * 20)
        }

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": result
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Synchronous wrapper
def detect_fraud_sync(data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for the async function"""
    import asyncio
    return asyncio.run(detect_fraud(data))

__all__ = ['detect_fraud', 'detect_fraud_sync']