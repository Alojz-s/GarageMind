import { useEffect, useState } from "react";
import { fetchCaptchaConfig, type CaptchaConfig } from "../api/auth";

// null = not loaded yet (or request failed); the widget renders only when enabled.
export function useCaptchaConfig(): CaptchaConfig | null {
  const [config, setConfig] = useState<CaptchaConfig | null>(null);
  useEffect(() => {
    fetchCaptchaConfig()
      .then(setConfig)
      .catch(() => setConfig({ enabled: false, site_key: null }));
  }, []);
  return config;
}
