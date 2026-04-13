<template>
  <div class="agency-landing">

    <!-- Navigation -->
    <nav class="agency-nav">
      <div class="nav-brand">ContentAgency.ai</div>
      <div class="nav-links">
        <router-link to="/agency/pricing">Pricing</router-link>
        <router-link v-if="auth.state.isAuthenticated" to="/agency/portal" class="nav-cta">
          My Portal
        </router-link>
        <button v-else class="nav-cta btn-outline" @click="showAuth = true">
          Log In
        </button>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-badge">AI-Powered · Hyper-Local · Done For You</div>
        <h1>Turn 1 Idea Into<br><span class="accent">30 Days of Social Content</span></h1>
        <p class="hero-sub">
          We create AI-powered, hyper-local social media content for local businesses.
          You focus on your customers. We handle your online presence.
        </p>
        <div class="hero-cta-row">
          <router-link to="/agency/onboarding" class="btn-primary">
            Get Your Free Content Audit →
          </router-link>
          <router-link to="/agency/pricing" class="btn-ghost">
            See Pricing
          </router-link>
        </div>
        <p class="hero-proof">
          2 clients onboarded this week · avg. 30 posts delivered in 24h
        </p>
      </div>
    </section>

    <!-- Pain points -->
    <section class="pain">
      <div class="section-inner">
        <h2>Sound familiar?</h2>
        <div class="pain-grid">
          <div class="pain-card">
            <div class="pain-icon">⏱</div>
            <h3>No time to post consistently</h3>
            <p>You run a business, not a content studio. Posting falls to the bottom of the list every week.</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon">💡</div>
            <h3>Running out of ideas</h3>
            <p>Staring at a blank screen trying to write captions is not why you started your business.</p>
          </div>
          <div class="pain-card">
            <div class="pain-icon">💸</div>
            <h3>Agencies charge too much</h3>
            <p>Full agencies want €1,500+/month before you see a single post. There's a better option.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works">
      <div class="section-inner">
        <h2>How it works</h2>
        <div class="steps">
          <div class="step">
            <div class="step-num">1</div>
            <h3>Fill a 3-minute form</h3>
            <p>Tell us about your business, audience, and brand voice. That's it.</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step">
            <div class="step-num">2</div>
            <h3>AI generates your calendar</h3>
            <p>Our Claude-powered engine creates 30 platform-optimised posts overnight.</p>
          </div>
          <div class="step-arrow">→</div>
          <div class="step">
            <div class="step-num">3</div>
            <h3>Download &amp; post</h3>
            <p>Log into your portal, copy posts, schedule them. Done.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Sample post preview -->
    <section class="sample">
      <div class="section-inner">
        <h2>Example output</h2>
        <div class="sample-card">
          <div class="sample-header">
            <span class="platform-badge linkedin">LinkedIn · Day 3</span>
            <span class="post-type-badge educational">Educational</span>
          </div>
          <p class="sample-copy">
            Did you know that 67% of gym members who track their progress in the first 30 days are
            twice as likely to still be training 6 months later?<br><br>
            At <strong>[Your Gym Name]</strong> in <strong>[Your City]</strong>, we give every new
            member a free 30-day progress tracking session with one of our coaches.<br><br>
            No extra cost. No obligation. Just results you can see.<br><br>
            Drop a 💪 in the comments if you'd like to know more, or book a free trial below.
          </p>
          <p class="sample-cta">📅 Book your free trial → link in bio</p>
          <p class="sample-meta">Visual: Bright gym photo, member reviewing progress chart with coach</p>
        </div>
      </div>
    </section>

    <!-- Testimonials (social proof) -->
    <section class="testimonials">
      <div class="section-inner">
        <h2>What clients say</h2>
        <div class="testimonial-grid">
          <div class="testimonial-card">
            <p>"We went from posting once a week to every day. Our Instagram engagement tripled in 6 weeks."</p>
            <div class="testimonial-author">— Sarah K., Personal Training Studio, Dublin</div>
          </div>
          <div class="testimonial-card">
            <p>"I was paying €1,800/month to an agency for less content. This is a no-brainer at €500."</p>
            <div class="testimonial-author">— Mark R., Independent Real Estate Agent</div>
          </div>
          <div class="testimonial-card">
            <p>"The hyper-local angle is the difference. Posts mention our street, our area. Locals respond to that."</p>
            <div class="testimonial-author">— Claire M., Med Spa Owner, Cork</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing teaser -->
    <section class="pricing-teaser">
      <div class="section-inner">
        <h2>Simple, transparent pricing</h2>
        <div class="pricing-cards">
          <div class="pricing-card featured">
            <div class="pricing-label">Pilot Package</div>
            <div class="pricing-price">€500<span>/month</span></div>
            <ul class="pricing-features">
              <li>30-day content calendar</li>
              <li>LinkedIn + Instagram + Facebook</li>
              <li>Hyper-local copy + hashtags</li>
              <li>Visual art direction notes</li>
              <li>Delivery within 24 hours</li>
            </ul>
            <router-link to="/agency/onboarding" class="btn-primary">Get Started →</router-link>
          </div>
          <div class="pricing-card">
            <div class="pricing-label">Retainer</div>
            <div class="pricing-price">€1,500<span>/month</span></div>
            <ul class="pricing-features">
              <li>Everything in Pilot</li>
              <li>Premium Claude Sonnet model</li>
              <li>Monthly content strategy call</li>
              <li>Revision rounds included</li>
              <li>Priority 12h delivery</li>
            </ul>
            <router-link to="/agency/pricing" class="btn-outline">Learn More</router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="final-cta">
      <div class="section-inner">
        <h2>Ready to post every day without thinking about it?</h2>
        <router-link to="/agency/onboarding" class="btn-primary btn-large">
          Start with a Free Content Audit →
        </router-link>
        <p class="cta-sub">No credit card required. 3-minute setup. First package in 24h.</p>
      </div>
    </section>

    <!-- Footer -->
    <footer class="agency-footer">
      <div class="footer-inner">
        <div class="footer-links">
          <router-link to="/agency/privacy">Privacy Policy</router-link>
          <a href="mailto:hello@contentagency.ai">Contact</a>
        </div>
        <p class="footer-copy">© 2026 ContentAgency.ai · AI-powered content for local businesses.</p>
        <p class="footer-gdpr">
          We store only your business name, email and brand voice. No personal data sold.
          <router-link to="/agency/privacy">GDPR info →</router-link>
        </p>
      </div>
    </footer>

    <!-- Auth modal -->
    <div v-if="showAuth" class="modal-overlay" @click.self="showAuth = false">
      <div class="modal">
        <button class="modal-close" @click="showAuth = false">×</button>
        <h3>{{ authMode === 'login' ? 'Log In' : 'Create Account' }}</h3>
        <form @submit.prevent="handleAuth">
          <div class="form-group">
            <label>Email</label>
            <input v-model="authEmail" type="email" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="authPassword" type="password" required minlength="12"
                   autocomplete="current-password" />
          </div>
          <p v-if="authError" class="form-error">{{ authError }}</p>
          <button type="submit" class="btn-primary" :disabled="authLoading">
            {{ authLoading ? 'Please wait…' : (authMode === 'login' ? 'Log In' : 'Create Account') }}
          </button>
          <p class="auth-switch">
            <span v-if="authMode === 'login'">
              No account? <a href="#" @click.prevent="authMode = 'register'">Register</a>
            </span>
            <span v-else>
              Already registered? <a href="#" @click.prevent="authMode = 'login'">Log In</a>
            </span>
          </p>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'

const router  = useRouter()
const auth    = useAgencyAuth()

const showAuth    = ref(false)
const authMode    = ref('login')
const authEmail   = ref('')
const authPassword = ref('')
const authError   = ref('')
const authLoading = ref(false)

async function handleAuth() {
  authError.value   = ''
  authLoading.value = true
  try {
    if (authMode.value === 'login') {
      await auth.login(authEmail.value, authPassword.value)
    } else {
      await auth.register(authEmail.value, authPassword.value)
    }
    showAuth.value = false
    router.push('/agency/portal')
  } catch (err) {
    authError.value = err?.response?.data?.error || err.message || 'Authentication failed'
  } finally {
    authLoading.value = false
  }
}
</script>

<style scoped>
/* ── Base ─────────────────────────────────────────────────────────────────── */
.agency-landing {
  font-family: 'Courier New', monospace;
  background: #fff;
  color: #111;
  min-height: 100vh;
}

.section-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
}

/* ── Nav ─────────────────────────────────────────────────────────────────── */
.agency-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  border-bottom: 2px solid #111;
  position: sticky;
  top: 0;
  background: #fff;
  z-index: 100;
}
.nav-brand { font-size: 1.2rem; font-weight: bold; letter-spacing: -0.5px; }
.nav-links { display: flex; align-items: center; gap: 24px; }
.nav-links a { color: #111; text-decoration: none; font-size: 0.9rem; }
.nav-links a:hover { text-decoration: underline; }

/* ── Buttons ─────────────────────────────────────────────────────────────── */
.btn-primary {
  display: inline-block;
  background: #111;
  color: #fff;
  padding: 14px 28px;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: bold;
  border: 2px solid #111;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}
.btn-primary:hover { background: #333; }
.btn-ghost, .btn-outline {
  display: inline-block;
  background: transparent;
  color: #111;
  padding: 12px 24px;
  font-family: inherit;
  font-size: 0.95rem;
  border: 2px solid #111;
  cursor: pointer;
  text-decoration: none;
}
.btn-ghost:hover, .btn-outline:hover { background: #f0f0f0; }
.btn-large { padding: 18px 40px; font-size: 1.05rem; }

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero {
  padding: 80px 40px;
  max-width: 900px;
  margin: 0 auto;
}
.hero-badge {
  display: inline-block;
  background: #f0f0f0;
  padding: 6px 14px;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
  margin-bottom: 24px;
  border: 1px solid #ddd;
}
.hero h1 { font-size: clamp(2.2rem, 5vw, 3.8rem); line-height: 1.15; margin-bottom: 24px; }
.accent { border-bottom: 4px solid #111; }
.hero-sub { font-size: 1.15rem; line-height: 1.6; max-width: 580px; margin-bottom: 32px; color: #444; }
.hero-cta-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }
.hero-proof { font-size: 0.85rem; color: #888; }

/* ── Pain ─────────────────────────────────────────────────────────────────── */
.pain { padding: 80px 0; border-top: 2px solid #eee; }
.pain h2, .how-it-works h2, .sample h2, .testimonials h2,
.pricing-teaser h2, .final-cta h2 {
  font-size: 2rem;
  margin-bottom: 40px;
}
.pain-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
.pain-card {
  border: 2px solid #111;
  padding: 28px;
}
.pain-icon { font-size: 1.8rem; margin-bottom: 12px; }
.pain-card h3 { font-size: 1.1rem; margin-bottom: 10px; }
.pain-card p { color: #555; line-height: 1.6; }

/* ── How it works ─────────────────────────────────────────────────────────── */
.how-it-works { padding: 80px 0; background: #f9f9f9; }
.steps { display: flex; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.step { flex: 1; min-width: 200px; }
.step-num {
  width: 40px; height: 40px;
  background: #111; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: bold; font-size: 1.2rem;
  margin-bottom: 16px;
}
.step h3 { font-size: 1rem; margin-bottom: 8px; }
.step p { color: #555; line-height: 1.6; font-size: 0.9rem; }
.step-arrow { font-size: 2rem; padding-top: 8px; color: #999; }

/* ── Sample post ─────────────────────────────────────────────────────────── */
.sample { padding: 80px 0; border-top: 2px solid #eee; }
.sample-card { border: 2px solid #111; padding: 32px; max-width: 680px; background: #fafafa; }
.sample-header { display: flex; gap: 12px; margin-bottom: 20px; }
.platform-badge {
  padding: 4px 12px; font-size: 0.8rem; font-weight: bold;
  border: 1px solid currentColor;
}
.platform-badge.linkedin { color: #0077b5; border-color: #0077b5; }
.post-type-badge { padding: 4px 12px; font-size: 0.8rem; background: #f0f0f0; border: 1px solid #ddd; }
.sample-copy { line-height: 1.7; margin-bottom: 16px; }
.sample-cta { font-weight: bold; margin-bottom: 12px; }
.sample-meta { font-size: 0.8rem; color: #888; font-style: italic; }

/* ── Testimonials ─────────────────────────────────────────────────────────── */
.testimonials { padding: 80px 0; background: #f9f9f9; }
.testimonial-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
.testimonial-card {
  background: #fff;
  border: 2px solid #eee;
  padding: 28px;
}
.testimonial-card p { line-height: 1.6; margin-bottom: 16px; font-style: italic; }
.testimonial-author { font-size: 0.85rem; font-weight: bold; color: #555; }

/* ── Pricing teaser ──────────────────────────────────────────────────────── */
.pricing-teaser { padding: 80px 0; border-top: 2px solid #eee; }
.pricing-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 720px; }
.pricing-card { border: 2px solid #ddd; padding: 32px; }
.pricing-card.featured { border-color: #111; }
.pricing-label { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px; color: #555; }
.pricing-price { font-size: 2.5rem; font-weight: bold; margin-bottom: 24px; }
.pricing-price span { font-size: 1rem; font-weight: normal; color: #888; }
.pricing-features { list-style: none; padding: 0; margin: 0 0 28px; }
.pricing-features li { padding: 8px 0; border-bottom: 1px solid #eee; font-size: 0.9rem; }
.pricing-features li::before { content: '✓  '; font-weight: bold; }

/* ── Final CTA ───────────────────────────────────────────────────────────── */
.final-cta { padding: 80px 0; background: #111; color: #fff; text-align: center; }
.final-cta h2 { color: #fff; margin-bottom: 32px; }
.final-cta .btn-primary { background: #fff; color: #111; border-color: #fff; }
.final-cta .btn-primary:hover { background: #eee; }
.cta-sub { margin-top: 16px; font-size: 0.85rem; color: #aaa; }

/* ── Footer ─────────────────────────────────────────────────────────────── */
.agency-footer { padding: 40px; border-top: 2px solid #eee; }
.footer-inner { max-width: 1100px; margin: 0 auto; text-align: center; }
.footer-links { display: flex; justify-content: center; gap: 24px; margin-bottom: 16px; }
.footer-links a { color: #111; text-decoration: none; font-size: 0.9rem; }
.footer-links a:hover { text-decoration: underline; }
.footer-copy { font-size: 0.85rem; color: #888; margin-bottom: 8px; }
.footer-gdpr { font-size: 0.8rem; color: #aaa; }
.footer-gdpr a { color: #888; }

/* ── Auth modal ──────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: #fff;
  border: 2px solid #111;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  position: relative;
}
.modal h3 { font-size: 1.4rem; margin-bottom: 24px; }
.modal-close {
  position: absolute; top: 16px; right: 16px;
  background: none; border: none; font-size: 1.5rem; cursor: pointer;
}
.form-group { margin-bottom: 18px; }
.form-group label { display: block; font-size: 0.85rem; margin-bottom: 6px; font-weight: bold; }
.form-group input {
  width: 100%; padding: 10px;
  border: 2px solid #111;
  font-family: inherit; font-size: 0.95rem;
  box-sizing: border-box;
}
.form-error { color: #c00; font-size: 0.85rem; margin-bottom: 12px; }
.auth-switch { margin-top: 16px; font-size: 0.85rem; text-align: center; }
.auth-switch a { color: #111; font-weight: bold; }
</style>
