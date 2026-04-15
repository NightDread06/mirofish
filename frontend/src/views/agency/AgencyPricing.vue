<template>
  <div class="agency-pricing">
    <nav class="agency-nav">
      <router-link to="/agency" class="nav-brand">ContentAgency.ai</router-link>
      <div class="nav-links">
        <router-link to="/agency">Home</router-link>
        <router-link v-if="auth.state.isAuthenticated" to="/agency/portal" class="nav-cta">Portal</router-link>
        <router-link v-else to="/agency/onboarding" class="nav-cta btn-primary">Get Started</router-link>
      </div>
    </nav>

    <div class="pricing-page">
      <h1>Simple, Transparent Pricing</h1>
      <p class="pricing-intro">No hidden fees. No long-term contracts. Pay monthly, cancel any time.</p>

      <div class="plans">
        <!-- Pilot -->
        <div class="plan-card featured">
          <div class="plan-label">Most Popular</div>
          <h2>Pilot Package</h2>
          <div class="plan-price">€500<span>/month</span></div>
          <p class="plan-desc">
            Perfect for testing the service. One month of AI-powered, hyper-local content delivered within 24 hours.
          </p>
          <ul class="plan-features">
            <li>30-day content calendar</li>
            <li>LinkedIn + Instagram + Facebook posts</li>
            <li>Platform-optimised copy for each channel</li>
            <li>Hyper-local references to your city/area</li>
            <li>Hashtag sets (10–15 per Instagram post)</li>
            <li>Visual art direction for each post</li>
            <li>Clear call-to-action per post</li>
            <li>Client portal access</li>
            <li>JSON + copy-paste download</li>
            <li>Delivery within 24 hours</li>
          </ul>
          <router-link to="/agency/onboarding" class="btn-primary">Start Your Pilot →</router-link>
          <p class="plan-note">No credit card required to start</p>
        </div>

        <!-- Retainer -->
        <div class="plan-card">
          <h2>Monthly Retainer</h2>
          <div class="plan-price">€1,500<span>/month</span></div>
          <p class="plan-desc">
            For businesses that want ongoing content, strategy, and priority support.
          </p>
          <ul class="plan-features">
            <li>Everything in Pilot</li>
            <li>Premium Claude Sonnet model (higher quality)</li>
            <li>All 4 platforms (+ Twitter/X)</li>
            <li>Monthly content strategy alignment call</li>
            <li>2 revision rounds per package</li>
            <li>Priority 12-hour delivery</li>
            <li>Monthly performance recommendations</li>
            <li>Outreach template library access</li>
          </ul>
          <router-link to="/agency/onboarding" class="btn-outline">Get Started →</router-link>
          <p class="plan-note">Pilot first, upgrade anytime</p>
        </div>

        <!-- Enterprise -->
        <div class="plan-card plan-enterprise">
          <h2>Enterprise</h2>
          <div class="plan-price">Custom</div>
          <p class="plan-desc">
            Multiple locations, white-label delivery, or custom integrations? Let's talk.
          </p>
          <ul class="plan-features">
            <li>Multiple business locations</li>
            <li>White-label content delivery</li>
            <li>Custom API integration</li>
            <li>Dedicated account manager</li>
            <li>SLA + guaranteed turnaround</li>
          </ul>
          <a href="mailto:hello@contentagency.ai" class="btn-outline">Contact Us →</a>
        </div>
      </div>

      <!-- FAQ -->
      <div class="faq">
        <h2>Common questions</h2>
        <div class="faq-list">
          <details>
            <summary>How fast is delivery?</summary>
            <p>Pilot packages are delivered within 24 hours of completing your onboarding form. Retainer clients get 12-hour delivery.</p>
          </details>
          <details>
            <summary>Can I request revisions?</summary>
            <p>Pilot clients can flag posts for revision via the portal. Retainer clients include 2 full revision rounds per month.</p>
          </details>
          <details>
            <summary>What content does the AI actually create?</summary>
            <p>Platform-specific post copy, hashtag sets, a clear call-to-action, and visual art direction notes for each post. Your 30 posts cover LinkedIn, Instagram, and Facebook by default.</p>
          </details>
          <details>
            <summary>Is my data safe?</summary>
            <p>We store only your business name, contact email, and brand voice notes. No personal data is ever sold or shared. You can request full data deletion at any time. <router-link to="/agency/privacy">Read our Privacy Policy</router-link>.</p>
          </details>
          <details>
            <summary>What if I want to cancel?</summary>
            <p>No contracts. Cancel any time from your portal. Your data is erased within 30 days of cancellation.</p>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAgencyAuth } from '../../store/agencyAuth.js'
const auth = useAgencyAuth()
</script>

<style scoped>
.agency-pricing { font-family: 'Courier New', monospace; background: #fff; color: #111; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 2px solid #111; position: sticky; top: 0; background: #fff; z-index: 100; }
.nav-brand { font-size: 1.2rem; font-weight: bold; text-decoration: none; color: #111; }
.nav-links { display: flex; align-items: center; gap: 24px; }
.nav-links a { color: #111; text-decoration: none; font-size: 0.9rem; }

.pricing-page { max-width: 1100px; margin: 0 auto; padding: 60px 24px; }
.pricing-page h1 { font-size: 2.5rem; margin-bottom: 12px; }
.pricing-intro { color: #555; margin-bottom: 48px; font-size: 1.05rem; }

.plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 80px; }
.plan-card { border: 2px solid #ddd; padding: 36px; position: relative; }
.plan-card.featured { border-color: #111; }
.plan-label { position: absolute; top: -14px; left: 24px; background: #111; color: #fff; padding: 4px 12px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em; }
.plan-card h2 { font-size: 1.5rem; margin-bottom: 16px; }
.plan-price { font-size: 2.8rem; font-weight: bold; margin-bottom: 16px; }
.plan-price span { font-size: 1rem; font-weight: normal; color: #888; }
.plan-desc { color: #555; line-height: 1.6; margin-bottom: 24px; font-size: 0.95rem; }
.plan-features { list-style: none; padding: 0; margin: 0 0 32px; }
.plan-features li { padding: 9px 0; border-bottom: 1px solid #eee; font-size: 0.9rem; }
.plan-features li::before { content: '✓  '; font-weight: bold; }
.plan-note { margin-top: 12px; font-size: 0.8rem; color: #888; text-align: center; }
.plan-enterprise { background: #fafafa; }

.btn-primary { display: inline-block; background: #111; color: #fff; padding: 14px 28px; font-family: inherit; font-size: 0.95rem; font-weight: bold; border: 2px solid #111; cursor: pointer; text-decoration: none; width: 100%; text-align: center; box-sizing: border-box; }
.btn-primary:hover { background: #333; }
.btn-outline { display: inline-block; background: transparent; color: #111; padding: 12px 24px; font-family: inherit; font-size: 0.95rem; border: 2px solid #111; cursor: pointer; text-decoration: none; width: 100%; text-align: center; box-sizing: border-box; }
.btn-outline:hover { background: #f0f0f0; }

.faq { max-width: 720px; }
.faq h2 { font-size: 1.8rem; margin-bottom: 32px; }
.faq-list details { border-bottom: 1px solid #eee; padding: 16px 0; }
.faq-list summary { cursor: pointer; font-weight: bold; font-size: 1rem; list-style: none; }
.faq-list summary::before { content: '+ '; }
.faq-list details[open] summary::before { content: '− '; }
.faq-list p { margin-top: 12px; color: #555; line-height: 1.6; font-size: 0.95rem; }
.faq-list a { color: #111; }
</style>
