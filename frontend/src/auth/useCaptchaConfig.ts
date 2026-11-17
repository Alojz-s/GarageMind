import { useEffect, useState } from 'react'
import { fetchCaptchaConfig, type CaptchaConfig } from '../api/auth'

// null = konfiguracja jeszcze się ładuje; błąd pobrania traktujemy jak wyłączoną CAPTCHA.
export function useCaptchaConfig(): CaptchaConfig | null {
  const [config, setConfig] = useState<CaptchaConfig | null>(null)
  useEffect(() => {
    fetchCaptchaConfig()
      .then(setConfig)
      .catch(() => setConfig({ enabled: false, site_key: null }))
  }, [])
  return config
}
