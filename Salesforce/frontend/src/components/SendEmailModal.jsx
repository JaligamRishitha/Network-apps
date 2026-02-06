import { useState } from 'react';
import { XMarkIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function SendEmailModal({ isOpen, onClose, recipients = [] }) {
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!subject.trim()) {
      toast.error('Please enter a subject');
      return;
    }
    if (!body.trim()) {
      toast.error('Please enter a message');
      return;
    }

    setSending(true);
    try {
      // In a real app, this would call an email API
      // For now, we'll simulate sending
      await new Promise(resolve => setTimeout(resolve, 1000));

      toast.success(`Email sent to ${recipients.length} recipient(s)`);
      handleClose();
    } catch (error) {
      toast.error('Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    setSubject('');
    setBody('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black/50" onClick={handleClose} />

        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b bg-sf-blue-500 rounded-t-lg">
            <h2 className="text-lg font-semibold text-white">
              New Email
            </h2>
            <button type="button" onClick={handleClose} className="p-1 text-white/80 hover:text-white rounded">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-4">
            {/* Recipients */}
            <div>
              <label className="label">To</label>
              <div className="input-field bg-gray-50 min-h-[40px] flex flex-wrap gap-1 items-center">
                {recipients.length > 0 ? (
                  recipients.map((r, i) => (
                    <span key={i} className="inline-flex items-center px-2 py-1 bg-sf-blue-100 text-sf-blue-700 rounded text-sm">
                      {r.email || r.name || `Recipient ${i + 1}`}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-400 text-sm">No recipients selected</span>
                )}
              </div>
            </div>

            {/* Subject */}
            <div>
              <label className="label">Subject</label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Enter subject..."
                className="input-field"
              />
            </div>

            {/* Body */}
            <div>
              <label className="label">Message</label>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Compose your message..."
                rows={10}
                className="input-field resize-none"
              />
            </div>

            {/* Formatting toolbar */}
            <div className="flex items-center space-x-2 border-t pt-3">
              <button type="button" className="p-1.5 text-gray-500 hover:bg-gray-100 rounded" title="Bold">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z" />
                </svg>
              </button>
              <button type="button" className="p-1.5 text-gray-500 hover:bg-gray-100 rounded" title="Italic">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 4h4m-2 0v16m-4 0h8" />
                </svg>
              </button>
              <button type="button" className="p-1.5 text-gray-500 hover:bg-gray-100 rounded" title="Link">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </button>
              <div className="flex-1" />
              <button type="button" className="p-1.5 text-gray-500 hover:bg-gray-100 rounded" title="Attach file">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-4 border-t bg-gray-50 rounded-b-lg">
            <button type="button" onClick={handleClose} className="btn-outline" disabled={sending}>
              Discard
            </button>
            <button
              type="button"
              onClick={handleSend}
              className="btn-primary inline-flex items-center"
              disabled={sending || recipients.length === 0}
            >
              <PaperAirplaneIcon className="w-4 h-4 mr-1" />
              {sending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
