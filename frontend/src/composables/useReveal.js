import { onMounted, onUnmounted } from 'vue'

/**
 * Observes elements with `.reveal` inside `root` and toggles `.in` when they
 * enter the viewport. One shared IntersectionObserver per mount, cleaned up
 * on unmount. Only affects opacity + transform (see agency-tokens.css).
 *
 * @param {import('vue').Ref<HTMLElement|null>} rootRef
 * @param {object} [opts]
 * @param {string} [opts.selector='.reveal']
 * @param {string} [opts.rootMargin='0px 0px -10% 0px']
 * @param {number} [opts.threshold=0.08]
 */
export function useReveal(rootRef, opts = {}) {
  const selector   = opts.selector   ?? '.reveal'
  const rootMargin = opts.rootMargin ?? '0px 0px -10% 0px'
  const threshold  = opts.threshold  ?? 0.08

  let observer = null

  const reduceMotion =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

  onMounted(() => {
    if (!rootRef.value) return

    if (reduceMotion || typeof IntersectionObserver === 'undefined') {
      rootRef.value.querySelectorAll(selector).forEach(el => el.classList.add('in'))
      return
    }

    observer = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('in')
            observer.unobserve(entry.target)
          }
        }
      },
      { rootMargin, threshold }
    )

    rootRef.value.querySelectorAll(selector).forEach(el => observer.observe(el))
  })

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })
}

/**
 * Writes a 0→1 scroll progress value to `--scroll` on the root element,
 * so CSS can drive a progress bar. rAF-throttled, passive listener.
 *
 * @param {import('vue').Ref<HTMLElement|null>} rootRef
 */
export function useScrollProgress(rootRef) {
  let raf = 0

  function onScroll() {
    if (raf) return
    raf = requestAnimationFrame(() => {
      raf = 0
      const max = document.documentElement.scrollHeight - window.innerHeight
      const p   = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
      rootRef.value?.style.setProperty('--scroll', p.toFixed(4))
    })
  }

  onMounted(() => {
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()
  })
  onUnmounted(() => {
    window.removeEventListener('scroll', onScroll)
    if (raf) cancelAnimationFrame(raf)
  })
}
