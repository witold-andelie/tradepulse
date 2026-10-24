import { useState } from 'react';

// Numeric chart equivalents are rendered when opened; closed tables do not add
// hundreds of hidden rows to the reading order or the normal screening workflow.
export default function MeasurementDisclosure({ title, children }) {
  const [open, setOpen] = useState(false);
  return <details className="research-details" onToggle={(event) => setOpen(event.currentTarget.open)}><summary>{title}</summary>{open && children}</details>;
}
