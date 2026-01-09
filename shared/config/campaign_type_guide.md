# Google Ads Campaign Type Selection Guide

## 🎯 Campaign Type Overview

Choose the right campaign type based on your business goals and target audience.

## 📊 Campaign Types & Use Cases

### 🔍 **Search Campaigns**
**Best for:** High-intent users searching for your services
**Bid Strategies:** Manual CPC, Maximize conversions, Target CPA/ROAS
**Ad Formats:** Text, Responsive Search Ads
**Budget Range:** $50-200/day
**Example:** "Resume writing services" searches

### 📺 **Performance Max (PMAX)**
**Best for:** Cross-network reach with automated optimization
**Bid Strategies:** Maximize conversions (only option)
**Ad Formats:** All formats (text, image, video, discovery)
**Budget Range:** $100-500+/day
**Example:** Full-funnel optimization across all Google networks

### 🛒 **Shopping Campaigns**
**Best for:** E-commerce or service catalogs
**Bid Strategies:** Manual CPC, Maximize conversion value
**Ad Formats:** Product/Service shopping ads
**Budget Range:** $75-300/day
**Example:** Service packages with pricing

### 🎬 **Video Campaigns**
**Best for:** Brand awareness and engagement
**Bid Strategies:** CPM, CPV, Maximize conversions
**Ad Formats:** Video ads on YouTube
**Budget Range:** $75-250/day
**Example:** Professional testimonials, career advice videos

### 📱 **App Campaigns**
**Best for:** Mobile app promotion
**Bid Strategies:** App installs, In-app actions
**Ad Formats:** App store listings, mobile placements
**Budget Range:** $50-150/day
**Example:** Mobile app for resume building

### 🌐 **Display Campaigns**
**Best for:** Visual branding and retargeting
**Bid Strategies:** CPM, CPC, Maximize conversions
**Ad Formats:** Banner ads, rich media
**Budget Range:** $50-150/day
**Example:** Website retargeting, brand awareness

### 🔍 **Discovery Campaigns**
**Best for:** Native ad placements
**Bid Strategies:** Maximize conversions, CPM
**Ad Formats:** Native ads in feed
**Budget Range:** $40-120/day
**Example:** Career advice content in Google feeds

### 🏢 **Local Campaigns**
**Best for:** Local service businesses
**Bid Strategies:** Local Services Leads
**Ad Formats:** Local service ads
**Budget Range:** $75-200/day
**Example:** Local resume writing services

## 🚀 Quick Selection Guide

| Business Goal | Primary Campaign Type | Secondary Type | Budget Allocation |
|---------------|----------------------|----------------|------------------|
| **Lead Generation** | Search | Performance Max | 60% Search, 40% PMAX |
| **Brand Awareness** | Video | Display | 50% Video, 50% Display |
| **Sales Conversion** | Search | Shopping | 70% Search, 30% Shopping |
| **App Promotion** | App | Performance Max | 60% App, 40% PMAX |
| **Local Services** | Local | Search | 50% Local, 50% Search |

## ⚙️ Configuration Examples

### High-Intent Lead Generation
```python
config = loader.load_campaign_config("search", "maximize_conversions")
# Budget: $89.99/day, Target CPA: $25
```

### Brand Awareness Campaign
```python
config = loader.load_campaign_config("video", "cpm")
# Budget: $100/day, Max CPM: $8.00
```

### Full-Funnel Optimization
```python
config = loader.load_campaign_config("performance_max")
# Budget: $150/day, Automated across all networks
```

## 💡 Pro Tips

- **Start with Search campaigns** for most B2B services
- **Add PMAX** for automated cross-network reach
- **Use Video campaigns** for thought leadership content
- **Higher budgets** generally perform better with automation
- **Test different bid strategies** within the same campaign type
- **Monitor performance** for 2-4 weeks before major changes

## 📈 Scaling Strategy

1. **Start Simple:** 1-2 campaign types with proven strategies
2. **Add Automation:** Introduce PMAX for broader reach
3. **Expand Networks:** Add Display/Video for awareness
4. **Optimize Budget:** Allocate more to high-performing types
5. **Test New Types:** Experiment with Discovery/Local as needed
