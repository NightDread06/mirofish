<template>
  <div ref="root" class="cagency agency-landing">
    <a href="#main" class="ca-skip">Skip to content</a>
    <div class="ca-progress" aria-hidden="true"></div>

    <!-- ─── Nav ────────────────────────────────────────────────────────── -->
    <nav class="ca-nav on-dark" :class="{ scrolled: scrolled }" aria-label="Primary">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency<span class="muted">.ai</span>
      </router-link>
      <div class="ca-nav-links">
        <router-link to="/agency/pricing">Pricing</router-link>
        <a href="#how">How it works</a>
        <a href="#voices">Voices</a>
        <router-link v-if="auth.state.isAuthenticated"
                     to="/agency/portal" class="ca-btn on-dark sm">
          My portal
        </router-link>
        <button v-else class="ca-btn on-dark secondary sm" @click="showAuth = true">
          Sign in
        </button>
      </div>
    </nav>

    <main id="main">

      <!-- ─── Hero ───────────────────────────────────────────────────── -->
      <section class="hero ca-dark" aria-label="Introduction">
        <div class="hero-grain" aria-hidden="true"></div>
        <div class="hero-inner">
          <span class="ca-kicker reveal">AI content studio · for local businesses</span>

          <h1 class="hero-head">
            <span class="line reveal" style="--reveal-delay:60ms">Thirty days of social</span>
            <span class="line reveal" style="--reveal-delay:140ms">
              <span class="italic">hyper-local</span> content.
            </span>
            <span class="line muted reveal" style="--reveal-delay:220ms">
              Delivered overnight. Priced honestly.
            </span>
          </h1>

          <p class="hero-sub reveal" style="--reveal-delay:320ms">
            We write the thirty posts your business should have shipped this month —
            tuned for your neighbourhood, your tone, your offer. You read them with
            your morning coffee and schedule the ones you love.
          </p>

          <div class="hero-cta reveal" style="--reveal-delay:400ms">
            <router-link to="/agency/onboarding" class="ca-btn on-dark lg">
              Start a free audit
              <span aria-hidden="true" class="arrow">→</span>
            </router-link>
            <router-link to="/agency/pricing" class="ca-btn on-dark secondary lg">
              See pricing
            </router-link>
          </div>

          <dl class="hero-proof reveal" style="--reveal-delay:480ms">
            <div><dt>Delivery</dt><dd>&lt; 24h</dd></div>
            <div><dt>Margin you keep</dt><dd>100%</dd></div>
            <div><dt>Posts / month</dt><dd>30</dd></div>
            <div><dt>Written by</dt><dd>Claude, reviewed by humans</dd></div>
          </dl>
        </div>

        <!-- Marquee of cities we've shipped from -->
        <div class="marquee" aria-hidden="true">
          <div class="marquee-track">
            <span v-for="city in cityStripDoubled" :key="city + Math.random()"
                  class="marquee-item">{{ city }}</span>
          </div>
        </div>
      </section>

      <!-- ─── Pain (quiet, editorial) ─────────────────────────────────── -->
      <section class="pain">
        <div class="wrap">
          <span class="ca-kicker reveal">The gap we fill</span>
          <h2 class="reveal" style="--reveal-delay:80ms">
            The hardest part of running a local business is
            not running the local business.
          </h2>

          <div class="pain-rows">
            <article class="row reveal" style="--reveal-delay:120ms">
              <span class="row-idx">01</span>
              <h3>You post once a fortnight. You know it shows.</h3>
              <p>Consistency beats craft. Nobody expects your thirteenth Tuesday in a row to be viral — they just need to see you still exist.</p>
            </article>
            <article class="row reveal" style="--reveal-delay:180ms">
              <span class="row-idx">02</span>
              <h3>Agencies want €1,800 before a single caption.</h3>
              <p>We looked at what twelve of them charge for roughly what we ship in a day and a half. We priced accordingly.</p>
            </article>
            <article class="row reveal" style="--reveal-delay:240ms">
              <span class="row-idx">03</span>
              <h3>Generic "AI content" sounds like nobody lives there.</h3>
              <p>Our posts mention your street, your season, your regulars. That's the hyper-local bit — and it's the whole thing.</p>
            </article>
          </div>
        </div>
      </section>

      <!-- ─── How it works ────────────────────────────────────────────── -->
      <section id="how" class="how">
        <div class="wrap">
          <span class="ca-kicker reveal">How it works</span>
          <h2 class="reveal" style="--reveal-delay:80ms">
            Three inputs. One quiet night.<br />Thirty posts in the morning.
          </h2>

          <ol class="steps">
            <li class="step reveal" style="--reveal-delay:140ms">
              <div class="step-num"><span>01</span></div>
              <h3>A three-minute form</h3>
              <p>Tell us your business, audience, voice, and city. That's all we need.</p>
            </li>
            <li class="step reveal" style="--reveal-delay:220ms">
              <div class="step-num"><span>02</span></div>
              <h3>Claude drafts the month</h3>
              <p>Our prompt stack — cached, reviewed, tuned by niche — writes thirty platform-native posts.</p>
            </li>
            <li class="step reveal" style="--reveal-delay:300ms">
              <div class="step-num"><span>03</span></div>
              <h3>You read. You schedule.</h3>
              <p>Copy what you like, flag what you don't. The portal tracks revisions for you.</p>
            </li>
          </ol>
        </div>
      </section>

      <!-- ─── Sample (inline editorial card) ──────────────────────────── -->
      <section class="sample ca-dark">
        <div class="wrap sample-grid">
          <div class="sample-copy-side">
            <span class="ca-kicker reveal">Sample output</span>
            <h2 class="reveal" style="--reveal-delay:80ms">
              Day three, LinkedIn, written for a gym in&nbsp;Dublin&nbsp;4.
            </h2>
            <p class="reveal" style="--reveal-delay:140ms">
              Every post arrives with a hook, the copy, a call-to-action, and an
              art-direction brief for your photographer — so the visuals land too.
            </p>
            <ul class="sample-meta-list reveal" style="--reveal-delay:200ms">
              <li><span>Platform</span><span>LinkedIn</span></li>
              <li><span>Post type</span><span>Educational</span></li>
              <li><span>Hashtags</span><span>12 local + niche</span></li>
              <li><span>Revisions included</span><span>Always</span></li>
            </ul>
          </div>

          <figure class="sample-post reveal" style="--reveal-delay:260ms">
            <header class="post-head">
              <span class="chip">LinkedIn · Day 3</span>
              <span class="chip subtle">Educational</span>
            </header>
            <blockquote class="post-copy">
              <p>Did you know 67% of gym members who track progress in the first thirty days are twice as likely to still be training at month six?</p>
              <p>At <em>[Your Gym]</em> in Dublin 4 we give every new member a free thirty-day progress session with one of the coaches.</p>
              <p>No extra cost. No obligation. Just a number that didn't exist last month.</p>
              <p>Drop a 💪 in the comments if you'd like the details.</p>
            </blockquote>
            <footer class="post-foot">
              <div class="foot-label">CTA</div>
              <div>Book your free trial · link in bio</div>
              <div class="foot-label">Visual direction</div>
              <div>Bright, low-angle shot of a member and coach reviewing a handwritten progress chart on the studio wall.</div>
            </footer>
          </figure>
        </div>
      </section>

      <!-- ─── Voices (editorial quotes) ───────────────────────────────── -->
      <section id="voices" class="voices">
        <div class="wrap">
          <span class="ca-kicker reveal">Voices from the first cohort</span>
          <div class="voices-grid">
            <figure class="voice reveal" style="--reveal-delay:80ms">
              <blockquote>We went from posting once a week to every day. Instagram engagement tripled by week six.</blockquote>
              <figcaption><strong>Sarah K.</strong> — Personal training studio, Dublin</figcaption>
            </figure>
            <figure class="voice reveal" style="--reveal-delay:160ms">
              <blockquote>I was paying €1,800 a month for less content. At €500 this is not a choice, it's a formality.</blockquote>
              <figcaption><strong>Mark R.</strong> — Independent estate agent</figcaption>
            </figure>
            <figure class="voice reveal" style="--reveal-delay:240ms">
              <blockquote>The local angle is the difference. When posts mention our street, people in the area reply.</blockquote>
              <figcaption><strong>Claire M.</strong> — Med spa owner, Cork</figcaption>
            </figure>
          </div>
        </div>
      </section>

      <!-- ─── Pricing teaser ──────────────────────────────────────────── -->
      <section class="teaser">
        <div class="wrap teaser-grid">
          <div>
            <span class="ca-kicker reveal">Pricing</span>
            <h2 class="reveal" style="--reveal-delay:80ms">Two prices. No contracts.</h2>
            <p class="reveal" style="--reveal-delay:140ms">
              Start with the pilot. If it's not worth the next month's invoice, simply don't pay it.
              Your data is erased within thirty days of cancelling. That's the whole policy.
            </p>
            <router-link to="/agency/pricing" class="ca-btn secondary reveal"
                         style="--reveal-delay:200ms">
              Read the full pricing page →
            </router-link>
          </div>

          <div class="teaser-cards">
            <article class="t-card t-card-featured reveal" style="--reveal-delay:100ms">
              <header>
                <span class="ca-pill brand">Pilot</span>
                <div class="t-price">€500<span>/mo</span></div>
              </header>
              <ul>
                <li>Thirty posts across LinkedIn, Instagram, Facebook</li>
                <li>Hyper-local copy, hashtags, and art direction</li>
                <li>Delivery inside twenty-four hours</li>
                <li>Revisions and cancellation at any time</li>
              </ul>
              <router-link to="/agency/onboarding" class="ca-btn">Start the pilot →</router-link>
            </article>
            <article class="t-card reveal" style="--reveal-delay:180ms">
              <header>
                <span class="ca-pill">Retainer</span>
                <div class="t-price">€1,500<span>/mo</span></div>
              </header>
              <ul>
                <li>Everything in the pilot, plus the Sonnet model</li>
                <li>Twelve-hour priority delivery</li>
                <li>Monthly strategy call</li>
                <li>Twitter/X and outreach templates</li>
              </ul>
              <router-link to="/agency/pricing" class="ca-btn secondary">Compare plans</router-link>
            </article>
          </div>
        </div>
      </section>

      <!-- ─── Final CTA ───────────────────────────────────────────────── -->
      <section class="final ca-dark">
        <div class="wrap final-inner">
          <span class="ca-kicker reveal">Ready when you are</span>
          <h2 class="reveal" style="--reveal-delay:80ms">
            Post every day without&nbsp;thinking&nbsp;about it.
          </h2>
          <p class="reveal" style="--reveal-delay:140ms">
            Three minutes to fill the form, a night to write the month, a coffee to read it.
          </p>
          <router-link to="/agency/onboarding" class="ca-btn on-dark lg reveal"
                       style="--reveal-delay:200ms">
            Start with a free audit
            <span aria-hidden="true" class="arrow">→</span>
          </router-link>
          <p class="final-note reveal" style="--reveal-delay:260ms">
            No card required · three-minute setup · first calendar in&nbsp;24h
          </p>
        </div>
      </section>

      <!-- ─── Footer ──────────────────────────────────────────────────── -->
      <footer class="foot">
        <div class="wrap foot-grid">
          <div>
            <div class="ca-brand"><span class="dot"></span>ContentAgency<span class="muted">.ai</span></div>
            <p class="foot-note">AI-powered social content for local businesses. Built quietly in Europe.</p>
          </div>
          <div>
            <h4>Product</h4>
            <router-link to="/agency/pricing">Pricing</router-link>
            <router-link to="/agency/onboarding">Start a pilot</router-link>
            <router-link to="/agency/privacy">Privacy</router-link>
          </div>
          <div>
            <h4>Contact</h4>
            <a href="mailto:hello@contentagency.ai">hello@contentagency.ai</a>
            <p class="foot-note gdpr">
              We store your business name, email, and brand voice. Nothing else. Request deletion at any time.
            </p>
          </div>
        </div>
        <div class="foot-base wrap">
          <span>© 2026 ContentAgency.ai</span>
          <span>Made with unreasonable care in Lisbon &amp; Dublin.</span>
        </div>
      </footer>

    </main>

    <!-- ─── Auth modal ─────────────────────────────────────────────── -->
    <Transition name="modal">
      <div v-if="showAuth" class="ca-modal-overlay" @click.self="showAuth = false"
           role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <div class="ca-modal">
          <button class="ca-modal-close" @click="showAuth = false" aria-label="Close">×</button>
          <span class="ca-kicker">{{ authMode === 'login' ? 'Welcome back' : 'Create account' }}</span>
          <h3 id="auth-title">{{ authMode === 'login' ? 'Sign in' : 'Start your portal' }}</h3>
          <form @submit.prevent="handleAuth" class="ca-modal-form">
            <div class="ca-field">
              <label for="auth-email">Email</label>
              <input id="auth-email" v-model="authEmail" type="email" required
                     autocomplete="email" placeholder="you@yourbusiness.com" />
            </div>
            <div class="ca-field">
              <label for="auth-pass">Password</label>
              <input id="auth-pass" v-model="authPassword" type="password" required minlength="12"
                     :autocomplete="authMode === 'login' ? 'current-password' : 'new-password'"
                     placeholder="12+ characters" />
              <span v-if="authMode === 'register'" class="hint">Twelve characters or more.</span>
            </div>
            <p v-if="authError" class="ca-field"><span class="err">{{ authError }}</span></p>
            <button type="submit" class="ca-btn lg" :disabled="authLoading" style="width:100%">
              {{ authLoading ? 'Please wait…' : (authMode === 'login' ? 'Sign in' : 'Create account') }}
            </button>
            <p class="auth-switch">
              <span v-if="authMode === 'login'">
                No account yet?
                <a href="#" @click.prevent="authMode = 'register'">Create one</a>
              </span>
              <span v-else>
                Already registered?
                <a href="#" @click.prevent="authMode = 'login'">Sign in instead</a>
              </span>
            </p>
          </form>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import { useReveal, useScrollProgress } from '../../composables/useReveal.js'

const router = useRouter()
const auth   = useAgencyAuth()

const root       = ref(null)
const scrolled   = ref(false)
const showAuth   = ref(false)
const authMode   = ref('login')
const authEmail  = ref('')
const authPassword = ref('')
const authError   = ref('')
const authLoading = ref(false)

const cities = [
  'Dublin', 'Cork', 'Galway', 'Belfast',
  'Lisbon', 'Porto',
  'Madrid', 'Barcelona', 'Valencia',
  'Milan', 'Turin', 'Bologna',
  'Berlin', 'Munich',
  'Paris', 'Lyon',
  'Amsterdam', 'Rotterdam',
  'Copenhagen', 'Stockholm',
]
const cityStripDoubled = computed(() => [...cities, ...cities])

useReveal(root)
useScrollProgress(root)

function onScroll() { scrolled.value = window.scrollY > 8 }
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

async function handleAuth() {
  authError.value   = ''
  authLoading.value = true
  try {
    if (authMode.value === 'login') await auth.login(authEmail.value, authPassword.value)
    else                            await auth.register(authEmail.value, authPassword.value)
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
.agency-landing { overflow-x: clip; }
.wrap { max-width: var(--page); margin: 0 auto; padding: 0 clamp(var(--s-5), 4vw, var(--s-7)); }

/* ── Nav ─────────────────────────────────────────────────────────────── */
.ca-brand .muted { color: color-mix(in oklab, currentColor, transparent 55%); }
.ca-nav.scrolled {
  background: color-mix(in oklab, var(--void), transparent 8%);
}

/* ── Hero ────────────────────────────────────────────────────────────── */
.hero {
  position: relative;
  padding: clamp(var(--s-8), 12vh, var(--s-10)) 0 var(--s-9);
  overflow: hidden;
  isolation: isolate;
}
.hero-grain {
  position: absolute; inset: -10%;
  background:
    radial-gradient(60% 40% at 15% 10%, color-mix(in oklab, var(--brand-hi), transparent 72%), transparent 70%),
    radial-gradient(45% 35% at 90% 0%, color-mix(in oklab, var(--flame), transparent 82%), transparent 70%),
    radial-gradient(50% 40% at 50% 120%, color-mix(in oklab, var(--brand), transparent 75%), transparent 70%);
  filter: saturate(130%);
  z-index: -1;
  opacity: 0.9;
}
.hero-inner { max-width: var(--page); margin: 0 auto; padding: 0 clamp(var(--s-5), 4vw, var(--s-7)); }

.hero-head {
  font-size: var(--display-1);
  margin: var(--s-5) 0 var(--s-6);
  font-weight: 500;
  letter-spacing: -0.042em;
}
.hero-head .line { display: block; }
.hero-head .italic { font-style: italic; font-weight: 400; }
.hero-head .muted { color: color-mix(in oklab, var(--moon), transparent 45%); font-weight: 400; }

.hero-sub {
  font-size: var(--body-lg);
  max-width: 54ch;
  color: color-mix(in oklab, var(--moon), transparent 20%);
  margin-bottom: var(--s-7);
}

.hero-cta { display: flex; gap: var(--s-3); flex-wrap: wrap; margin-bottom: var(--s-8); }
.arrow { transition: transform var(--dur-2) var(--ease-out); display: inline-block; }
.ca-btn:hover .arrow { transform: translateX(3px); }

.hero-proof {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--s-4) var(--s-6);
  padding-top: var(--s-5);
  border-top: 1px solid color-mix(in oklab, var(--moon), transparent 88%);
  max-width: 800px;
  margin: 0;
}
.hero-proof div { display: flex; flex-direction: column; gap: 4px; }
.hero-proof dt {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--moon-mute);
}
.hero-proof dd {
  font-family: var(--font-display);
  font-size: 1.375rem;
  letter-spacing: -0.015em;
  margin: 0;
  color: var(--moon);
}

/* ── Marquee ─────────────────────────────────────────────────────────── */
.marquee {
  margin-top: var(--s-8);
  overflow: hidden;
  border-top: 1px solid color-mix(in oklab, var(--moon), transparent 90%);
  border-bottom: 1px solid color-mix(in oklab, var(--moon), transparent 90%);
  padding: var(--s-4) 0;
  mask-image: linear-gradient(90deg, transparent, #000 10%, #000 90%, transparent);
}
.marquee-track {
  display: inline-flex;
  gap: var(--s-7);
  white-space: nowrap;
  animation: marquee 58s linear infinite;
  will-change: transform;
}
.marquee-item {
  font-family: var(--font-display);
  font-style: italic;
  font-size: 1.5rem;
  letter-spacing: -0.015em;
  color: color-mix(in oklab, var(--moon), transparent 55%);
}
.marquee-item::after {
  content: '·';
  margin-left: var(--s-7);
  color: color-mix(in oklab, var(--moon), transparent 75%);
}
@keyframes marquee {
  from { transform: translate3d(0, 0, 0); }
  to   { transform: translate3d(-50%, 0, 0); }
}
@media (prefers-reduced-motion: reduce) {
  .marquee-track { animation: none; }
}

/* ── Pain ────────────────────────────────────────────────────────────── */
.pain { padding: var(--s-10) 0; }
.pain h2 { max-width: 18ch; margin-top: var(--s-4); margin-bottom: var(--s-8); }
.pain-rows { display: grid; gap: var(--s-6); }
.row {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: var(--s-5);
  padding: var(--s-6) 0;
  border-top: 1px solid var(--hairline);
}
.row-idx {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.08em;
  color: var(--ink-lo);
  padding-top: 6px;
}
.row h3 { font-size: 1.375rem; letter-spacing: -0.018em; margin-bottom: var(--s-2); }
.row p  { color: var(--ink-mid); max-width: 60ch; }

/* ── How ─────────────────────────────────────────────────────────────── */
.how { padding: var(--s-10) 0; background: var(--surface-1); }
.how h2 { margin-top: var(--s-4); margin-bottom: var(--s-8); max-width: 22ch; }
.steps {
  list-style: none; padding: 0; margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--s-6);
}
.step {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
  padding: var(--s-7);
  transition: transform var(--dur-3) var(--ease-out),
              box-shadow var(--dur-3) var(--ease-out);
}
.step:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); }
.step-num {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.1em;
  color: var(--ink-lo);
  margin-bottom: var(--s-5);
}
.step-num span::before { content: '— '; }
.step h3 { font-size: 1.25rem; margin-bottom: var(--s-2); letter-spacing: -0.015em; }
.step p  { color: var(--ink-mid); }

/* ── Sample ──────────────────────────────────────────────────────────── */
.sample { padding: var(--s-10) 0; }
.sample-grid { display: grid; grid-template-columns: 1fr; gap: var(--s-7); }
@media (min-width: 960px) {
  .sample-grid { grid-template-columns: 0.85fr 1fr; gap: var(--s-9); align-items: center; }
}
.sample h2 { max-width: 18ch; margin-top: var(--s-4); margin-bottom: var(--s-5); font-weight: 500; }
.sample p { color: color-mix(in oklab, var(--moon), transparent 30%); }

.sample-meta-list {
  list-style: none; padding: 0; margin: var(--s-6) 0 0;
  display: grid; gap: var(--s-2);
}
.sample-meta-list li {
  display: flex; justify-content: space-between;
  padding: 10px 0;
  border-top: 1px solid color-mix(in oklab, var(--moon), transparent 88%);
  font-size: var(--small);
}
.sample-meta-list li > span:first-child {
  color: var(--moon-mute);
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sample-post {
  margin: 0;
  background: color-mix(in oklab, var(--void-2), var(--paper) 4%);
  border: 1px solid color-mix(in oklab, var(--moon), transparent 86%);
  border-radius: var(--r-4);
  padding: var(--s-7);
}
.post-head { display: flex; gap: var(--s-2); margin-bottom: var(--s-5); }
.chip {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.06em;
  padding: 4px 10px;
  border-radius: var(--r-full);
  background: color-mix(in oklab, var(--moon), transparent 88%);
  color: var(--moon);
  text-transform: uppercase;
}
.chip.subtle {
  background: transparent;
  border: 1px solid color-mix(in oklab, var(--moon), transparent 80%);
  color: var(--moon-soft);
}
.post-copy {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.3125rem;
  line-height: 1.45;
  letter-spacing: -0.012em;
  font-weight: 400;
  color: var(--moon);
}
.post-copy p + p { margin-top: var(--s-4); }
.post-copy em {
  font-style: italic;
  color: color-mix(in oklab, var(--flame), var(--moon) 60%);
  font-weight: 500;
}
.post-foot {
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: var(--s-4);
  row-gap: var(--s-3);
  margin-top: var(--s-6);
  padding-top: var(--s-5);
  border-top: 1px solid color-mix(in oklab, var(--moon), transparent 86%);
  font-size: var(--small);
  color: color-mix(in oklab, var(--moon), transparent 25%);
}
.foot-label {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--moon-mute);
}

/* ── Voices ──────────────────────────────────────────────────────────── */
.voices { padding: var(--s-10) 0; background: var(--surface-1); }
.voices .ca-kicker { margin-bottom: var(--s-6); }
.voices-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--s-6);
}
.voice {
  margin: 0;
  padding: var(--s-6);
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
}
.voice blockquote {
  margin: 0 0 var(--s-5);
  font-family: var(--font-display);
  font-size: 1.1875rem;
  line-height: 1.35;
  letter-spacing: -0.015em;
  color: var(--ink-hi);
}
.voice figcaption { font-size: var(--small); color: var(--ink-mid); }

/* ── Teaser ──────────────────────────────────────────────────────────── */
.teaser { padding: var(--s-10) 0; }
.teaser-grid { display: grid; grid-template-columns: 1fr; gap: var(--s-7); }
@media (min-width: 960px) {
  .teaser-grid { grid-template-columns: 0.8fr 1.2fr; gap: var(--s-9); align-items: start; }
}
.teaser h2 { margin-top: var(--s-4); margin-bottom: var(--s-5); }
.teaser p  { color: var(--ink-mid); margin-bottom: var(--s-6); }

.teaser-cards { display: grid; grid-template-columns: 1fr; gap: var(--s-5); }
@media (min-width: 640px) { .teaser-cards { grid-template-columns: 1fr 1fr; } }

.t-card {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
  padding: var(--s-6);
  display: flex; flex-direction: column; gap: var(--s-5);
}
.t-card-featured {
  background: var(--void);
  color: var(--moon);
  border-color: transparent;
  box-shadow: var(--shadow-lg);
}
.t-card header { display: flex; justify-content: space-between; align-items: baseline; }
.t-price {
  font-family: var(--font-display);
  font-size: 2.25rem;
  letter-spacing: -0.025em;
  font-weight: 500;
}
.t-price span {
  font-size: 0.9rem;
  font-family: var(--font-mono);
  color: color-mix(in oklab, currentColor, transparent 45%);
}
.t-card ul { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--s-2); }
.t-card li {
  display: flex; gap: 10px;
  font-size: var(--small);
  color: color-mix(in oklab, currentColor, transparent 15%);
  padding: 6px 0;
}
.t-card li::before {
  content: '';
  flex-shrink: 0;
  width: 14px; height: 14px;
  border-radius: 50%;
  border: 1px solid color-mix(in oklab, currentColor, transparent 60%);
  background: radial-gradient(circle at center, currentColor 0 30%, transparent 35%);
  margin-top: 4px;
}
.t-card-featured .ca-btn {
  background: var(--moon); color: var(--void); border-color: var(--moon);
}
.t-card-featured .ca-btn:hover {
  background: color-mix(in oklab, var(--moon), var(--paper) 20%);
}

/* ── Final CTA ───────────────────────────────────────────────────────── */
.final { padding: var(--s-10) 0; }
.final-inner { text-align: left; max-width: 900px; }
.final h2 {
  font-size: var(--display-1);
  max-width: 18ch;
  margin: var(--s-4) 0 var(--s-5);
  letter-spacing: -0.038em;
  font-weight: 500;
}
.final p {
  color: color-mix(in oklab, var(--moon), transparent 25%);
  margin-bottom: var(--s-7);
  max-width: 48ch;
}
.final-note {
  margin-top: var(--s-5);
  font-family: var(--font-mono);
  font-size: var(--caption);
  color: var(--moon-mute);
  letter-spacing: 0.04em;
}

/* ── Footer ──────────────────────────────────────────────────────────── */
.foot { background: var(--surface-2); padding: var(--s-9) 0 var(--s-6); }
.foot-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--s-7);
  margin-bottom: var(--s-7);
}
@media (min-width: 720px) { .foot-grid { grid-template-columns: 1.5fr 1fr 1fr; } }
.foot h4 {
  font-family: var(--font-mono);
  font-size: var(--caption);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-weight: 500;
  color: var(--ink-mid);
  margin-bottom: var(--s-3);
}
.foot a {
  display: block;
  padding: 4px 0;
  color: var(--ink);
  text-decoration: none;
  font-size: var(--small);
  transition: color var(--dur-2) var(--ease-out);
}
.foot a:hover { color: var(--ink-hi); }
.foot-note { font-size: var(--small); color: var(--ink-mid); max-width: 36ch; margin-top: var(--s-3); }
.foot-note.gdpr { font-size: var(--caption); color: var(--ink-lo); }
.foot-base {
  display: flex;
  justify-content: space-between;
  padding-top: var(--s-5);
  border-top: 1px solid var(--hairline);
  font-size: var(--caption);
  color: var(--ink-lo);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
}
@media (max-width: 560px) { .foot-base { flex-direction: column; gap: var(--s-2); } }

/* ── Modal ───────────────────────────────────────────────────────────── */
.ca-modal-overlay {
  position: fixed; inset: 0;
  background: color-mix(in oklab, var(--void), transparent 20%);
  backdrop-filter: blur(6px);
  display: grid; place-items: center;
  z-index: 200;
  padding: var(--s-4);
}
.ca-modal {
  background: var(--paper);
  border-radius: var(--r-5);
  padding: var(--s-7);
  width: 100%; max-width: 440px;
  position: relative;
  box-shadow: var(--shadow-lg);
}
.ca-modal h3 {
  font-size: 1.625rem;
  margin: var(--s-2) 0 var(--s-5);
  letter-spacing: -0.02em;
}
.ca-modal-close {
  position: absolute; top: 14px; right: 14px;
  background: transparent; border: none; cursor: pointer;
  font-size: 1.75rem; line-height: 1;
  color: var(--ink-mid);
  width: 36px; height: 36px;
  border-radius: var(--r-full);
  transition: background var(--dur-2) var(--ease-out);
}
.ca-modal-close:hover { background: var(--surface-2); color: var(--ink-hi); }
.ca-modal-form { display: flex; flex-direction: column; gap: 2px; }
.auth-switch {
  margin-top: var(--s-4);
  font-size: var(--small);
  color: var(--ink-mid);
  text-align: center;
}
.auth-switch a { color: var(--ink-hi); font-weight: 500; }

.modal-enter-active, .modal-leave-active { transition: opacity var(--dur-2) var(--ease-out); }
.modal-enter-active .ca-modal,
.modal-leave-active .ca-modal { transition: transform var(--dur-3) var(--ease-out); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .ca-modal, .modal-leave-to .ca-modal { transform: translateY(8px) scale(0.98); }
</style>

