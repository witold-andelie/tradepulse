const tones = {
  'strong-positive': 'bg-emerald-100 text-emerald-900 ring-emerald-300',
  positive: 'bg-green-50 text-green-900 ring-green-300',
  neutral: 'bg-slate-100 text-slate-800 ring-slate-300',
  negative: 'bg-orange-50 text-orange-900 ring-orange-300',
  'strong-negative': 'bg-red-100 text-red-900 ring-red-300',
  muted: 'bg-gray-100 text-gray-700 ring-gray-300',
  info: 'bg-blue-50 text-blue-900 ring-blue-300',
  warning: 'bg-yellow-100 text-yellow-900 ring-yellow-400',
};

export default function Badge({ tone, label }) {
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset ${tones[tone] || tones.muted}`}>
      {label}
    </span>
  );
}
