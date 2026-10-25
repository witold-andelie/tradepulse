function normalizedLanguage(lang) { return String(lang || '').replaceAll('_', '-').toLowerCase(); }

export function matchingVoices(voices, locale) {
  const target = normalizedLanguage(locale);
  // A generic language may use its regional voices. Explicit regional locales are not silently swapped.
  return voices.filter((voice) => {
    const lang = normalizedLanguage(voice.lang);
    return lang === target || lang.startsWith(`${target}-`);
  });
}

export function speechAvailable(synth, Utterance) {
  return typeof Utterance === 'function' && ['speak', 'pause', 'resume', 'cancel', 'getVoices'].every((method) => typeof synth?.[method] === 'function');
}

// Browser boundary with injected dependencies for deterministic lifecycle/error tests.
export function createSpeechController(synth, Utterance, notify, timers = globalThis) {
  let current = null;
  let startTimer = null;
  let state = 'idle';
  let generation = 0;
  let started = false;
  function update(next) { state = next; notify(next); }
  function clearTimer() { if (startTimer != null) timers.clearTimeout(startTimer); startTimer = null; }
  function watchStart(token) {
    clearTimer();
    startTimer = timers.setTimeout(() => { if (token === generation) { cancel(false); update('error'); } }, 12000);
  }
  function cancel(announce = true) {
    generation += 1;
    clearTimer();
    if (current) {
      current.onstart = current.onend = current.onerror = current.onpause = current.onresume = null;
      current = null;
      try { synth.cancel(); } catch { /* Cancellation must not break navigation. */ }
    }
    if (announce) update('idle');
  }
  return {
    play(text, voice) {
      cancel(false);
      if (!speechAvailable(synth, Utterance) || !voice || !text.trim()) { update('error'); return; }
      const token = generation;
      try {
        const utterance = new Utterance(text);
        current = utterance;
        started = false;
        utterance.voice = voice;
        utterance.lang = voice.lang;
        utterance.onstart = () => { if (token === generation) { started = true; clearTimer(); if (state !== 'paused') update('speaking'); } };
        utterance.onpause = () => { if (token === generation) { clearTimer(); update('paused'); } };
        utterance.onresume = () => { if (token === generation) { if (!started) watchStart(token); update('speaking'); } };
        utterance.onend = () => { if (token === generation) { clearTimer(); current = null; update('ended'); } };
        utterance.onerror = () => { if (token === generation) { clearTimer(); current = null; update('error'); } };
        update('speaking');
        watchStart(token);
        // cancel() preserves the engine's global pause state across playback and navigation.
        if (synth.paused) synth.resume();
        synth.speak(utterance);
      } catch { cancel(false); update('error'); }
    },
    pause() { if (current && state === 'speaking') { try { clearTimer(); synth.pause(); update('paused'); } catch { cancel(false); update('error'); } } },
    resume() { if (current && state === 'paused') { try { if (!started) watchStart(generation); synth.resume(); update('speaking'); } catch { cancel(false); update('error'); } } },
    stop: () => cancel(),
    dispose: () => cancel(false),
  };
}
