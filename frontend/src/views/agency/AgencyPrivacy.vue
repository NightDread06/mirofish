<template>
  <div class="privacy-page">
    <nav class="agency-nav">
      <router-link to="/agency" class="nav-brand">ContentAgency.ai</router-link>
    </nav>
    <div class="privacy-inner">
      <h1>Privacy Policy</h1>
      <p class="last-updated">Last updated: April 2026</p>

      <section>
        <h2>1. Who we are</h2>
        <p>ContentAgency.ai is an AI-powered social media content service for local businesses. Contact: <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a></p>
      </section>

      <section>
        <h2>2. What data we collect</h2>
        <p>We collect only what is necessary to deliver the service:</p>
        <ul>
          <li>Business name and type</li>
          <li>Contact email address</li>
          <li>City and country</li>
          <li>Brand voice information (tone, audience, keywords)</li>
          <li>Optional: social media handles/URLs (for content personalisation only)</li>
          <li>Account credentials (email + hashed password — password is never stored in plain text)</li>
        </ul>
        <p><strong>We never collect:</strong> personal photos, client/patient data, payment card details, or any sensitive personal information.</p>
      </section>

      <section>
        <h2>3. How we use your data</h2>
        <ul>
          <li>To generate personalised social media content for your business</li>
          <li>To provide access to your client portal</li>
          <li>To send service-related notifications (not marketing without consent)</li>
        </ul>
        <p>Your data is processed by Claude AI (Anthropic) as a sub-processor under standard data processing agreements. No data is used to train AI models.</p>
      </section>

      <section>
        <h2>4. Legal basis (GDPR)</h2>
        <p>We process your data on the basis of:</p>
        <ul>
          <li><strong>Contract performance</strong> — to deliver the content service you purchased</li>
          <li><strong>Legitimate interest</strong> — to maintain security and prevent fraud</li>
          <li><strong>Consent</strong> — where explicitly given (e.g. marketing emails)</li>
        </ul>
      </section>

      <section>
        <h2>5. Data retention</h2>
        <p>Active client data is retained for the duration of the service relationship. Churned or inactive accounts are automatically purged after 90 days. You may request earlier deletion at any time.</p>
      </section>

      <section>
        <h2>6. Your rights</h2>
        <p>Under GDPR, you have the right to:</p>
        <ul>
          <li><strong>Access</strong> — request a copy of all data we hold about you</li>
          <li><strong>Rectification</strong> — correct inaccurate data</li>
          <li><strong>Erasure</strong> — request permanent deletion of your data ("right to be forgotten")</li>
          <li><strong>Portability</strong> — receive your data in a machine-readable format</li>
          <li><strong>Objection</strong> — object to processing based on legitimate interest</li>
        </ul>
        <p>To exercise any right: email <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a> or use the deletion option in your client portal.</p>
      </section>

      <section>
        <h2>7. Cookies</h2>
        <p>We use only essential cookies required for authentication (session/refresh token). No advertising or tracking cookies are used.</p>
      </section>

      <section>
        <h2>8. Third-party processors</h2>
        <ul>
          <li><strong>Anthropic (Claude API)</strong> — content generation (data processed under DPA)</li>
          <li><strong>Hosting provider</strong> — servers in the EU/EEA</li>
        </ul>
      </section>

      <section>
        <h2>9. Contact &amp; complaints</h2>
        <p>For privacy questions: <a href="mailto:privacy@contentagency.ai">privacy@contentagency.ai</a></p>
        <p>You have the right to lodge a complaint with your national data protection authority (e.g. DPC in Ireland).</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.privacy-page { font-family: 'Courier New', monospace; background: #fff; color: #111; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 2px solid #111; }
.nav-brand { font-size: 1.2rem; font-weight: bold; text-decoration: none; color: #111; }
.privacy-inner { max-width: 800px; margin: 0 auto; padding: 60px 24px; }
.privacy-inner h1 { font-size: 2.5rem; margin-bottom: 8px; }
.last-updated { color: #888; font-size: 0.85rem; margin-bottom: 48px; }
section { margin-bottom: 40px; }
h2 { font-size: 1.25rem; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eee; }
p { line-height: 1.7; color: #333; margin-bottom: 12px; }
ul { padding-left: 24px; }
ul li { margin-bottom: 8px; line-height: 1.6; color: #333; }
a { color: #111; }
</style>
