# Component Patterns Reference

## Feature Component Structure

```tsx
// components/features/DocumentCard/
// No index.tsx barrel — import directly

// DocumentCard.tsx
import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { formatDate } from '@/lib/formatters';
import type { Document } from '@/api/types';

interface DocumentCardProps {
  document: Document;
  onDelete: (id: string) => void;
}

export function DocumentCard({ document, onDelete }: DocumentCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    await onDelete(document.id);
    setIsDeleting(false);
  };

  return (
    <article className="rounded-xl border border-surface-300 bg-surface-100 p-4 shadow-card">
      <h3 className="font-semibold text-text-primary">{document.filename}</h3>
      <p className="text-sm text-text-secondary">{formatDate(document.createdAt)}</p>
      <Button variant="danger" size="sm" onClick={handleDelete} disabled={isDeleting}>
        Delete
      </Button>
    </article>
  );
}
```

## Compound Component Pattern

```tsx
// components/ui/Tabs.tsx
import { createContext, useContext, useState } from 'react';

const TabsContext = createContext<{ activeTab: string; setActiveTab: (t: string) => void } | null>(null);

export function Tabs({ children, defaultTab }: { children: React.ReactNode; defaultTab: string }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children }: { children: React.ReactNode }) {
  return <div className="flex gap-2 border-b border-surface-300">{children}</div>;
}

export function Tab({ value, children }: { value: string; children: React.ReactNode }) {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error('Tab must be inside Tabs');
  const isActive = ctx.activeTab === value;
  return (
    <button
      onClick={() => ctx.setActiveTab(value)}
      className={cn(
        'px-4 py-2 text-sm font-medium transition-colors',
        isActive ? 'border-b-2 border-brand-500 text-brand-600' : 'text-text-secondary hover:text-text-primary'
      )}
    >
      {children}
    </button>
  );
}
```

## Loading / Error / Empty States

```tsx
// Always handle all three states
function DocumentList() {
  const { data, isLoading, error } = useDocuments();

  if (isLoading) return <DocumentListSkeleton />;
  if (error) return <ErrorMessage error={error} retry={() => refetch()} />;
  if (!data?.length) return <EmptyState message="No documents yet" />;

  return (
    <ul className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {data.map((doc) => (
        <DocumentCard key={doc.id} document={doc} />
      ))}
    </ul>
  );
}
```
