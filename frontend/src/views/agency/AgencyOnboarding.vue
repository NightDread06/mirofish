<template>
  <div class="agency-onboarding">
    <nav class="agency-nav">
      <router-link to="/agency" class="nav-brand">ContentAgency.ai</router-link>
      <div class="step-indicator">
        <span v-for="n in 3" :key="n"
              :class="['step-dot', { active: currentStep === n, done: currentStep > n }]">
          {{ n }}
        </span>
      </div>
    </nav>

    <!-- Completed state — show auth prompt -->
    <div v-if="submitted" class="onboarding-done">
      <div class="done-icon">✓</div>
      <h2>Your profile is ready!</h2>
      <p>Create a free account to access your client portal and trigger content generation.</p>
      <form @submit.prevent="handleAuth" class="auth-form">
        <div class="form-group">
          <label>Email address</label>
          <input v-model="authEmail" type="email" required autocomplete="email" placeholder="you@example.com" />
        </div>
        <div class="form-group">
          <label>Password <span class="hint">(12+ characters)</span></label>
          <input v-model="authPassword" type="password" required minlength="12"
                 autocomplete="new-password" placeholder="Choose a strong password" />
        </div>
        <p v-if="authError" class="form-error">{{ authError }}</p>
        <button type="submit" class="btn-primary" :disabled="authLoading">
          {{ authLoading ? 'Creating account…' : 'Create Account & Go to Portal →' }}
        </button>
        <p class="login-link">
          Already have an account?
          <a href="#" @click.prevent="showLogin = true">Log in instead</a>
        </p>
      </form>

      <!-- Login modal -->
      <div v-if="showLogin" class="modal-overlay" @click.self="showLogin = false">
        <div class="modal">
          <button class="modal-close" @click="showLogin = false">×</button>
          <h3>Log In</h3>
          <form @submit.prevent="handleLogin">
            <div class="form-group">
              <label>Email</label>
              <input v-model="loginEmail" type="email" required autocomplete="email" />
            </div>
            <div class="form-group">
              <label>Password</label>
              <input v-model="loginPassword" type="password" required autocomplete="current-password" />
            </div>
            <p v-if="loginError" class="form-error">{{ loginError }}</p>
            <button type="submit" class="btn-primary" :disabled="loginLoading">
              {{ loginLoading ? 'Logging in…' : 'Log In' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Onboarding form steps -->
    <div v-else class="onboarding-form">
      <div class="form-card">

        <!-- Step 1: Business info -->
        <div v-if="currentStep === 1">
          <h2>Tell us about your business</h2>
          <p class="step-desc">This shapes every post we create for you.</p>
          <div class="form-group">
            <label>Business name *</label>
            <input v-model="form.business_name" type="text" required maxlength="255"
                   placeholder="e.g. City Fit Gym" />
          </div>
          <div class="form-group">
            <label>Business type *</label>
            <select v-model="form.business_type" required>
              <option value="">Select type…</option>
              <option value="gym">Gym / Personal Training</option>
              <option value="salon">Hair Salon / Beauty</option>
              <option value="restaurant">Restaurant / Café</option>
              <option value="clinic">Clinic / Med Spa</option>
              <option value="real_estate">Real Estate Agent</option>
              <option value="other">Other local business</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>City *</label>
              <input v-model="form.city" type="text" required maxlength="100"
                     placeholder="e.g. Dublin" />
            </div>
            <div class="form-group">
              <label>Country</label>
              <input v-model="form.country" type="text" maxlength="2"
                     placeholder="IE" />
            </div>
          </div>
          <div class="form-group">
            <label>Contact email *</label>
            <input v-model="form.email" type="email" required placeholder="you@yourbusiness.com" />
          </div>
        </div>

        <!-- Step 2: Audience & voice -->
        <div v-if="currentStep === 2">
          <h2>Your audience &amp; brand voice</h2>
          <p class="step-desc">The more specific you are, the better the content.</p>
          <div class="form-group">
            <label>Target audience</label>
            <textarea v-model="form.target_audience" rows="3" maxlength="500"
                      placeholder="e.g. Women aged 25-45 in south Dublin interested in fitness and wellness"></textarea>
            <span class="char-count">{{ form.target_audience.length }}/500</span>
          </div>
          <div class="form-group">
            <label>Brand tone</label>
            <div class="tone-grid">
              <button v-for="tone in tones" :key="tone.value"
                      :class="['tone-btn', { selected: form.tone === tone.value }]"
                      type="button" @click="form.tone = tone.value">
                {{ tone.label }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>Brand keywords</label>
            <input v-model="form.brand_keywords" type="text" maxlength="300"
                   placeholder="e.g. results-driven, community, transformation" />
            <span class="field-hint">Comma-separated words/phrases that define your brand</span>
          </div>
          <div class="form-group">
            <label>Main competitors (optional)</label>
            <input v-model="form.competitors" type="text" maxlength="300"
                   placeholder="e.g. Anytime Fitness, PureGym" />
            <span class="field-hint">We'll differentiate your content from theirs</span>
          </div>
        </div>

        <!-- Step 3: Social handles + consent -->
        <div v-if="currentStep === 3">
          <h2>Social profiles &amp; consent</h2>
          <p class="step-desc">Optional but helps us tailor content. Never used for automated posting.</p>
          <div class="form-group">
            <label>LinkedIn URL (optional)</label>
            <input v-model="form.linkedin_url" type="url" maxlength="500"
                   placeholder="https://linkedin.com/company/yourbusiness" />
          </div>
          <div class="form-group">
            <label>Instagram handle (optional)</label>
            <input v-model="form.instagram_handle" type="text" maxlength="100"
                   placeholder="@yourbusiness" />
          </div>
          <div class="form-group">
            <label>Facebook page URL (optional)</label>
            <input v-model="form.facebook_page" type="url" maxlength="500"
                   placeholder="https://facebook.com/yourbusiness" />
          </div>

          <div class="gdpr-box">
            <label class="checkbox-label">
              <input v-model="form.gdpr_consent" type="checkbox" required />
              <span>
                I agree that ContentAgency.ai stores my business information to generate social media
                content on my behalf. I understand I can
                <router-link to="/agency/privacy">view my data or request deletion</router-link>
                at any time. *
              </span>
            </label>
          </div>
        </div>

        <!-- Errors -->
        <p v-if="formError" class="form-error">{{ formError }}</p>

        <!-- Navigation -->
        <div class="form-nav">
          <button v-if="currentStep > 1" class="btn-ghost" type="button" @click="currentStep--">
            ← Back
          </button>
          <button v-if="currentStep < 3" class="btn-primary" type="button" @click="nextStep">
            Continue →
          </button>
          <button v-if="currentStep === 3" class="btn-primary" type="button"
                  @click="submitOnboarding" :disabled="submitting">
            {{ submitting ? 'Saving…' : 'Submit & Create Account →' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAgencyAuth } from '../../store/agencyAuth.js'
import { submitOnboarding as apiSubmitOnboarding } from '../../api/agency.js'

const router = useRouter()
const auth   = useAgencyAuth()

const currentStep = ref(1)
const submitted   = ref(false)
const submitting  = ref(false)
const formError   = ref('')

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
  { value: 'friendly',     label: '😊 Friendly'      },
  { value: 'professional', label: '💼 Professional'  },
  { value: 'bold',         label: '🔥 Bold'          },
  { value: 'calm',         label: '🌿 Calm'          },
  { value: 'playful',      label: '🎉 Playful'       },
]

// Auth state for post-submit account creation
const authEmail    = ref('')
const authPassword = ref('')
const authError    = ref('')
const authLoading  = ref(false)
const showLogin    = ref(false)
const loginEmail   = ref('')
const loginPassword = ref('')
const loginError   = ref('')
const loginLoading = ref(false)

// Saved client ID from onboarding response
let savedClientId = null

function nextStep() {
  formError.value = ''
  if (currentStep.value === 1) {
    if (!form.business_name.trim()) { formError.value = 'Business name is required'; return }
    if (!form.business_type) { formError.value = 'Business type is required'; return }
    if (!form.city.trim()) { formError.value = 'City is required'; return }
    if (!form.email.trim()) { formError.value = 'Contact email is required'; return }
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

  // If user is already logged in, submit immediately
  if (auth.state.isAuthenticated) {
    try {
      const res = await apiSubmitOnboarding({ ...form })
      savedClientId = res.data?.id
      router.push('/agency/portal')
    } catch (err) {
      formError.value = err?.message || 'Submission failed. Please try again.'
    } finally {
      submitting.value = false
    }
    return
  }

  // Store form data in sessionStorage to reuse after registration
  sessionStorage.setItem('agency_pending_onboarding', JSON.stringify({ ...form }))
  submitted.value  = true
  submitting.value = false
}

async function handleAuth() {
  authError.value   = ''
  authLoading.value = true
  try {
    await auth.register(authEmail.value, authPassword.value)
    // Resubmit onboarding now that we're authenticated
    const pending = JSON.parse(sessionStorage.getItem('agency_pending_onboarding') || '{}')
    if (pending.business_name) {
      const res = await apiSubmitOnboarding(pending)
      savedClientId = res.data?.id
    }
    sessionStorage.removeItem('agency_pending_onboarding')
    router.push('/agency/portal')
  } catch (err) {
    authError.value = err?.response?.data?.error || err.message || 'Registration failed'
  } finally {
    authLoading.value = false
  }
}

async function handleLogin() {
  loginError.value  = ''
  loginLoading.value = true
  try {
    await auth.login(loginEmail.value, loginPassword.value)
    // Resubmit onboarding
    const pending = JSON.parse(sessionStorage.getItem('agency_pending_onboarding') || '{}')
    if (pending.business_name) {
      await apiSubmitOnboarding(pending)
    }
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
.agency-onboarding { font-family: 'Courier New', monospace; background: #fff; color: #111; min-height: 100vh; }
.agency-nav { display: flex; justify-content: space-between; align-items: center; padding: 20px 40px; border-bottom: 2px solid #111; }
.nav-brand { font-size: 1.2rem; font-weight: bold; text-decoration: none; color: #111; }
.step-indicator { display: flex; gap: 12px; align-items: center; }
.step-dot { width: 32px; height: 32px; border-radius: 50%; border: 2px solid #ddd; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: bold; color: #999; }
.step-dot.active { border-color: #111; color: #111; background: #111; color: #fff; }
.step-dot.done { border-color: #111; background: #f0f0f0; color: #111; }

.onboarding-form { max-width: 600px; margin: 60px auto; padding: 0 24px; }
.form-card { border: 2px solid #111; padding: 40px; }
.form-card h2 { font-size: 1.8rem; margin-bottom: 8px; }
.step-desc { color: #555; margin-bottom: 32px; }

.form-group { margin-bottom: 22px; position: relative; }
.form-group label { display: block; font-size: 0.85rem; font-weight: bold; margin-bottom: 6px; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 10px; border: 2px solid #ccc;
  font-family: inherit; font-size: 0.95rem; box-sizing: border-box;
  transition: border-color 0.15s;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #111; outline: none; }
.form-group textarea { resize: vertical; }
.char-count { position: absolute; right: 0; bottom: -18px; font-size: 0.75rem; color: #aaa; }
.field-hint { font-size: 0.78rem; color: #888; margin-top: 4px; display: block; }

.form-row { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }

.tone-grid { display: flex; flex-wrap: wrap; gap: 10px; }
.tone-btn { padding: 8px 16px; border: 2px solid #ddd; background: #fff; font-family: inherit; cursor: pointer; font-size: 0.88rem; }
.tone-btn.selected { border-color: #111; background: #111; color: #fff; }

.gdpr-box { border: 2px solid #eee; padding: 20px; background: #fafafa; margin-top: 8px; }
.checkbox-label { display: flex; gap: 12px; align-items: flex-start; cursor: pointer; font-size: 0.88rem; line-height: 1.5; }
.checkbox-label input { margin-top: 3px; flex-shrink: 0; }
.checkbox-label a { color: #111; }

.form-error { color: #c00; font-size: 0.85rem; margin-bottom: 16px; }
.form-nav { display: flex; justify-content: space-between; align-items: center; margin-top: 32px; gap: 16px; }

.btn-primary { display: inline-block; background: #111; color: #fff; padding: 14px 28px; font-family: inherit; font-size: 0.95rem; font-weight: bold; border: 2px solid #111; cursor: pointer; text-decoration: none; }
.btn-primary:hover:not(:disabled) { background: #333; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-ghost { display: inline-block; background: transparent; color: #111; padding: 12px 24px; font-family: inherit; font-size: 0.95rem; border: 2px solid #ddd; cursor: pointer; }

/* Done state */
.onboarding-done { max-width: 540px; margin: 80px auto; padding: 0 24px; text-align: center; }
.done-icon { font-size: 3rem; margin-bottom: 16px; }
.onboarding-done h2 { font-size: 2rem; margin-bottom: 12px; }
.onboarding-done > p { color: #555; margin-bottom: 32px; }
.auth-form { text-align: left; border: 2px solid #111; padding: 32px; }
.hint { font-weight: normal; color: #888; }
.login-link { margin-top: 16px; font-size: 0.85rem; text-align: center; }
.login-link a { color: #111; font-weight: bold; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: #fff; border: 2px solid #111; padding: 40px; width: 100%; max-width: 420px; position: relative; }
.modal h3 { font-size: 1.4rem; margin-bottom: 24px; }
.modal-close { position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 1.5rem; cursor: pointer; }
</style>
