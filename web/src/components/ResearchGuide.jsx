import { useLocale, Message } from "../i18n/Locale.jsx";
import { usePresentation } from '../hooks/usePresentation.jsx';

export function ViewSwitch() {
  const { t, locale } = useLocale();
  const { view, chooseView } = usePresentation();
  return <div className="view-control"><div role="group" aria-label={t("Research presentation")} className="view-switch">
    <button type="button" aria-pressed={view === 'simple'} onClick={() => chooseView('simple')}>{t("Simple View")}</button>
    <button type="button" aria-pressed={view === 'pro'} onClick={() => chooseView('pro')}>{t("Pro View")}</button>
  </div><span className="view-caption">{t("Same evidence. Your level of detail.")}</span></div>;
}
export function ResearchGuide() {
  const { t, locale } = useLocale();
  return <details className="research-guide" id="research-guide"><summary>{t("Research guide · Understand the terms")}</summary><div className="glossary-grid">
    <section><h2>{t("Stance and score")}</h2><p>{t("A research stance is a recorded relative position within an asset pool, never an instruction to place an order. A composite score combines weighted factor measurements. A higher score does not establish lower risk or a profitable future return.")}</p></section>
    <section><h2>{t("Coverage is not confidence")}</h2><p>{t("Coverage is the share of model weight with available factor data. It is not a probability that a prediction is correct. Missing values are shown as an em dash.")}</p></section>
    <section><h2>{t("Expected is not realized")}</h2><p>{t("Expected alpha and net edge are model estimates in basis points, not earned returns. One basis point is one hundredth of a percentage point. Recorded evaluation is separate from future performance.")}</p></section>
    <section><h2>{t("Evidence can fail")}</h2><p>{t("Verified and rejected are recorded verifier outcomes, not guarantees. An abstained explanation does not establish a supported explanation. No call means the run records no directional stance; the exact reason may not be supplied.")}</p></section>
    <section><h2>{t("Factors and rank IC")}</h2><p>{t("A factor measures a defined property. Rank IC is a rank correlation used to evaluate predictive information. Measure, incremental information, prediction, net cost and consistency are separate research gates.")}</p></section>
    <section><h2>{t("Data and time")}</h2><p>{t("The as-of date is the decision context, not today's date. SYNTHETIC means fictional instruments and generated numbers. REPLAY uses a sample snapshot; unavailable model recordings can produce abstentions. Check Run limitations and the original explanation. REAL identifies source-reported live data and calls.")}</p></section>
  </div></details>;
}
export function ViewIntro({ children }) {
  const { t, locale } = useLocale();
  const { isPro } = usePresentation();
  return !isPro ? <div className="simple-orientation"><span className="orientation-icon" aria-hidden="true">i</span><div>{children}<p>{t("Exact source measurements remain available below. Simple View changes presentation, not the underlying research.")}</p></div></div> : null;
}
export function StanceMeaning({ tier }) {
  const { t, locale } = useLocale();
  return <p className="stance-meaning">{tier === 'NO_CALL'
    ? t("The run records no directional research stance. Do not interpret missing evidence as a positive or negative outlook.")
    : t("This is the run’s relative research stance within its asset pool. It is not an instruction, a measure of safety or a guarantee of returns.")}</p>;
}
