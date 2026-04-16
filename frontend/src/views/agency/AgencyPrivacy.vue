<template>
  <div ref="root" class="cagency privacy">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Privacy">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency
      </router-link>
      <div class="ca-nav-links">
        <router-link to="/agency/pricing">Pricing</router-link>
        <router-link to="/agency/onboarding">Start</router-link>
      </div>
    </nav>

    <main id="main" class="privacy-inner">
      <header class="privacy-head reveal">
        <span class="ca-kicker">Legal</span>
        <h1>Privacy policy</h1>
        <p class="last-updated">Last updated: April 2026</p>
      </header>

      <div class="privacy-layout">
        <aside class="toc" aria-label="Sections">
          <span class="ca-kicker">Contents</span>
          <ol>
            <li v-for="s in sections" :key="s.id">
              <a :href="`#${s.id}`">{{ s.label }}</a>
            </li>
          </ol>
        </aside>

        <article class="privacy-body reveal">
          <section id="who-we-are">
            <h2>1. Who we are</h2>
            <p>
              ContentAgency.ai is an AI-powered social media content service
              for local businesses. Contact
              <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a>.
            </p>
          </section>

          <section id="what-we-collect">
            <h2>2. What data we collect</h2>
            <p>We collect only what is necessary to deliver the service.</p>
            <ul>
              <li>Business name and type</li>
              <li>Contact email address</li>
              <li>City and country</li>
              <li>Brand voice information (tone, audience, keywords)</li>
              <li>Optional: social media handles or URLs (for content personalisation only)</li>
              <li>Account credentials (email + hashed password — password is never stored in plain text)</li>
            </ul>
            <p>
              <strong>We never collect:</strong> personal photos, client or
              patient data, payment card details, or any sensitive personal
              information.
            </p>
          </section>

          <section id="how-we-use">
            <h2>3. How we use your data</h2>
            <ul>
              <li>To generate personalised social media content for your business</li>
              <li>To provide access to your client portal</li>
              <li>To send service-related notifications (not marketing without consent)</li>
            </ul>
            <p>
              Your data is processed by Claude AI (Anthropic) as a
              sub-processor under standard data processing agreements. No
              data is used to train AI models.
            </p>
          </section>

          <section id="legal-basis">
            <h2>4. Legal basis (GDPR)</h2>
            <p>We process your data on the basis of:</p>
            <ul>
              <li><strong>Contract performance</strong> — to deliver the content service you purchased</li>
              <li><strong>Legitimate interest</strong> — to maintain security and prevent fraud</li>
              <li><strong>Consent</strong> — where explicitly given (e.g. marketing emails)</li>
            </ul>
          </section>

          <section id="retention">
            <h2>5. Data retention</h2>
            <p>
              Active client data is retained for the duration of the service
              relationship. Churned or inactive accounts are automatically
              purged after 90 days. You may request earlier deletion at any
              time.
            </p>
          </section>

          <section id="your-rights">
            <h2>6. Your rights</h2>
            <p>Under GDPR, you have the right to:</p>
            <ul>
              <li><strong>Access</strong> — request a copy of all data we hold about you</li>
              <li><strong>Rectification</strong> — correct inaccurate data</li>
              <li><strong>Erasure</strong> — request permanent deletion of your data ("right to be forgotten")</li>
              <li><strong>Portability</strong> — receive your data in a machine-readable format</li>
              <li><strong>Objection</strong> — object to processing based on legitimate interest</li>
            </ul>
            <p>
              To exercise any right, email
              <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a>
              or use the deletion option in your client portal.
            </p>
          </section>

          <section id="cookies">
            <h2>7. Cookies</h2>
            <p>
              We use only essential cookies required for authentication
              (session or refresh token). No advertising or tracking cookies
              are used.
            </p>
          </section>

          <section id="processors">
            <h2>8. Third-party processors</h2>
            <ul>
              <li><strong>Anthropic (Claude API)</strong> — content generation (data processed under DPA)</li>
              <li><strong>Hosting provider</strong> — servers in the EU/EEA</li>
            </ul>
          </section>

          <section id="contact">
            <h2>9. Contact &amp; complaints</h2>
            <p>
              For privacy questions:
              <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a>.
            </p>
            <p>
              You have the right to lodge a complaint with your national data
              protection authority (e.g. DPC in Ireland).
            </p>
          </section>
        </article>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useReveal } from '../../composables/useReveal.js'

const root = ref(null)
useReveal(root)

const sections = [
  { id: 'who-we-are',     label: 'Who we are' },
  { id: 'what-we-collect', label: 'What we collect' },
  { id: 'how-we-use',     label: 'How we use it' },
  { id: 'legal-basis',    label: 'Legal basis' },
  { id: 'retention',      label: 'Data retention' },
  { id: 'your-rights',    label: 'Your rights' },
  { id: 'cookies',        label: 'Cookies' },
  { id: 'processors',     label: 'Third-party processors' },
  { id: 'contact',        label: 'Contact & complaints' },
]
</script>

<style scoped>
.privacy-inner {
  max-width: var(--page);
  margin: 0 auto;
  padding: var(--s-8) var(--s-5) var(--s-10);
}

.privacy-head {
  border-bottom: 1px solid var(--hairline);
  padding-bottom: var(--s-6);
  margin-bottom: var(--s-8);
}
.privacy-head h1 {
  font-size: var(--display-2);
  margin: var(--s-2) 0;
}
.last-updated {
  font-family: var(--font-mono);
  font-size: var(--caption);
  color: var(--ink-lo);
  letter-spacing: 0.04em;
}

.privacy-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--s-7);
}
@media (min-width: 900px) {
  .privacy-layout { grid-template-columns: 220px 1fr; gap: var(--s-8); }
  .toc {
    position: sticky;
    top: calc(var(--s-8));
    align-self: start;
  }
}

.toc ol {
  list-style: none;
  margin: var(--s-3) 0 0;
  padding: 0;
  display: flex; flex-direction: column;
  gap: var(--s-2);
  counter-reset: toc;
}
.toc li { counter-increment: toc; font-size: var(--small); }
.toc li::before {
  content: counter(toc, decimal-leading-zero);
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.04em;
  color: var(--ink-lo);
  margin-right: 8px;
}
.toc a {
  color: var(--ink-mid);
  text-decoration: none;
  transition: color var(--dur-2) var(--ease-out);
}
.toc a:hover { color: var(--ink-hi); }

.privacy-body {
  max-width: var(--measure);
}
.privacy-body section { margin-bottom: var(--s-8); scroll-margin-top: var(--s-8); }
.privacy-body section:last-child { margin-bottom: 0; }

.privacy-body h2 {
  font-size: 1.375rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  margin: 0 0 var(--s-3);
  padding-bottom: var(--s-2);
  border-bottom: 1px solid var(--hairline);
  color: var(--ink-hi);
}
.privacy-body p {
  line-height: 1.7;
  color: var(--ink);
  margin: 0 0 var(--s-3);
}
.privacy-body ul {
  padding-left: var(--s-5);
  margin: 0 0 var(--s-4);
}
.privacy-body li {
  margin-bottom: var(--s-2);
  line-height: 1.65;
  color: var(--ink);
}
.privacy-body a {
  color: var(--brand);
  text-decoration-color: color-mix(in oklab, var(--brand), transparent 60%);
}
.privacy-body strong { color: var(--ink-hi); font-weight: 600; }
</style>
