#!/usr/bin/env python3
"""
AI-Generated Service: calculate_order_total
Description: Calculate tax based on customer location
Generated: 2025-09-19T10:30:00.000000
"""

from typing import Dict, Any, List
import json
from datetime import datetime

async def calculate_order_total(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate order total with tax based on customer location.

    Inputs: items, customer_location, apply_discounts
    Outputs: subtotal, tax_amount, discount_amount, total, tax_rate
    """

    try:
        # Extract inputs
        items = data.get('items', [])
        customer_location = data.get('customer_location', {})
        apply_discounts = data.get('apply_discounts', True)

        # Calculate subtotal
        subtotal = 0
        for item in items:
            price = item.get('price', 0)
            quantity = item.get('quantity', 1)
            subtotal += price * quantity

        # Determine tax rate based on location
        state = customer_location.get('state', 'CA')
        tax_rates = {
            'CA': 0.0725,  # California
            'TX': 0.0625,  # Texas
            'NY': 0.08,    # New York
            'FL': 0.06,    # Florida
            'WA': 0.065,   # Washington
            'OR': 0,       # Oregon (no sales tax)
            'MT': 0,       # Montana (no sales tax)
            'NH': 0,       # New Hampshire (no sales tax)
            'DE': 0,       # Delaware (no sales tax)
            'AK': 0,       # Alaska (no sales tax)
        }

        # Add city tax for certain locations
        city = customer_location.get('city', '').upper()
        city_tax = 0
        if state == 'CA' and city == 'SAN FRANCISCO':
            city_tax = 0.01  # Additional 1% for SF
        elif state == 'NY' and city == 'NEW YORK':
            city_tax = 0.045  # NYC additional tax
        elif state == 'WA' and city == 'SEATTLE':
            city_tax = 0.0365  # Seattle additional tax

        base_tax_rate = tax_rates.get(state, 0.05)  # Default 5% for unknown states
        total_tax_rate = base_tax_rate + city_tax

        # Calculate tax
        tax_amount = subtotal * total_tax_rate

        # Apply discounts
        discount_amount = 0
        if apply_discounts:
            # Volume discount
            if subtotal > 1000:
                discount_amount = subtotal * 0.10  # 10% off for orders over $1000
            elif subtotal > 500:
                discount_amount = subtotal * 0.05  # 5% off for orders over $500

            # Loyalty discount (if customer data provided)
            if data.get('customer_tier') == 'gold':
                discount_amount += subtotal * 0.05  # Additional 5% for gold members
            elif data.get('customer_tier') == 'platinum':
                discount_amount += subtotal * 0.10  # Additional 10% for platinum

        # Calculate final total
        total = subtotal - discount_amount + tax_amount

        result = {
            'subtotal': round(subtotal, 2),
            'tax_amount': round(tax_amount, 2),
            'tax_rate': round(total_tax_rate * 100, 2),  # As percentage
            'discount_amount': round(discount_amount, 2),
            'total': round(total, 2),
            'location_used': f"{city}, {state}" if city else state,
            'discounts_applied': []
        }

        # List applied discounts
        if discount_amount > 0:
            if subtotal > 1000:
                result['discounts_applied'].append('Volume discount (10%)')
            elif subtotal > 500:
                result['discounts_applied'].append('Volume discount (5%)')

            if data.get('customer_tier') == 'gold':
                result['discounts_applied'].append('Gold member discount (5%)')
            elif data.get('customer_tier') == 'platinum':
                result['discounts_applied'].append('Platinum member discount (10%)')

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
def calculate_order_total_sync(data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for the async function"""
    import asyncio
    return asyncio.run(calculate_order_total(data))

__all__ = ['calculate_order_total', 'calculate_order_total_sync']