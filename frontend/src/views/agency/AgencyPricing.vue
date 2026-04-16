<template>
  <div ref="root" class="cagency agency-pricing">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Primary">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency<span class="muted">.ai</span>
      </router-link>
      <div class="ca-nav-links">
        <router-link to="/agency">Home</router-link>
        <a href="#faq">FAQ</a>
        <router-link v-if="auth.state.isAuthenticated"
                     to="/agency/portal" class="ca-btn sm">My portal</router-link>
        <router-link v-else to="/agency/onboarding" class="ca-btn sm">Start a pilot</router-link>
      </div>
    </nav>

    <main id="main" class="wrap">

      <header class="head">
        <span class="ca-kicker reveal">Pricing</span>
        <h1 class="reveal" style="--reveal-delay:80ms">
          Two prices.<br />No contracts.<br />No surprises.
        </h1>
        <p class="lede reveal" style="--reveal-delay:160ms">
          You pay monthly. You cancel whenever. Your data is erased
          within thirty days of cancellation. That's the entire policy.
        </p>
      </header>

      <section class="plans" aria-label="Plans">
        <article class="plan featured reveal" style="--reveal-delay:80ms">
          <header>
            <span class="ca-pill on-dark">Most chosen</span>
            <h2>Pilot</h2>
            <div class="price"><span class="amount">€500</span><span class="per">/ month</span></div>
            <p>One full month of content, delivered overnight. If it's not worth the next invoice, don't pay it.</p>
          </header>
          <ul>
            <li>Thirty posts, delivered within 24 hours</li>
            <li>LinkedIn, Instagram, and Facebook</li>
            <li>Platform-native copy tuned to each feed</li>
            <li>Hyper-local references to your city or neighbourhood</li>
            <li>Twelve to fifteen hashtags per Instagram post</li>
            <li>Visual art direction with each post</li>
            <li>A clear call-to-action per post</li>
            <li>Client portal · copy, JSON download, revision requests</li>
          </ul>
          <router-link to="/agency/onboarding" class="ca-btn on-dark lg">
            Start the pilot <span class="arrow">→</span>
          </router-link>
          <p class="note">No card required to start.</p>
        </article>

        <article class="plan reveal" style="--reveal-delay:160ms">
          <header>
            <span class="ca-pill brand">Retainer</span>
            <h2>Retainer</h2>
            <div class="price"><span class="amount">€1,500</span><span class="per">/ month</span></div>
            <p>For businesses that want an always-on pipeline and a quieter inbox.</p>
          </header>
          <ul>
            <li>Everything in the pilot</li>
            <li>Claude Sonnet model — sharper drafts</li>
            <li>All four platforms, Twitter/X included</li>
            <li>Monthly thirty-minute strategy call</li>
            <li>Two revision rounds per package</li>
            <li>Priority twelve-hour delivery</li>
            <li>Monthly performance recommendations</li>
            <li>Outreach template library</li>
          </ul>
          <router-link to="/agency/onboarding" class="ca-btn secondary lg">
            Upgrade from pilot
          </router-link>
          <p class="note">Start with the pilot and upgrade anytime.</p>
        </article>

        <article class="plan plan-quiet reveal" style="--reveal-delay:240ms">
          <header>
            <span class="ca-pill">Enterprise</span>
            <h2>Enterprise</h2>
            <div class="price"><span class="amount">Custom</span></div>
            <p>Multiple locations, white-label, or API delivery? Let's talk.</p>
          </header>
          <ul>
            <li>Multiple business locations</li>
            <li>White-label delivery</li>
            <li>Custom API integration</li>
            <li>Dedicated account lead</li>
            <li>SLA with guaranteed turnaround</li>
          </ul>
          <a href="mailto:hello@contentagency.ai" class="ca-btn secondary lg">
            Write to us
          </a>
        </article>
      </section>

      <!-- Compare table (optional, read-only details) -->
      <section class="compare reveal" aria-label="Plan comparison">
        <header class="compare-head">
          <span class="ca-kicker">What differs</span>
          <h2>At a glance</h2>
        </header>
        <div class="compare-table" role="table">
          <div role="row" class="row head-row">
            <div role="columnheader">—</div>
            <div role="columnheader">Pilot</div>
            <div role="columnheader">Retainer</div>
            <div role="columnheader">Enterprise</div>
          </div>
          <div v-for="r in compareRows" :key="r.label" role="row" class="row">
            <div role="cell" class="cell-label">{{ r.label }}</div>
            <div role="cell">{{ r.pilot }}</div>
            <div role="cell">{{ r.retainer }}</div>
            <div role="cell">{{ r.enterprise }}</div>
          </div>
        </div>
      </section>

      <section id="faq" class="faq">
        <span class="ca-kicker reveal">Common questions</span>
        <h2 class="reveal" style="--reveal-delay:80ms">Answers, in order of how often they're asked.</h2>

        <div class="faq-list">
          <details v-for="(q, i) in faqs" :key="q.q" class="reveal"
                   :style="`--reveal-delay:${120 + i * 50}ms`">
            <summary>
              <span class="q-num">{{ String(i + 1).padStart(2, '0') }}</span>
              <span>{{ q.q }}</span>
              <span class="q-mark" aria-hidden="true">+</span>
            </summary>
            <div class="q-body"><p>{{ q.a }}</p></div>
          </details>
        </div>
      </section>

      <section class="close-cta reveal">
        <h2>Still deciding? Read one month, not one landing page.</h2>
        <router-link to="/agency/onboarding" class="ca-btn lg">
          Start with a free audit <span class="arrow">→</span>
        </router-link>
        <p class="note">Three-minute form · first calendar in 24h · cancel at any time.</p>
      </section>

    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import { useReveal } from '../../composables/useReveal.js'

const auth = useAgencyAuth()
const root = ref(null)
useReveal(root)

const compareRows = [
  { label: 'Posts / month',     pilot: '30',                retainer: '30',                enterprise: 'Custom' },
  { label: 'Platforms',         pilot: 'LI · IG · FB',      retainer: '+ Twitter/X',       enterprise: 'All + API' },
  { label: 'Delivery SLA',      pilot: '24 h',              retainer: '12 h priority',     enterprise: 'SLA-backed' },
  { label: 'Model tier',        pilot: 'Claude Haiku',      retainer: 'Claude Sonnet',     enterprise: 'Sonnet + custom' },
  { label: 'Revision rounds',   pilot: 'On request',        retainer: 'Two per package',   enterprise: 'Unlimited' },
  { label: 'Strategy call',     pilot: '—',                 retainer: 'Monthly · 30 min',  enterprise: 'On-demand' },
  { label: 'Locations',         pilot: '1',                 retainer: '1',                 enterprise: 'Multiple' },
]

const faqs = [
  { q: 'How fast is delivery?',
    a: 'Pilot packages arrive within 24 hours of onboarding. Retainer clients get 12-hour priority delivery.' },
  { q: 'Can I request revisions?',
    a: 'Pilot clients can flag posts via the portal and we rewrite them. Retainer clients include two full revision rounds per month.' },
  { q: 'What exactly does the AI write?',
    a: 'Platform-specific post copy, hashtag sets, a clear call-to-action, and visual art direction notes. Thirty posts cover LinkedIn, Instagram, and Facebook by default.' },
  { q: 'Is my data safe?',
    a: 'We store only your business name, contact email, and brand voice notes. No personal data is ever sold or shared. You can request full deletion at any time.' },
  { q: 'What if I want to cancel?',
    a: 'No contracts. Cancel from your portal in one click. Your data is erased within 30 days of cancellation.' },
  { q: 'Do you work outside Europe?',
    a: 'Yes — we ship content for English-speaking markets worldwide. Our local language coverage is strongest in English, Portuguese, Spanish, Italian, and French.' },
]
</script>

<style scoped>
.wrap { max-width: var(--page); margin: 0 auto; padding: 0 clamp(var(--s-5), 4vw, var(--s-7)); }

.head { padding: var(--s-10) 0 var(--s-7); max-width: var(--page); }
.head h1 {
  font-size: var(--display-1);
  margin: var(--s-4) 0 var(--s-6);
  font-weight: 500;
  letter-spacing: -0.038em;
  max-width: 14ch;
}
.lede { font-size: var(--body-lg); max-width: 58ch; color: var(--ink-mid); }

/* ── Plans ────────────────────────────────────────────────────────────── */
.plans {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--s-5);
  padding-bottom: var(--s-9);
}
@media (min-width: 760px)  { .plans { grid-template-columns: 1fr 1fr; } }
@media (min-width: 1100px) { .plans { grid-template-columns: 1.1fr 1fr 0.9fr; align-items: start; } }

.plan {
  position: relative;
  display: flex; flex-direction: column; gap: var(--s-5);
  padding: var(--s-7);
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
  transition: transform var(--dur-3) var(--ease-out),
              box-shadow var(--dur-3) var(--ease-out),
              border-color var(--dur-3) var(--ease-out);
}
.plan:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); border-color: var(--hairline-2); }

.plan.featured {
  background: var(--void);
  color: var(--moon);
  border-color: transparent;
  box-shadow: var(--shadow-lg);
}
.plan.featured p { color: color-mix(in oklab, var(--moon), transparent 25%); }
.plan.featured h2, .plan.featured .price { color: var(--moon); }
.plan.featured .note { color: var(--moon-mute); }

.plan-quiet { background: var(--surface-1); }

.plan header { display: flex; flex-direction: column; gap: var(--s-3); }
.plan h2 {
  font-size: 1.875rem;
  letter-spacing: -0.020em;
  font-weight: 500;
}
.price { display: flex; align-items: baseline; gap: 8px; }
.price .amount {
  font-family: var(--font-display);
  font-size: 3rem;
  letter-spacing: -0.030em;
  font-weight: 500;
}
.price .per {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: color-mix(in oklab, currentColor, transparent 45%);
}
.plan p { font-size: var(--small); max-width: 42ch; }

.plan ul {
  list-style: none; padding: 0; margin: 0;
  display: grid; gap: 2px;
  font-size: var(--small);
}
.plan li {
  padding: 10px 0;
  display: flex; gap: 10px;
  border-top: 1px solid color-mix(in oklab, currentColor, transparent 88%);
  color: color-mix(in oklab, currentColor, transparent 15%);
}
.plan li::before {
  content: ''; flex-shrink: 0;
  width: 16px; height: 16px; border-radius: 50%;
  margin-top: 3px;
  border: 1px solid color-mix(in oklab, currentColor, transparent 65%);
  background: radial-gradient(circle at center, currentColor 0 28%, transparent 35%);
}
.plan li:first-child { border-top: none; }

.plan .ca-btn { width: 100%; margin-top: auto; }
.plan.featured .ca-btn { background: var(--moon); color: var(--void); border-color: var(--moon); }
.plan.featured .ca-btn:hover { background: color-mix(in oklab, var(--moon), var(--paper) 18%); }
.note {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.04em;
  color: var(--ink-lo);
  text-align: center;
  margin: 0;
}

.arrow { transition: transform var(--dur-2) var(--ease-out); display: inline-block; }
.ca-btn:hover .arrow { transform: translateX(3px); }

/* ── Compare table ───────────────────────────────────────────────────── */
.compare { padding: var(--s-9) 0; border-top: 1px solid var(--hairline); }
.compare-head h2 { margin-top: var(--s-2); font-size: 2rem; max-width: 16ch; }
.compare-table {
  margin-top: var(--s-6);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  overflow: hidden;
}
.compare-table .row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  padding: 14px var(--s-5);
  font-size: var(--small);
  color: var(--ink);
  align-items: center;
}
.compare-table .row + .row { border-top: 1px solid var(--hairline); }
.compare-table .head-row {
  background: var(--surface-1);
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--ink-mid);
}
.compare-table .cell-label {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.04em;
  color: var(--ink-mid);
}
@media (max-width: 640px) {
  .compare-table .row { grid-template-columns: 1.1fr 0.9fr 0.9fr 0.9fr; padding: 12px var(--s-4); font-size: 0.8125rem; }
}

/* ── FAQ ─────────────────────────────────────────────────────────────── */
.faq { padding: var(--s-10) 0; max-width: 820px; }
.faq h2 { margin: var(--s-3) 0 var(--s-7); font-size: 2.25rem; letter-spacing: -0.025em; max-width: 22ch; }
.faq-list { display: grid; gap: 0; }
.faq-list details {
  border-top: 1px solid var(--hairline);
  padding: 0;
}
.faq-list details:last-child { border-bottom: 1px solid var(--hairline); }
.faq-list summary {
  cursor: pointer;
  list-style: none;
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  gap: var(--s-4);
  align-items: center;
  padding: var(--s-5) 0;
  font-size: 1.125rem;
  letter-spacing: -0.01em;
  color: var(--ink-hi);
  font-family: var(--font-display);
  font-weight: 500;
  transition: color var(--dur-2) var(--ease-out);
}
.faq-list summary:hover { color: var(--brand); }
.faq-list summary::-webkit-details-marker { display: none; }
.q-num {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.06em;
  color: var(--ink-lo);
}
.q-mark {
  font-size: 1.25rem;
  color: var(--ink-lo);
  transition: transform var(--dur-2) var(--ease-out);
  justify-self: end;
}
.faq-list details[open] .q-mark { transform: rotate(45deg); }
.q-body {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows var(--dur-3) var(--ease-out);
}
.faq-list details[open] .q-body { grid-template-rows: 1fr; }
.q-body > p {
  overflow: hidden;
  padding: 0 0 var(--s-6) calc(40px + var(--s-4));
  color: var(--ink-mid);
  font-size: var(--body);
  max-width: 62ch;
}

/* ── Close CTA ───────────────────────────────────────────────────────── */
.close-cta {
  text-align: center;
  padding: var(--s-10) 0;
  border-top: 1px solid var(--hairline);
  display: grid; justify-items: center; gap: var(--s-5);
}
.close-cta h2 { font-size: 2rem; max-width: 24ch; letter-spacing: -0.022em; }
</style>
