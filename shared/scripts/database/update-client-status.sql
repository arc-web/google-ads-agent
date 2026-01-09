-- Update Client Google Ads Status Based on Active Clients
-- This script updates the status_google_ads column based on currently active clients
-- Active clients are set to "Live", all others to "Not Active"

-- Step 1: Add new clients (use ON CONFLICT to handle if they already exist)
INSERT INTO clients (name, status_google_ads) 
VALUES 
  ('BrainBasedEMDR.com', 'Live'),
  ('DT Exotics Real', 'Live')
ON CONFLICT (name) DO UPDATE SET status_google_ads = 'Live';

-- Step 2: Reset all existing clients to "Not Active" (including NULL values)
UPDATE clients SET status_google_ads = 'Not Active';

-- Step 3: Set active clients to "Live" (case-insensitive matching)
UPDATE clients 
SET status_google_ads = 'Live' 
WHERE LOWER(name) IN (
  '501ppc.com',
  'advertisingreportcard.com',
  'collabmedspa.com',
  'proximahire.com',
  'fillyourtrucks.com',
  'sfbayareamoving.com',
  'likeaflashmoving.com',
  'therappc.com',
  'drivenstack.com',
  'myexpertresume.com',
  'pittsburghcit.com',
  'fulltiltautobody.com',
  'bayareatherapyforwellness.com',
  'intensivetherapyretreat.com',
  'reduxdigitalmarketing.com',
  'bluegorilladigital.com',
  'clintonautogroup.com',
  'soflocustom.com',
  'audiwpb.com',
  'douglasvolkswagen.com',
  'oceanautoclub.com',
  'oceanmazda.com',
  'oceanmazdawestkendall.com',
  'brainbasedemdr.com',
  'dt exotics real'
);

-- Step 4: Handle special case - Evolution Restoration (matches EvoRestore.com)
UPDATE clients 
SET status_google_ads = 'Live' 
WHERE name = 'Evolution Restoration & Renovation - Water Mitigation Phoenix';

-- Step 5: Ensure sVantage is Not Active (whitelabel partner, social ads only)
UPDATE clients 
SET status_google_ads = 'Not Active' 
WHERE LOWER(name) = 'svantage';

