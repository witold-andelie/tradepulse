import { useCallback, useEffect, useMemo, useState } from 'react';
import { createSpeechController, matchingVoices, speechAvailable } from './speech.js';

export function useReadAloud(locale, navigationKey) {
  const synth = typeof window !== 'undefined' ? window.speechSynthesis : null;
  const Utterance = typeof window !== 'undefined' ? window.SpeechSynthesisUtterance : null;
  const supported = speechAvailable(synth, Utterance);
  const [voices, setVoices] = useState([]);
  const [status, setStatus] = useState('idle');
  const [voiceId, setVoiceId] = useState('');
  const refresh = useCallback(() => {
    try { setVoices(supported ? Array.from(synth.getVoices()) : []); } catch { setVoices([]); }
  }, [synth, supported]);
  const controller = useMemo(() => createSpeechController(synth, Utterance, setStatus), [synth, Utterance]);
  useEffect(() => {
    synth?.addEventListener?.('voiceschanged', refresh);
    refresh();
    // Some engines enumerate late without an event. Retry a bounded number of times.
    const timers = supported ? [250, 1000, 3000, 10000].map((delay) => setTimeout(refresh, delay)) : [];
    return () => {
      synth?.removeEventListener?.('voiceschanged', refresh);
      timers.forEach(clearTimeout);
    };
  }, [refresh, synth]);
  useEffect(() => {
    controller.stop();
    return () => controller.dispose();
  }, [controller, locale, navigationKey]);
  const choices = matchingVoices(voices, locale);
  const voice = choices.find((item) => item.voiceURI === voiceId) || choices[0] || null;
  const chooseVoice = (value) => { controller.stop(); setVoiceId(value); };
  return { supported, choices, voice, chooseVoice, refresh, status,
    play: (text) => controller.play(text, voice), pause: controller.pause, resume: controller.resume, stop: controller.stop };
}
