
# CONVERSION TRACKING SETUP GUIDE - Wright's Search Campaigns

## WHY THIS IS CRITICAL
Without proper conversion tracking, all bid strategies (Maximize Conversions, Target CPA) will fail. This is the foundation of data-driven bidding.

## GOOGLE ADS CONVERSION ACTIONS REQUIRED

### 1. Website Quote Form Submissions
**Setup Steps**:
1. Go to Tools & Settings > Measurement > Conversions
2. Click "New conversion action"
3. Select "Website"
4. Choose "Submit a form or sign up"
5. Name: "Website Quote Form"
6. Value: Use different values for each action
   - Impact Windows: $200
   - Impact Doors: $150
   - Hurricane Protection: $300
   - Energy Efficiency: $100
   - Commercial Solutions: $500
7. Attribution: Data-driven attribution
8. Conversion window: 30 days

### 2. Phone Calls from Ads
**Setup Steps**:
1. New conversion action > Phone calls
2. Name: "Phone Call Leads"
3. Value: Same as website quotes
4. Attribution: Data-driven
5. Include calls to a Google forwarding number
6. Enable call reporting

### 3. Appointment Booking Form
**Setup Steps**:
1. New conversion action > Website
2. "Schedule an appointment"
3. Name: "Appointment Bookings"
4. Value: 2x quote value (higher intent)
5. Attribution: First-click (direct intent)

### 4. Contact Form Submissions
**Setup Steps**:
1. New conversion action > Website
2. "Contact or lead form"
3. Name: "Contact Form Leads"
4. Value: 0.5x quote value (lower intent)
5. Attribution: Last-click

## GOOGLE TAG MANAGER INTEGRATION

### Required Tags:
1. **Google Ads Conversion Tracking Tag**
2. **Google Analytics GA4 Tag**
3. **Facebook Pixel** (if using)
4. **Call Tracking Tags**

### Triggers Needed:
- Form submission triggers
- Phone click triggers
- Appointment booking triggers
- Contact form triggers

## CROSS-DOMAIN TRACKING
**If using subdomains**: Enable cross-domain tracking in GA4 and GTM

## ATTRIBUTION MODEL RECOMMENDATIONS
- **Primary**: Data-driven attribution
- **Fallback**: Last-click for conservative measurement
- **Custom**: First-click for direct response campaigns

## TESTING CONVERSION TRACKING
1. Submit test forms and verify conversions appear in Google Ads
2. Make test phone calls and verify tracking
3. Check attribution reports for accuracy
4. Validate conversion values match expectations

## MONTHLY AUDIT REQUIREMENTS
- Verify all conversion actions are active
- Check for duplicate conversions
- Validate attribution settings
- Review conversion value assignments
