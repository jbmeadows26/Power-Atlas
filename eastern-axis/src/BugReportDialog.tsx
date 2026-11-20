import { useEffect, useRef } from 'react';
import { ExternalLink, X } from 'lucide-react';
import './bugReportDialog.css';

const FORM_ID = 'LDKRaj';

/** Anonymous public reporting: a published Tally form, never GitHub Issues. */
export default function BugReportDialog({ open, onClose, section }: {
  open: boolean;
  onClose: () => void;
  section: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    return () => { if (dialog.open) dialog.close(); };
  }, [open]);
  if (!open) return null;

  // Only the application section is shared for triage. Do not transmit the
  // country selector, full URL, query string, IP, account state or user data.
  const context = new URLSearchParams({ section });
  const publicUrl = 'https://tally.so/r/' + FORM_ID + '?' + context.toString();
  const embeddedUrl = 'https://tally.so/embed/' + FORM_ID +
    '?alignLeft=1&hideTitle=0&transparentBackground=0&' + context.toString();

  return (
    <dialog ref={ref} className="ea-bug-dialog" aria-labelledby="ea-bug-heading"
      onCancel={event => { event.preventDefault(); onClose(); }}
      onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="ea-bug-panel">
        <header>
          <div>
            <h2 id="ea-bug-heading">Report a bug</h2>
            <p>No GitHub account, email address, or platform login needed.</p>
          </div>
          <button type="button" onClick={onClose} className="ea-bug-close" aria-label="Close bug report"><X size={20} /></button>
        </header>
        <iframe className="ea-bug-form" title="Anonymous Eastern Axis bug report"
          src={embeddedUrl} loading="eager" referrerPolicy="no-referrer" />
        <footer>
          <span>Reports are saved in our Tally feedback inbox. Avoid private information.</span>
          <a href={publicUrl} target="_blank" rel="noopener noreferrer">Open form separately <ExternalLink size={13}/></a>
        </footer>
      </div>
    </dialog>
  );
}
