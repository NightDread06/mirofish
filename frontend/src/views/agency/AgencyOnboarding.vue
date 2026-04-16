<template>
  <div ref="root" class="cagency agency-onboarding">
    <a href="#main" class="ca-skip">Skip to content</a>

    <nav class="ca-nav" aria-label="Primary">
      <router-link to="/agency" class="ca-brand">
        <span class="dot" aria-hidden="true"></span>ContentAgency<span class="muted">.ai</span>
      </router-link>
      <div class="step-indicator" aria-label="Progress">
        <div v-for="n in 3" :key="n"
             class="step-dot"
             :class="{ active: currentStep === n, done: currentStep > n }"
             :aria-current="currentStep === n ? 'step' : null">
          <span class="step-dot-num">{{ String(n).padStart(2, '0') }}</span>
          <span class="step-dot-label">{{ stepLabels[n - 1] }}</span>
        </div>
      </div>
    </nav>

    <main id="main" class="wrap">
      <!-- Completed state — show auth prompt -->
      <section v-if="submitted" class="done reveal in">
        <span class="ca-kicker">Step 4 of 3</span>
        <h1>Your profile is ready.</h1>
        <p>Create your portal login so you can read the calendar the moment it arrives.</p>

        <form @submit.prevent="handleAuth" class="auth-form">
          <div class="ca-field">
            <label for="onb-email">Email</label>
            <input id="onb-email" v-model="authEmail" type="email" required
                   autocomplete="email" placeholder="you@yourbusiness.com" />
          </div>
          <div class="ca-field">
            <label for="onb-pass">Password</label>
            <input id="onb-pass" v-model="authPassword" type="password" required minlength="12"
                   autocomplete="new-password" placeholder="Twelve or more characters" />
            <span class="hint">Twelve characters minimum — mix letters, numbers, and punctuation.</span>
          </div>
          <p v-if="authError" class="ca-field"><span class="err">{{ authError }}</span></p>
          <button type="submit" class="ca-btn lg" :disabled="authLoading" style="width:100%">
            {{ authLoading ? 'Creating account…' : 'Create account and open portal →' }}
          </button>
          <p class="login-link">
            Already have an account?
            <a href="#" @click.prevent="showLogin = true">Sign in instead</a>
          </p>
        </form>

        <Transition name="modal">
          <div v-if="showLogin" class="ca-modal-overlay" @click.self="showLogin = false"
               role="dialog" aria-modal="true">
            <div class="ca-modal">
              <button class="ca-modal-close" @click="showLogin = false" aria-label="Close">×</button>
              <span class="ca-kicker">Welcome back</span>
              <h3>Sign in</h3>
              <form @submit.prevent="handleLogin" class="ca-modal-form">
                <div class="ca-field">
                  <label>Email</label>
                  <input v-model="loginEmail" type="email" required autocomplete="email" />
                </div>
                <div class="ca-field">
                  <label>Password</label>
                  <input v-model="loginPassword" type="password" required
                         autocomplete="current-password" />
                </div>
                <p v-if="loginError" class="ca-field"><span class="err">{{ loginError }}</span></p>
                <button type="submit" class="ca-btn lg" :disabled="loginLoading" style="width:100%">
                  {{ loginLoading ? 'Signing in…' : 'Sign in' }}
                </button>
              </form>
            </div>
          </div>
        </Transition>
      </section>

      <!-- Onboarding form steps -->
      <section v-else class="onboard">
        <header class="onboard-head">
          <span class="ca-kicker">Step {{ currentStep }} of 3</span>
          <h1>{{ stepTitles[currentStep - 1] }}</h1>
          <p>{{ stepDescs[currentStep - 1] }}</p>
        </header>

        <form class="form-card" @submit.prevent="currentStep === 3 ? submitOnboarding() : nextStep()">

          <!-- Step 1: Business info -->
          <template v-if="currentStep === 1">
            <div class="ca-field">
              <label for="f-name">Business name</label>
              <input id="f-name" v-model="form.business_name" type="text" required maxlength="255"
                     placeholder="e.g. City Fit Gym" />
            </div>
            <div class="ca-field">
              <label for="f-type">Business type</label>
              <select id="f-type" v-model="form.business_type" required>
                <option value="">Select type…</option>
                <option value="gym">Gym / personal training</option>
                <option value="salon">Hair salon / beauty</option>
                <option value="restaurant">Restaurant / café</option>
                <option value="clinic">Clinic / med spa</option>
                <option value="real_estate">Real-estate agent</option>
                <option value="other">Other local business</option>
              </select>
            </div>
            <div class="form-row">
              <div class="ca-field">
                <label for="f-city">City</label>
                <input id="f-city" v-model="form.city" type="text" required maxlength="100"
                       placeholder="e.g. Dublin" />
              </div>
              <div class="ca-field">
                <label for="f-country">Country</label>
                <input id="f-country" v-model="form.country" type="text" maxlength="2"
                       placeholder="IE" />
              </div>
            </div>
            <div class="ca-field">
              <label for="f-email">Contact email</label>
              <input id="f-email" v-model="form.email" type="email" required
                     placeholder="you@yourbusiness.com" />
            </div>
          </template>

          <!-- Step 2: Audience & voice -->
          <template v-if="currentStep === 2">
            <div class="ca-field">
              <label for="f-aud">Target audience</label>
              <textarea id="f-aud" v-model="form.target_audience" rows="3" maxlength="500"
                        placeholder="e.g. Women aged 25–45 in south Dublin interested in fitness and wellness"></textarea>
              <span class="hint">{{ form.target_audience.length }}/500</span>
            </div>

            <div class="ca-field">
              <label>Brand tone</label>
              <div class="tone-grid">
                <button v-for="tone in tones" :key="tone.value"
                        type="button"
                        class="tone-chip"
                        :class="{ selected: form.tone === tone.value }"
                        @click="form.tone = tone.value">
                  <span class="tone-label">{{ tone.label }}</span>
                  <span class="tone-hint">{{ tone.hint }}</span>
                </button>
              </div>
            </div>

            <div class="ca-field">
              <label for="f-kw">Brand keywords</label>
              <input id="f-kw" v-model="form.brand_keywords" type="text" maxlength="300"
                     placeholder="results-driven, community, transformation" />
              <span class="hint">Comma-separated words and phrases that define your brand.</span>
            </div>
            <div class="ca-field">
              <label for="f-comp">Main competitors (optional)</label>
              <input id="f-comp" v-model="form.competitors" type="text" maxlength="300"
                     placeholder="Anytime Fitness, PureGym" />
              <span class="hint">We'll differentiate your content from theirs.</span>
            </div>
          </template>

          <!-- Step 3: Social handles + consent -->
          <template v-if="currentStep === 3">
            <div class="ca-field">
              <label for="f-li">LinkedIn URL (optional)</label>
              <input id="f-li" v-model="form.linkedin_url" type="url" maxlength="500"
                     placeholder="https://linkedin.com/company/yourbusiness" />
            </div>
            <div class="ca-field">
              <label for="f-ig">Instagram handle (optional)</label>
              <input id="f-ig" v-model="form.instagram_handle" type="text" maxlength="100"
                     placeholder="@yourbusiness" />
            </div>
            <div class="ca-field">
              <label for="f-fb">Facebook page URL (optional)</label>
              <input id="f-fb" v-model="form.facebook_page" type="url" maxlength="500"
                     placeholder="https://facebook.com/yourbusiness" />
            </div>

            <label class="gdpr">
              <input v-model="form.gdpr_consent" type="checkbox" required />
              <span>
                I agree that ContentAgency.ai stores my business information to generate
                social-media content on my behalf. I understand I can
                <router-link to="/agency/privacy">view my data or request deletion</router-link>
                at any time.
              </span>
            </label>
          </template>

          <p v-if="formError" class="ca-field"><span class="err">{{ formError }}</span></p>

          <div class="form-nav">
            <button v-if="currentStep > 1" type="button" class="ca-btn ghost"
                    @click="currentStep--">← Back</button>
            <div class="form-nav-spacer"></div>
            <button v-if="currentStep < 3" type="submit" class="ca-btn">
              Continue <span class="arrow">→</span>
            </button>
            <button v-if="currentStep === 3" type="submit" class="ca-btn" :disabled="submitting">
              {{ submitting ? 'Saving…' : 'Submit and create account →' }}
            </button>
          </div>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import { submitOnboarding as apiSubmitOnboarding } from '../../api/agency.js'
import { useReveal } from '../../composables/useReveal.js'

const router = useRouter()
const auth   = useAgencyAuth()

const root = ref(null)
useReveal(root)

const currentStep = ref(1)
const submitted   = ref(false)
const submitting  = ref(false)
const formError   = ref('')

const stepTitles = [
  'Tell us about your business',
  'Your audience and brand voice',
  'Social profiles and consent',
]
const stepDescs = [
  'This shapes every post we write for you. Be specific — specific wins.',
  'The more colour you give us here, the sharper the drafts arrive.',
  'Optional handles help us tailor content. We never post automatically on your behalf.',
]
const stepLabels = ['Business', 'Voice', 'Handles']

const form = reactive({
  business_name:    '',
  business_type:    '',
  city:             '',
  country:          'IE',
  email:            '',
  tone:             'friendly',
  target_audience:  '',
  brand_keywords:   '',
  competitors:      '',
  linkedin_url:     '',
  instagram_handle: '',
  facebook_page:    '',
  gdpr_consent:     false,
})

const tones = [
  { value: 'friendly',     label: 'Friendly',     hint: 'warm, first-person'       },
  { value: 'professional', label: 'Professional', hint: 'crisp, measured'          },
  { value: 'bold',         label: 'Bold',         hint: 'punchy, opinionated'      },
  { value: 'calm',         label: 'Calm',         hint: 'quiet, deliberate'        },
  { value: 'playful',      label: 'Playful',      hint: 'light, a little cheeky'   },
]

const authEmail    = ref('')
const authPassword = ref('')
const authError    = ref('')
const authLoading  = ref(false)
const showLogin    = ref(false)
const loginEmail   = ref('')
const loginPassword = ref('')
const loginError   = ref('')
const loginLoading = ref(false)

function nextStep() {
  formError.value = ''
  if (currentStep.value === 1) {
    if (!form.business_name.trim()) { formError.value = 'Business name is required'; return }
    if (!form.business_type)        { formError.value = 'Business type is required'; return }
    if (!form.city.trim())          { formError.value = 'City is required'; return }
    if (!form.email.trim())         { formError.value = 'Contact email is required'; return }
  }
  currentStep.value++
}

async function submitOnboarding() {
  formError.value = ''
  if (!form.gdpr_consent) {
    formError.value = 'Please accept the data consent to continue'
    return
  }
  submitting.value = true

  if (auth.state.isAuthenticated) {
    try {
      await apiSubmitOnboarding({ ...form })
      router.push('/agency/portal')
    } catch (err) {
      formError.value = err?.message || 'Submission failed. Please try again.'
    } finally {
      submitting.value = false
    }
    return
  }

  sessionStorage.setItem('agency_pending_onboarding', JSON.stringify({ ...form }))
  submitted.value  = true
  submitting.value = false
}

async function handleAuth() {
  authError.value   = ''
  authLoading.value = true
  try {
    await auth.register(authEmail.value, authPassword.value)
    const pending = JSON.parse(sessionStorage.getItem('agency_pending_onboarding') || '{}')
    if (pending.business_name) await apiSubmitOnboarding(pending)
    sessionStorage.removeItem('agency_pending_onboarding')
    router.push('/agency/portal')
  } catch (err) {
    authError.value = err?.response?.data?.error || err.message || 'Registration failed'
  } finally {
    authLoading.value = false
  }
}

async function handleLogin() {
  loginError.value   = ''
  loginLoading.value = true
  try {
    await auth.login(loginEmail.value, loginPassword.value)
    const pending = JSON.parse(sessionStorage.getItem('agency_pending_onboarding') || '{}')
    if (pending.business_name) await apiSubmitOnboarding(pending)
    sessionStorage.removeItem('agency_pending_onboarding')
    showLogin.value = false
    router.push('/agency/portal')
  } catch (err) {
    loginError.value = err?.response?.data?.error || err.message || 'Login failed'
  } finally {
    loginLoading.value = false
  }
}
</script>

<style scoped>
.wrap { max-width: 820px; margin: 0 auto; padding: 0 clamp(var(--s-5), 4vw, var(--s-7)); }

/* ── Progress dots in nav ─────────────────────────────────────────────── */
.step-indicator { display: flex; gap: 2px; align-items: center; }
.step-dot {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px;
  border-radius: var(--r-full);
  border: 1px solid transparent;
  transition: background var(--dur-2) var(--ease-out),
              border-color var(--dur-2) var(--ease-out),
              color var(--dur-2) var(--ease-out);
  color: var(--ink-lo);
  font-size: var(--caption);
}
.step-dot.active {
  background: var(--ink-hi); color: var(--paper);
}
.step-dot.done {
  color: var(--brand);
}
.step-dot-num { font-family: var(--font-mono); letter-spacing: 0.06em; }
.step-dot-label { font-family: var(--font-body); letter-spacing: -0.005em; }
@media (max-width: 640px) { .step-dot-label { display: none; } }

/* ── Header ───────────────────────────────────────────────────────────── */
.onboard-head { padding: var(--s-9) 0 var(--s-7); }
.onboard-head h1 {
  font-size: clamp(2rem, 3.6vw + 1rem, 3.5rem);
  margin: var(--s-3) 0 var(--s-4);
  letter-spacing: -0.028em;
  font-weight: 500;
}
.onboard-head p { color: var(--ink-mid); font-size: var(--body-lg); max-width: 60ch; }

.form-card {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
  padding: clamp(var(--s-5), 4vw, var(--s-7));
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--s-9);
}

.form-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--s-4);
}
@media (max-width: 520px) { .form-row { grid-template-columns: 1fr; } }

/* ── Tone chips ───────────────────────────────────────────────────────── */
.tone-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--s-2);
}
.tone-chip {
  appearance: none;
  cursor: pointer;
  padding: 12px 14px;
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px;
  font-family: inherit;
  text-align: left;
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  color: var(--ink);
  transition: border-color var(--dur-2) var(--ease-out),
              background var(--dur-2) var(--ease-out),
              transform var(--dur-2) var(--ease-out);
}
.tone-chip:hover { border-color: var(--hairline-2); transform: translateY(-1px); }
.tone-chip.selected {
  background: var(--ink-hi);
  border-color: var(--ink-hi);
  color: var(--paper);
}
.tone-label { font-weight: 500; font-size: 0.95rem; }
.tone-hint {
  font-family: var(--font-mono);
  font-size: var(--mono-cap);
  letter-spacing: 0.02em;
  color: color-mix(in oklab, currentColor, transparent 40%);
}

/* ── GDPR consent ─────────────────────────────────────────────────────── */
.gdpr {
  display: grid;
  grid-template-columns: 20px 1fr;
  gap: var(--s-3);
  padding: var(--s-5);
  background: var(--surface-1);
  border: 1px solid var(--hairline);
  border-radius: var(--r-3);
  font-size: var(--small);
  line-height: 1.55;
  color: var(--ink-mid);
  cursor: pointer;
}
.gdpr input { margin-top: 3px; accent-color: var(--brand); }
.gdpr a { color: var(--ink-hi); font-weight: 500; }

/* ── Form nav ─────────────────────────────────────────────────────────── */
.form-nav {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  margin-top: var(--s-6);
  padding-top: var(--s-5);
  border-top: 1px solid var(--hairline);
}
.form-nav-spacer { flex: 1; }
.arrow { transition: transform var(--dur-2) var(--ease-out); display: inline-block; }
.ca-btn:hover .arrow { transform: translateX(3px); }

/* ── Done state ───────────────────────────────────────────────────────── */
.done { padding: var(--s-9) 0; max-width: 540px; margin: 0 auto; }
.done h1 {
  font-size: clamp(2rem, 3.6vw + 1rem, 3.5rem);
  margin: var(--s-3) 0 var(--s-4);
  letter-spacing: -0.028em;
  font-weight: 500;
}
.done > p { color: var(--ink-mid); margin-bottom: var(--s-7); }
.auth-form {
  background: var(--paper);
  border: 1px solid var(--hairline);
  border-radius: var(--r-4);
  padding: var(--s-7);
  box-shadow: var(--shadow-sm);
}
.login-link {
  margin-top: var(--s-4);
  text-align: center;
  font-size: var(--small);
  color: var(--ink-mid);
}
.login-link a { color: var(--ink-hi); font-weight: 500; }

/* ── Modal ────────────────────────────────────────────────────────────── */
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
.ca-modal h3 { font-size: 1.625rem; margin: var(--s-2) 0 var(--s-5); letter-spacing: -0.02em; }
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

.modal-enter-active, .modal-leave-active { transition: opacity var(--dur-2) var(--ease-out); }
.modal-enter-active .ca-modal, .modal-leave-active .ca-modal { transition: transform var(--dur-3) var(--ease-out); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .ca-modal, .modal-leave-to .ca-modal { transform: translateY(8px) scale(0.98); }
</style>
