import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import Highlight from 'react-highlight'

export function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-pre:bg-transparent prose-code:text-[var(--foreground)]">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code(props) {
            const { className, children, ...rest } = props
            const match = /language-(\w+)/.exec(className ?? '')
            if (!match) {
              return <code className="rounded bg-[var(--accent-soft)] px-1 py-0.5" {...rest}>{children}</code>
            }
            return (
              <Highlight className={match[1]}>
                {String(children).replace(/\n$/, '')}
              </Highlight>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
