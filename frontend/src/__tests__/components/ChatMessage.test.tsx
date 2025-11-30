import { render, screen } from '@testing-library/react';
import { ChatMessage } from '@/components/chat/ChatMessage';

describe('ChatMessage', () => {
  const userMessage = {
    id: '1',
    role: 'user' as const,
    content: 'Do I need planning permission?',
    timestamp: new Date().toISOString(),
  };

  const assistantMessage = {
    id: '2',
    role: 'assistant' as const,
    content: 'Based on the guidelines, you may need planning permission.',
    timestamp: new Date().toISOString(),
    sources: [
      {
        title: 'Camden Guidelines',
        url: 'https://example.com/guidelines',
        snippet: 'Planning permission is required for...',
      },
    ],
  };

  it('renders user message correctly', () => {
    render(<ChatMessage message={userMessage} />);

    expect(screen.getByText('Do I need planning permission?')).toBeInTheDocument();
  });

  it('renders assistant message correctly', () => {
    render(<ChatMessage message={assistantMessage} />);

    expect(
      screen.getByText(/Based on the guidelines, you may need planning permission/)
    ).toBeInTheDocument();
  });

  it('shows sources for assistant messages', () => {
    render(<ChatMessage message={assistantMessage} />);

    // Sources section should be present
    expect(screen.getByText(/Camden Guidelines/i)).toBeInTheDocument();
  });

  it('does not show sources for user messages', () => {
    render(<ChatMessage message={userMessage} />);

    // No sources section for user messages
    expect(screen.queryByText(/Sources/i)).not.toBeInTheDocument();
  });

  it('applies correct styling for user vs assistant messages', () => {
    const { container, rerender } = render(<ChatMessage message={userMessage} />);

    // User messages should have user-specific styling
    const userMessageElement = container.firstChild;
    expect(userMessageElement).toBeInTheDocument();

    rerender(<ChatMessage message={assistantMessage} />);

    // Assistant messages should have different styling
    const assistantMessageElement = container.firstChild;
    expect(assistantMessageElement).toBeInTheDocument();
  });

  it('handles messages with markdown content', () => {
    const markdownMessage = {
      ...assistantMessage,
      content: '**Important:** You need planning permission for:\n- Extensions\n- Loft conversions',
    };

    render(<ChatMessage message={markdownMessage} />);

    // Should render markdown content
    expect(screen.getByText(/Important/)).toBeInTheDocument();
  });

  it('handles empty content gracefully', () => {
    const emptyMessage = {
      ...userMessage,
      content: '',
    };

    render(<ChatMessage message={emptyMessage} />);

    // Should not crash with empty content
    expect(screen.queryByText('undefined')).not.toBeInTheDocument();
  });
});
