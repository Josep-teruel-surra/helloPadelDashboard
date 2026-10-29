import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/cn";

/** Renderiza markdown (con tablas y listas de tareas). El HTML crudo no se interpreta: sin XSS. */
export function Markdown({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn("prose prose-stone max-w-none prose-a:text-amber-700", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
