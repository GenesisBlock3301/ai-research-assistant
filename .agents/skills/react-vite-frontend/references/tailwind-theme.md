# Tailwind v4 Theme Reference

## index.css Setup

```css
@import "tailwindcss";

@theme {
  /* Colors */
  --color-brand-500: oklch(0.62 0.18 252);
  --color-brand-600: oklch(0.55 0.2 252);
  --color-surface-100: #ffffff;
  --color-surface-200: #f8fafc;
  --color-surface-300: #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;

  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Spacing */
  --spacing-sidebar: 16rem;

  /* Shadows */
  --shadow-card: 0 1px 3px rgb(0 0 0 / 0.1);
  --shadow-dropdown: 0 10px 15px -3px rgb(0 0 0 / 0.1);

  /* Breakpoints */
  --breakpoint-xs: 30rem;
  --breakpoint-3xl: 120rem;
}

/* Dark mode */
@layer base {
  html {
    color-scheme: light dark;
  }
  html.dark {
    color-scheme: dark;
  }
}
```

## Usage Examples

```tsx
<div className="bg-surface-100 dark:bg-surface-900 rounded-xl shadow-card p-6">
  <h2 className="font-sans text-lg font-semibold text-text-primary">
    Document Title
  </h2>
</div>
```

## Component Variants Pattern

```tsx
// components/ui/Button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const variants = {
  primary: 'bg-brand-600 text-white hover:bg-brand-500',
  secondary: 'bg-surface-200 text-text-primary hover:bg-surface-300',
  danger: 'bg-red-600 text-white hover:bg-red-500',
};

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
};

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors disabled:opacity-50',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
```
