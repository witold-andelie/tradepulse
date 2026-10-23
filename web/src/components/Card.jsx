export default function Card({ title, children }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {title && <h2 className="mb-3 text-lg font-semibold text-slate-900">{title}</h2>}
      {children}
    </section>
  );
}
