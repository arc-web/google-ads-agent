# Wright's Impact Window and Door Client-Specific Implementation Guide

## Overview

This implementation provides a comprehensive, client-specific Google Ads management platform for Wright's Impact Window and Door, Florida's premier impact window and door specialist with over 50 years of experience protecting homes and businesses from hurricanes, improving energy efficiency, and enhancing property value.

## Client Profile

- **Company**: Wright's Impact Window and Door
- **Website**: https://wrightsimpactwindowanddoor.com/
- **Phone**: 561-588-7353
- **Industry**: Impact Windows & Doors (Hurricane Protection)
- **Services**: Impact Windows, Impact Doors, Commercial Solutions, Financing Options
- **Experience**: 50+ years in Florida market
- **Locations**: Corporate Office (West Palm Beach), Regional Office (Punta Gorda), Statewide Service
- **Account Status**: New Client - Comprehensive Strategy Development

## Campaign Strategy

### Primary Focus Areas
1. **Hurricane Protection**: Storm preparedness and impact resistance
2. **Energy Efficiency**: Utility savings and environmental benefits
3. **Impact Windows**: Residential window replacement solutions
4. **Impact Doors**: Security and storm-resistant door systems
5. **Commercial Solutions**: Condo, multi-unit, and commercial property solutions
6. **Financing Options**: PACE financing, cash purchase, unsecured loans

### Key Differentiators
- 50+ years Florida hurricane protection experience
- Lifetime manufacturer guarantee
- Statewide service coverage
- Professional installation and custom measurements
- Energy efficiency certifications
- Insurance-approved products for premium discounts
- Multiple financing options to reduce barriers to purchase

## Technical Implementation

### Campaign Structure
- **Search Campaigns (TPPC)**: Primary conversion-focused campaigns by service type
- **Performance Max Campaigns**: Awareness and consideration for high-intent users
- **Display Campaigns**: Retargeting and awareness expansion
- **Local Campaigns**: Geographic targeting and local service area coverage

### Asset Groups (Performance Max)
1. Hurricane Protection & Storm Defense
2. Energy-Efficient Window Solutions
3. Impact Door Security Systems
4. Commercial Property Solutions
5. Financing & Payment Options
6. Before/After Project Results
7. Florida Service Area Coverage
8. Lifetime Guarantee & Warranties

## Performance Max Strategy

### Campaign-Level Settings
- **Budget**: $150-300 daily per major campaign (based on service value)
- **Networks**: Google Search, Search Partners, Display Network, YouTube
- **Languages**: English, Spanish (for Florida market)
- **Locations**: Florida statewide with radius targeting around offices
- **Ad Schedule**: Standard business hours with extended availability messaging

### Asset Group Configuration
- **Headlines**: Hurricane protection, energy savings, lifetime guarantee
- **Descriptions**: Trust signals, financing options, local service
- **Images**: Before/after project photos, product installations, storm damage prevention
- **Videos**: Installation process, storm protection demonstrations, customer testimonials
- **Sitelink Extensions**: Service pages, financing, contact information
- **Callouts**: "50+ Years Experience", "Lifetime Guarantee", "Licensed & Insured"

### Campaign Architecture & Ad Rules

### Document Structure & Critical Pathways
- **[`CLIENT_AD_COPY_REQUESTS.md`](CLIENT_AD_COPY_REQUESTS.md)**: **MANDATORY** client-specific requirements (100% inclusion required)
- **[`PERFORMANCE_MAX_AD_RULES.md`](PERFORMANCE_MAX_AD_RULES.md)**: **PMAX campaigns** - Asset Groups, AI optimization, multi-network
- **[`SEARCH_CAMPAIGN_AD_RULES.md`](SEARCH_CAMPAIGN_AD_RULES.md)**: **Search campaigns** - Ad Groups, RSA, keyword targeting
- **[`AD_COPY_BEST_PRACTICES.md`](AD_COPY_BEST_PRACTICES.md)**: Strategic framework and technical writing standards

### Campaign Type Pathways (NO CONFUSION ALLOWED)

#### Performance Max Campaigns
**File Pathway**: `campaigns/Wrights_Performance_Max_2026.csv`
**Structure**: Campaign → Asset Groups → Headlines (1-5) + Descriptions (1-5) + AI Optimization
**Rules**: Follow `PERFORMANCE_MAX_AD_RULES.md`
**Validation**: PMAX validation path in CSV validator

#### Search Campaigns
**File Pathway**: `campaigns/Wrights_Service_NearMe_Only_2026.csv`
**Structure**: Campaign → Ad Groups → Keywords → RSA Headlines (1-15) + Descriptions (1-5)
**Rules**: Follow `SEARCH_CAMPAIGN_AD_RULES.md`
**Validation**: Search validation path in CSV validator

### Client Requirements Integration (MANDATORY - 100% Compliance)
**CRITICAL**: All campaigns must include client requirements from `CLIENT_AD_COPY_REQUESTS.md` intuitively. Client gets exactly what they want, optimized for performance.

#### Core Client Requirements (Must Be Included):
1. **Energy Efficiency** - "Improve Energy Efficiency"
2. **Noise Reduction** - "Noise Reduction"
3. **Home Security** - "Increase Home Security"
4. **Insurance Benefits** - "Lower Insurance Rates"
5. **Property Value** - "Improve Property Value"
6. **Home Protection** - "safeguard your home"
7. **Florida Positioning** - "Impact Windows and Doors in FL with a Lifetime Guarantee"
8. **PACE Financing** - Complete financing details including "100% financing with no money down and deferred payments for over 12 months, based on home equity with no minimum credit score required"

## Strategic Ad Copy Framework (Technical Writing Standards)
**#1 Headlines (1-2 required per asset group):**
- Must start with "#1" followed by service information
- Examples: "#1 Impact Windows Expert", "#1 Hurricane Protection", "#1 Energy Efficient Solutions"
- Position as market leader in Florida impact window industry

**Brand-Specific Headlines (2 required per asset group):**
- Include exact brand: "Wright's Impact Windows" or "Wright's Impact Doors"
- Include brand variations: "Wright's Window & Door", "Wright's Impact Specialists"
- Must fit within 30 character limit while maintaining brand recognition

**Service-Focused Headlines (5+ required per asset group):**
- Impact Windows: "Premium Impact Windows", "Hurricane Impact Glass", "Storm-Resistant Windows"
- Impact Doors: "Impact Entry Doors", "Hurricane Door Systems", "Security Impact Doors"
- Energy Efficiency: "Energy-Efficient Windows", "Utility Bill Savings", "Green Building Solutions"
- Commercial: "Commercial Impact Windows", "Condo Impact Solutions", "Building Protection"

**Regional Headlines (5+ required per asset group):**
- Florida-specific: "Florida Hurricane Protection", "Florida Impact Windows"
- County-specific: "Lee County Impact Windows", "Broward County Protection"
- City-specific: "Fort Myers Impact Doors", "Naples Storm Protection"
- Combined: "Impact Windows Fort Myers", "Hurricane Doors Naples"

#### Description Requirements (80-90 chars optimal)
**Value Impact & Black Swan Messaging:**
- **Emergency Preparedness**: "Don't wait for storm season - protect your home now from hurricanes"
- **Insurance Benefits**: "Insurance-approved impact products for premium discounts"
- **Energy Savings**: "Reduce utility bills by up to 40% with energy-efficient impact windows"
- **Property Value**: "Increase home value with premium impact protection"
- **Peace of Mind**: "Sleep soundly knowing your family is protected from Florida storms"
- **Lifetime Protection**: "50+ years protecting Florida homes from hurricanes"

**Trust Signals & Credibility:**
- "50+ Years Florida Hurricane Protection Experience"
- "Lifetime Manufacturer Guarantee"
- "Licensed & State-Certified Installation"
- "Professional Measurements & Custom Solutions"

**Financing & Accessibility:**
- "Flexible Financing Options Available"
- "PACE Financing for Easy Payments"
- "Cash, Financing, or Unsecured Loans"

#### Character Limits Compliance - Technical Writing Standards
- **Headlines**: 22-29 characters **optimal** (22 min, 30 max - jam-pack value)
- **Descriptions**: 75-85 characters **optimal** (75 min, 90 max - jam-pack value)
- **Business Name**: ≤20 characters in Gmail ads
- **Callouts**: ≤25 characters per callout
- **Sitelink Text**: ≤25 characters
- **Sitelink Descriptions**: ≤35 characters

#### Technical Writing Requirements
- **Eliminate Filler Words**: No "the", "a", "an", "or", "very", "really", "just"
- **No Em Dashes**: Use hyphens or restructure sentences
- **Value Density**: Every character must contribute to conversion or urgency
- **Precision Language**: Maximum impact with minimum word count

#### Keyword Integration Strategy
- Map headlines to search themes from keyword research
- Combine service + regional targeting for hyper-local relevance
- Include long-tail keyword variations in descriptions
- Match user intent: awareness → consideration → conversion

#### Black Swan Value Proposition
**Why customers choose Wright's Impact (the "unspoken" reasons):**
- **Catastrophic Loss Prevention**: "Avoid total home destruction from hurricanes"
- **Insurance Claim Denial Avoidance**: "Prevent denied claims from inadequate protection"
- **Family Safety Priority**: "Protect what matters most - your family's safety"
- **Property Investment Protection**: "Safeguard your largest financial investment"
- **Peace of Mind**: "Eliminate hurricane anxiety year-round"

## Search Campaign Strategy

### Keyword Targeting Structure
- **Primary Keywords**: High-intent service + location combinations
- **Long-tail Keywords**: Problem-solution oriented searches
- **Negative Keywords**: Non-service related terms, competitors, DIY
- **Match Types**: Exact (converting terms), Phrase (related searches), Broad (discovery)

### Ad Copy Structure
- **Headline 1**: Primary service + hurricane protection
- **Headline 2**: Key benefit (energy savings, security, insurance)
- **Headline 3**: Trust signal (50+ years, lifetime guarantee)
- **Description**: Service details + financing options + phone number

### Campaign Architecture
1. **TPPC - Hurricane Protection**
   - Keywords: "hurricane windows Florida", "impact windows near me", "storm protection doors"
   - Focus: Emergency preparedness and storm defense

2. **TPPC - Impact Windows**
   - Keywords: "impact windows West Palm Beach", "energy efficient windows Florida", "hurricane impact windows"
   - Focus: Residential window replacement and upgrades

3. **TPPC - Impact Doors**
   - Keywords: "impact doors Florida", "storm resistant doors", "hurricane doors near me"
   - Focus: Door replacement and security enhancement

4. **TPPC - Commercial Solutions**
   - Keywords: "commercial impact windows", "condo impact doors", "multi unit property windows"
   - Focus: Commercial and multi-unit property solutions

5. **TPPC - Financing**
   - Keywords: "impact windows financing", "PACE financing windows", "window replacement loans"
   - Focus: Overcoming price objections through financing

## Local Service Area Strategy

### Geographic Targeting
- **Primary Targeting**: West Palm Beach, FL (corporate headquarters)
- **Secondary Targeting**: Punta Gorda, FL (regional office)
- **Statewide Coverage**: Florida service area with local intent keywords
- **Radius Targeting**: 25-50 mile radius from office locations
- **High-Value Areas**: Coastal regions, hurricane zones, high-rise communities

### Local Keywords by Intent
- **Immediate Need**: "emergency impact windows", "hurricane damage repair"
- **Local Intent**: "impact windows near me", "West Palm Beach impact windows"
- **Commercial**: "condo impact windows", "property management windows"

### Business Profile Integration
- **Google Business Profile**: Complete profile optimization
- **Local Extensions**: Address, phone, directions, hours
- **Reviews Management**: Solicit and respond to customer reviews
- **Photos**: Project photos, office location, installation process

## Conversion Tracking

### Primary Conversions
1. **Phone Calls**: Primary conversion action (immediate intent)
2. **Contact Form Submissions**: Lead generation for estimates
3. **Directions Requests**: Local service area interest
4. **Financing Applications**: Financing inquiry tracking

### Conversion Values (Estimated)
- Phone calls: $150 (average project value for residential)
- Form submissions: $200 (qualified estimate requests)
- Direction requests: $50 (service area interest)
- Financing inquiries: $300 (high-intent qualified leads)

### Attribution Model
- **Data-Driven Attribution**: For comprehensive user journey tracking
- **Position-Based**: Weighted attribution across touchpoints
- **Time Decay**: Recent interactions weighted higher

## Budget Allocation Strategy

### Campaign Budget Distribution
- **Hurricane Protection PMAX**: 30% (peak demand service)
- **Impact Windows Search**: 25% (primary revenue driver)
- **Impact Doors Search**: 20% (complementary service)
- **Commercial Solutions**: 15% (high-value opportunities)
- **Financing Campaigns**: 10% (conversion optimization)

### Seasonal Budget Adjustments
- **- **Pre-Season (April-May)**: Storm preparation campaigns
- **Post-Storm Response**: Emergency repair campaigns as needed

### Geographic Budget Allocation
- **West Palm Beach Area**: 40% (corporate office location)
- **Punta Gorda Area**: 30% (regional office coverage)
- **Statewide Florida**: 30% (broader market opportunity)

## Quality Score Optimization

### Ad Relevance Factors
- **Keyword Relevance**: Exact match between user intent and service offerings
- **Ad Copy Quality**: Clear hurricane protection and energy savings messaging
- **Landing Page Experience**: Fast, mobile-friendly pages with clear CTAs
- **Historical Performance**: Positive conversion history through optimization

### Landing Page Optimization
- **Page Load Speed**: <2 seconds for optimal user experience
- **Mobile Responsiveness**: 100% mobile-optimized for Florida market
- **Clear CTAs**: Prominent phone numbers, estimate forms, financing options
- **Trust Signals**: 50+ years experience, lifetime guarantee, certifications
- **Local Relevance**: Service area maps, local contact information

### Technical Performance
- **Core Web Vitals**: Optimize for Google's page experience metrics
- **SSL Certificate**: Secure website for customer trust
- **Schema Markup**: Local business and service schema implementation
- **XML Sitemap**: Comprehensive sitemap for search engine crawling

## Remarketing Strategy

### Audience Segments
1. **Website Visitors**: General retargeting for awareness
2. **Service Page Visitors**: Service-specific remarketing
3. **Estimate Form Abandons**: High-intent retargeting
4. **Phone Number Clickers**: Immediate follow-up campaigns
5. **Financing Page Visitors**: Financing-focused nurturing

### Remarketing Campaign Types
- **Display Remarketing**: Visual before/after ads, storm protection messaging
- **Search Remarketing**: Competitive protection for high-value searches
- **YouTube Remarketing**: Educational content about impact solutions
- **Dynamic Remarketing**: Product-specific retargeting

### Remarketing Creative Strategy
- **Abandoned Cart/Forms**: "Complete Your Estimate" messaging
- **Service Browsers**: Educational content about benefits
- **Recent Visitors**: Limited-time offers and urgency
- **Past Customers**: Referral and review requests

## Compliance & Regulatory

### Industry Regulations
- **Building Codes**: Florida hurricane code compliance
- **Insurance Standards**: Approved products for windstorm coverage
- **Contractor Licensing**: State-licensed installation requirements
- **Energy Efficiency**: Florida Energy Code compliance
- **Accessibility Standards**: ADA compliance for commercial installations

### Advertising Compliance
- **FTC Guidelines**: Truthful claims about protection and savings
- **Local Laws**: Florida advertising regulations
- **Testimonial Usage**: Verified customer testimonials only
- **Guarantee Claims**: Clearly defined lifetime warranty terms
- **Pricing Transparency**: Clear financing and payment terms

### Data Privacy
- **Customer Information**: Secure handling of contact information
- **Lead Tracking**: Compliant lead generation and follow-up
- **Analytics Compliance**: GDPR and privacy regulation adherence

## Performance Monitoring

### Key Performance Indicators
- **Cost per Acquisition**: Target <$100 (based on $150 average project value)
- **Conversion Rate**: Target >4% (phone calls + form submissions)
- **Phone Call Tracking**: 95%+ attribution accuracy
- **Return on Ad Spend**: Target >400% (industry standard for home improvement)
- **Customer Lifetime Value**: Track referral and repeat business value

### Reporting Cadence
- Budget pacing, impression share, and major performance alerts
- Campaign performance trends and keyword optimization opportunities
- Comprehensive performance analysis and budget reallocation
- Strategic planning, market analysis, and competitive intelligence

### Custom Reporting Dimensions
- **Geographic Performance**: Performance by city/region
- **Service Line Performance**: ROI by service type
- **Seasonal Performance**: Performance by season/hurricane preparedness
- **Device Performance**: Mobile vs desktop conversion tracking

## Risk Mitigation

### Campaign Performance Risks
- **Low Quality Score**: Comprehensive keyword research and negative keyword implementation
- **Budget Overage**: Strict daily budget caps and automated alerts
- **Low Conversion Rate**: Multi-step conversion funnel optimization
- **Competitive Pressure**: Unique value proposition and competitive differentiation

### Account Health Risks
- **Policy Violations**: Regular compliance audits and ad copy reviews
- **Limited Ad Approval**: Backup creative library and testing protocols
- **Technical Issues**: Regular account audits and performance monitoring
- **Platform Changes**: Google Ads update monitoring and adaptation

### Business Continuity Risks
- **Seasonal Demand Fluctuations**: Budget flexibility and campaign pausing capabilities
- **Economic Factors**: Financing option emphasis during economic uncertainty
- **Weather-Related Campaigns**: Emergency budget reserves for storm response
- **Supplier/Installation Capacity**: Service capacity monitoring and campaign adjustments

## Success Metrics

- Establish approved campaign structure across all service lines
- Achieve positive ROI (>300%) across primary campaigns
- Generate qualified leads through phone calls and estimate forms
- Optimize cost per acquisition below $100
- Build comprehensive remarketing audiences
- Scale successful campaigns to optimal budget levels
- Expand geographic targeting to high-opportunity areas
- Implement advanced automation and smart bidding
- Achieve industry-leading ROAS (>400%)
- Develop predictive performance modeling
- Become market leader in Florida impact window advertising
- Expand service offerings through campaign performance insights
- Implement AI-powered optimization and creative generation
- Maximize customer lifetime value through referral programs
- Establish brand authority in hurricane protection category

---

## ⚠️ CRITICAL AUTOMATION POLICY: REMOVE ALL RULES AND SCRIPTS

### Based on Comprehensive Rules & Scripts Analysis

**IMMEDIATE ACTION REQUIRED**: Remove ALL existing automation rules and scripts from the Google Ads account.

### Analysis Findings
- **Current Rules Assessment**: 18+ conflicting automation rules provide minimal to no strategic value
- **Cost-Benefit Analysis**: Manual management is simpler, cheaper, and safer for this account size
- **Technical Assessment**: Existing automation creates unnecessary complexity and risk
- **Business Logic Review**: Rules may just be time-shifting identical ads (no strategic differentiation)

### Removal Requirements
1. **Disable All Rules**: Remove all automated rules from the account
2. **Delete All Scripts**: Remove any Google Ads scripts from the account
3. **Use Native Features**: Rely on Google Ads built-in automation (Smart Bidding, Ad Scheduling)
4. **Manual Oversight**: Implement manual schedule management for business hours

### When Automation May Be Considered (Future)
- **Hurricane Emergency Response**: Simple emergency pause rules ONLY
- **Scale Justifies**: Only if account grows to 50+ active campaigns

### Implementation Notes
- **Ad Scheduling**: Use Google Ads native ad scheduling feature instead of rules
- **Business Hours**: Manual changes quarterly or as client requests
- **Emergency Protocol**: Develop simple manual emergency response procedures
- **Monitoring**: Manual performance monitoring and client communication

### Risk Mitigation
- **No Technical Debt**: Avoid script maintenance and API costs
- **Reliability**: Eliminate automation failure risks
- **Transparency**: Clear manual change history
- **Flexibility**: Easy ad-hoc adjustments without technical barriers

---

**Automation Assessment Date**: 
**Recommendation**: MANUAL MANAGEMENT ONLY for current account scope
**Review Trigger**: Re-evaluate only if account exceeds 50 active campaigns

## Competitive Intelligence

### Market Position Analysis
- **Market Leader**: Wright's established position with 50+ years experience
- **Competitive Advantages**: Lifetime guarantee, statewide coverage, financing options
- **Competitive Threats**: National chains, local competitors, online-only sellers
- **Differentiation Strategy**: Local expertise, hurricane specialization, comprehensive service

### Competitive Monitoring
- **Keyword Competition**: Monitor competitor ad positions and messaging
- **Pricing Strategy**: Competitive financing options and value positioning
- **Service Expansion**: Track competitor service offerings and market changes
- **Brand Perception**: Monitor online reviews and reputation management

This comprehensive implementation strategy positions Wright's Impact Window and Door for Google Ads success by leveraging their unique position as Florida's most experienced impact window and door specialist, with sophisticated targeting, conversion optimization, and performance monitoring to maximize return on advertising investment.