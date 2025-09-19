#!/usr/bin/env python3
"""
AI-Generated Service: segment_customer
Description: Categorize customers by value, behavior, and engagement
Generated: 2025-09-19T10:33:00.000000
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

async def segment_customer(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Segment customers into categories based on value, behavior, and engagement metrics.

    Inputs: customer_id, purchase_history, engagement_metrics, demographic_data
    Outputs: segment, sub_segment, lifetime_value_tier, churn_risk, recommendations, profile_summary
    """

    try:
        # Extract inputs
        customer_id = data.get('customer_id')
        purchase_history = data.get('purchase_history', {})
        engagement_metrics = data.get('engagement_metrics', {})
        demographic_data = data.get('demographic_data', {})

        # Calculate key metrics
        total_purchases = purchase_history.get('total_orders', 0)
        lifetime_value = purchase_history.get('lifetime_value', 0)
        avg_order_value = purchase_history.get('average_order_value', 0)
        days_since_last_order = purchase_history.get('days_since_last_order', 0)
        purchase_frequency = purchase_history.get('orders_per_month', 0)

        # Engagement scoring
        email_open_rate = engagement_metrics.get('email_open_rate', 0)
        click_through_rate = engagement_metrics.get('click_through_rate', 0)
        app_usage_days = engagement_metrics.get('app_usage_days_per_month', 0)
        support_tickets = engagement_metrics.get('support_tickets_last_90_days', 0)
        reviews_written = engagement_metrics.get('reviews_written', 0)
        referrals_made = engagement_metrics.get('referrals_made', 0)

        # Demographics
        account_age_months = demographic_data.get('account_age_months', 0)
        location_tier = demographic_data.get('location_tier', 'suburban')  # urban, suburban, rural
        preferred_channel = demographic_data.get('preferred_channel', 'web')

        # Determine primary segment
        if lifetime_value >= 10000 and purchase_frequency >= 2:
            segment = 'VIP'
            sub_segment = 'Platinum'
        elif lifetime_value >= 5000 and purchase_frequency >= 1:
            segment = 'VIP'
            sub_segment = 'Gold'
        elif lifetime_value >= 2000 or purchase_frequency >= 1:
            segment = 'Loyal'
            sub_segment = 'Regular'
        elif total_purchases >= 2:
            segment = 'Active'
            sub_segment = 'Occasional'
        elif total_purchases == 1:
            segment = 'New'
            sub_segment = 'First-time'
        else:
            segment = 'Prospect'
            sub_segment = 'Potential'

        # Refine based on recency
        if days_since_last_order > 180:
            if segment in ['VIP', 'Loyal']:
                segment = 'At Risk'
                sub_segment = 'Lapsed ' + sub_segment
            else:
                segment = 'Dormant'
                sub_segment = 'Inactive'
        elif days_since_last_order > 90 and segment != 'VIP':
            sub_segment = 'Cooling'

        # Determine lifetime value tier
        if lifetime_value >= 10000:
            lifetime_value_tier = 'Diamond'
        elif lifetime_value >= 5000:
            lifetime_value_tier = 'Platinum'
        elif lifetime_value >= 2000:
            lifetime_value_tier = 'Gold'
        elif lifetime_value >= 500:
            lifetime_value_tier = 'Silver'
        else:
            lifetime_value_tier = 'Bronze'

        # Calculate churn risk
        churn_score = 0

        if days_since_last_order > 60:
            churn_score += 30
        if days_since_last_order > 120:
            churn_score += 30

        if email_open_rate < 0.1:
            churn_score += 20
        if app_usage_days < 2:
            churn_score += 20

        if support_tickets > 3:
            churn_score += 15

        if purchase_frequency < 0.5:
            churn_score += 15

        churn_risk = 'High' if churn_score >= 70 else ('Medium' if churn_score >= 40 else 'Low')

        # Generate recommendations based on segment
        recommendations = []

        if segment == 'VIP':
            recommendations.extend([
                'Assign dedicated account manager',
                'Offer exclusive early access to new products',
                'Provide VIP customer service line',
                'Send personalized thank you gifts'
            ])
        elif segment == 'Loyal':
            recommendations.extend([
                'Enroll in loyalty rewards program',
                'Send birthday and anniversary offers',
                'Provide product recommendations based on history'
            ])
        elif segment == 'At Risk':
            recommendations.extend([
                'Send win-back campaign immediately',
                'Offer special comeback discount',
                'Survey to understand dissatisfaction',
                'Personal outreach from customer success'
            ])
        elif segment == 'Active':
            recommendations.extend([
                'Encourage second purchase with discount',
                'Send product education emails',
                'Highlight customer reviews and testimonials'
            ])
        elif segment == 'New':
            recommendations.extend([
                'Send welcome series emails',
                'Offer first-time buyer discount for next purchase',
                'Request feedback on first experience'
            ])
        elif segment == 'Dormant':
            recommendations.extend([
                'Re-engagement email campaign',
                'Special reactivation offer',
                'Update on new products and improvements'
            ])

        # Add channel-specific recommendations
        if preferred_channel == 'mobile':
            recommendations.append('Optimize mobile app experience')
        elif preferred_channel == 'social':
            recommendations.append('Increase social media engagement')

        # Build profile summary
        profile_summary = {
            'value_indicator': 'High Value' if lifetime_value >= 2000 else ('Medium Value' if lifetime_value >= 500 else 'Low Value'),
            'activity_level': 'Highly Active' if purchase_frequency >= 2 else ('Active' if purchase_frequency >= 1 else 'Inactive'),
            'engagement_level': 'Highly Engaged' if email_open_rate > 0.3 else ('Engaged' if email_open_rate > 0.15 else 'Low Engagement'),
            'loyalty_status': 'Champion' if referrals_made > 2 else ('Advocate' if reviews_written > 3 else 'Customer'),
            'preferred_channel': preferred_channel,
            'customer_since': f"{account_age_months} months"
        }

        # Calculate potential value
        if segment in ['New', 'Active']:
            potential_value = avg_order_value * 12 * 2  # Potential for 2 years
        else:
            potential_value = avg_order_value * purchase_frequency * 12

        result = {
            'segment': segment,
            'sub_segment': sub_segment,
            'lifetime_value_tier': lifetime_value_tier,
            'churn_risk': churn_risk,
            'churn_score': churn_score,
            'recommendations': recommendations,
            'profile_summary': profile_summary,
            'potential_value': round(potential_value, 2),
            'engagement_score': round((email_open_rate * 30 + click_through_rate * 30 + (app_usage_days/30) * 40), 2),
            'segment_confidence': 0.85,  # Could be calculated based on data completeness
            'next_review_date': (datetime.now() + timedelta(days=30)).isoformat()
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
def segment_customer_sync(data: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for the async function"""
    import asyncio
    return asyncio.run(segment_customer(data))

__all__ = ['segment_customer', 'segment_customer_sync']